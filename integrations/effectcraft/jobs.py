"""Serial GPU queue with recoverable results and cooperative cancellation."""
import json
from pathlib import Path
import re
import shutil
import sys
import threading
import time
import uuid

from options import validate
from resident import Worker

TERMINAL = {'completed', 'failed', 'cancelled'}


class Jobs:
    def __init__(self, root, output_root, python=sys.executable, worker=None):
        self.root, self.output_root = Path(root).resolve(), Path(output_root).resolve()
        self.worker = worker or Worker(self.root, python)
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.jobs = {}
        self.active = None
        self.closed = False
        self.output_root.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.output_root.glob('*/job.json'), key=lambda p: p.stat().st_mtime)[-100:]:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if not re.fullmatch('[0-9a-f]{32}', data['id']) or path.parent.name != data['id']: continue
                if data['state'] not in TERMINAL:
                    data.update(state='failed', error='Dienst während der Verarbeitung beendet. Auftrag bitte erneut starten.', finished=time.time())
                data['cancel'] = threading.Event()
                data['folder'] = str(path.parent)
                self.jobs[data['id']] = data
            except (OSError, ValueError, KeyError, TypeError): pass
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _persist(self, job, strict=False):
        path = Path(job['folder'], 'job.json')
        temp = path.with_suffix('.tmp')
        try:
            temp.write_text(json.dumps({k: v for k, v in job.items() if k != 'cancel'}, ensure_ascii=False), encoding='utf-8')
            temp.replace(path)
        except OSError as error:
            job['storage_error'] = 'Auftragsstatus konnte nicht gespeichert werden: ' + str(error)
            if strict: raise

    def submit(self, params):
        return self.submit_batch([params])[0]

    def submit_batch(self, items):
        if not isinstance(items, list) or not 1 <= len(items) <= 32: raise ValueError('1 bis 32 Clips pro Stapel auswählen')
        options = [validate(item) for item in items]
        with self.condition:
            if self.closed: raise ValueError('Dienst wird beendet')
            if sum(j['state'] not in TERMINAL for j in self.jobs.values()) + len(items) > 32:
                raise ValueError('Warteschlange voll. Höchstens 32 offene Aufträge.')
            added, folders = [], []
            try:
                for option in options:
                    identity = uuid.uuid4().hex
                    folder = self.output_root / identity
                    folder.mkdir()
                    folders.append(folder)
                    job = dict(id=identity, state='queued', input=option['input'], options=option,
                        context=option['context'], preview=option['preview'], output=None, error=None,
                        log=str(folder / 'inference.log'), folder=str(folder), started=None, created=time.time(), finished=None,
                        cancel=threading.Event(),cache_dir=str(folder/'cache') if option['keep_cache'] else None,cache_owner=identity)
                    self.jobs[identity] = job
                    self._persist(job, strict=True)
                    added.append(identity)
            except OSError:
                for folder in folders:
                    self.jobs.pop(folder.name, None)
                    shutil.rmtree(folder, ignore_errors=True)
                raise
            # Bound resident history; disk results remain recoverable.
            for identity in list(self.jobs):
                if len(self.jobs) <= 100: break
                if self.jobs[identity]['state'] in TERMINAL: del self.jobs[identity]
            result = [self.status(identity) for identity in added]
            self.condition.notify_all()
            return result

    def options(self, identity):
        with self.lock:
            if identity not in self.jobs: raise ValueError('Unknown job')
            return json.loads(json.dumps(self.jobs[identity]['options']))

    def retry(self, identity, changes=None):
        if changes is not None and not isinstance(changes,dict):raise ValueError('Ungültige Einstellungen')
        with self.condition:
            if identity not in self.jobs:raise ValueError('Unknown job')
            old=self.jobs[identity]
            if old['state'] not in TERMINAL:raise ValueError('Laufenden Auftrag zuerst beenden')
            options=dict(old['options'],**(changes or {}))
            result=self.submit(options)
            job=self.jobs[result['id']];job['retry_of']=identity
            if old.get('kind')=='refine' and changes is None:
                parent=old.get('parent') or {k:old[k] for k in
                    ('id','cache_dir','first_frame','end_frame','native_fps','frame_count','cropped','preview') if k in old}
                if parent.get('cache_dir') and Path(parent['cache_dir']).is_dir():
                    job.update(kind='refine',parent=dict(parent),refine_of=old.get('refine_of',identity))
            self._persist(job)
            return self.status(job['id'])

    def refine(self, identity, changes):
        from postprocess import FINISHING
        if not isinstance(changes,dict) or set(changes)-FINISHING:raise ValueError('Nur Kanten, Farbsäume und Ausgabe ändern')
        with self.condition:
            if identity not in self.jobs:raise ValueError('Unknown job')
            old=self.jobs[identity]
            if old['state']!='completed' or not old.get('cache_dir') or not Path(old['cache_dir']).is_dir():
                raise ValueError('Korrekturdaten fehlen. KI-Auftrag mit Korrekturdaten erneut starten.')
            result=self.submit(dict(old['options'],**changes))
            job=self.jobs[result['id']]
            job.update(kind='refine',refine_of=identity,parent={k:old[k] for k in
                ('id','cache_dir','first_frame','end_frame','native_fps','frame_count','cropped','preview')})
            job['parent']['cache_owner']=old.get('cache_owner') or old['id']
            self._persist(job)
            return self.status(job['id'])

    def _loop(self):
        while True:
            with self.condition:
                queued = next((j for j in self.jobs.values() if j['state'] == 'queued'), None)
                if queued is None:
                    if self.closed: return
                    self.condition.wait()
                    continue
                job = queued
                self.active = job['id']
                job.update(state='running', started=time.time())
                self._persist(job)
            try:
                spec = dict(id=job['id'], folder=job['folder'], options=job['options'], kind=job.get('kind','inference'))
                if job.get('kind')=='refine': spec['parent']=job['parent']
                result = self.worker.run(spec, job['cancel'])
                with self.lock:
                    if not job['cancel'].is_set():
                        output = Path(result['output']).resolve()
                        if not output.is_relative_to(Path(job['folder']).resolve()) or not output.is_file():
                            raise RuntimeError('Ausgabedatei fehlt oder ist ungültig')
                        job.update({k: v for k, v in result.items() if k not in ('ok', 'resident')})
                        job['state'] = 'completed'
            except Exception as error:
                with self.lock: job.update(state='failed', error=str(error), output=None)
            finally:
                with self.condition:
                    if job['cancel'].is_set(): job.update(state='cancelled', output=None)
                    job['finished'] = time.time()
                    self._persist(job)
                    self.active = None
                    self.condition.notify_all()

    def status(self, identity):
        from bridge import describe_progress, explain_failure
        with self.lock:
            if identity not in self.jobs: raise ValueError('Unknown job')
            job = self.jobs[identity]
            result = {k: v for k, v in job.items() if k not in ('cancel', 'options', 'folder', 'started', 'created', 'finished', 'parent')}
            result['elapsed'] = round((job['finished'] or time.time()) - (job['started'] or job['created']))
            result['position'] = [j['id'] for j in self.jobs.values() if j['state'] == 'queued'].index(identity) + 1 if job['state'] == 'queued' else 0
        try:
            with open(result['log'], 'rb') as log:
                log.seek(0, 2)
                log.seek(max(0, log.tell() - 4096))
                result['detail'] = log.read().decode('utf-8', 'replace')
        except FileNotFoundError: result['detail'] = ''
        result['can_refine'] = bool(result['state']=='completed' and result.get('frame_count') and result.get('cache_dir') and Path(result['cache_dir']).is_dir())
        result['progress'] = describe_progress(result['detail'], result['state'])
        result['message'] = explain_failure(result['detail'], result['error']) if result['state'] == 'failed' else None
        return result

    def list(self):
        with self.lock: return [self.status(identity) for identity in self.jobs]

    def cancel(self, identity):
        with self.condition:
            if identity not in self.jobs: raise ValueError('Unknown job')
            job = self.jobs[identity]
            if job['state'] not in TERMINAL:
                job['cancel'].set()
                Path(job['folder'], 'cancel').touch()
                if job['state'] == 'queued': job.update(state='cancelled', finished=time.time())
                else: job['state'] = 'cancelling'
                self._persist(job)
            return self.status(identity)

    def release(self):
        with self.lock:
            if any(j['state'] not in TERMINAL for j in self.jobs.values()): raise ValueError('Zuerst laufende und wartende Aufträge beenden')
            self.worker.release()
            return {'resident': False}

    def close(self):
        with self.condition:
            self.closed = True
            for identity in list(self.jobs): self.cancel(identity)
            self.condition.notify_all()
        self.thread.join(timeout=23)
        self.worker.close()
        self.thread.join(timeout=4)
