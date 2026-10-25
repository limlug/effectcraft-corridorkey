"""Inventory and targeted cleanup. Finished media are never cleanup candidates."""
import json
import re
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid
from bundles import media_paths


def size(path):
    if not path.exists() or path.is_symlink():return 0
    if path.is_file():return path.stat().st_size
    total=0
    for child in path.rglob('*'):
        try:
            if child.is_file() and not child.is_symlink():total+=child.stat().st_size
        except OSError:pass
    return total


class Storage:
    def __init__(self,jobs,player,tasks):
        self.jobs,self.player,self.tasks=jobs,player,tasks
        self.lock=threading.RLock()
        self.report_data={'busy':True}
        self.updated=0
        self.measuring=False
        self.plans={}

    def report(self):
        with self.lock:
            if not self.measuring and time.monotonic()-self.updated>5:
                self.measuring=True
                threading.Thread(target=self._measure,daemon=True).start()
            return dict(self.report_data)

    def _measure(self):
        try:
            with self.jobs.lock:jobs=[dict(j) for j in self.jobs.jobs.values()]
            folders=[p for p in self.jobs.output_root.iterdir() if re.fullmatch('[0-9a-f]{32}',p.name) and p.is_dir() and not p.is_symlink()]
            total=sum(size(p) for p in folders)+size(self.jobs.output_root/'_review')
            roots={Path(j['cache_dir']) for j in jobs if j.get('cache_dir')} | {p/'cache' for p in folders if (p/'cache').is_dir()}
            corrections=sum(size(p) for p in roots)
            previews=sum(size(p/'playback') for p in folders)
            entries=[dict(id=j['id'],name=j.get('context',{}).get('name') or Path(j['input']).name,
                          state=j['state'],preview_bytes=size(Path(j['folder'])/'playback'),
                          cache_bytes=size(Path(j['cache_dir'])) if j.get('cache_dir') else 0) for j in jobs]
            data=dict(busy=False,total_bytes=total,preview_bytes=previews,cache_bytes=corrections,
                      free_bytes=shutil.disk_usage(self.jobs.output_root).free,jobs=entries,gpu=None)
            binary=shutil.which('nvidia-smi')
            if binary:
                try:
                    result=subprocess.run([binary,'--query-gpu=memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=2,check=True)
                    total_mb,used_mb=map(int,result.stdout.splitlines()[0].split(','))
                    data['gpu']=dict(total_bytes=total_mb*1024**2,used_bytes=used_mb*1024**2)
                except (OSError,ValueError,subprocess.SubprocessError,IndexError):pass
            with self.lock:self.report_data=data;self.updated=time.monotonic()
        except OSError as error:
            with self.lock:self.report_data=dict(busy=False,error=str(error));self.updated=time.monotonic()
        finally:
            with self.lock:self.measuring=False

    def _references(self,references):
        if not isinstance(references,list) or len(references)>1000 or not all(isinstance(p,str) and len(p)<=8192 and Path(p).is_absolute() for p in references):raise ValueError('Ungültige Medienreferenzen')
        paths={Path(p).resolve() for p in references}
        with self.jobs.lock:
            projects={j.get('context',{}).get('project') for j in self.jobs.jobs.values()}
        for name in projects:
            if not name:continue
            project=Path(name)
            try:
                if project.is_file() and project.stat().st_size<64*1024*1024:
                    paths|=media_paths(json.loads(project.read_text(encoding='utf-8')),project.parent)
            except (OSError,ValueError):
                # Unknown references: preserve all generated data from that project.
                with self.jobs.lock:
                    for job in self.jobs.jobs.values():
                        if job.get('context',{}).get('project')==name:
                            paths.add(Path(job['folder'])/'playback')
                            if job.get('cache_dir'):paths.add(Path(job['cache_dir']))
        return paths

    def _candidates(self,identities,include_cache,references):
        protected_views=self.player.protected()
        with self.jobs.lock:
            jobs=list(self.jobs.jobs.values())
            active={j['id'] for j in jobs if j['state'] not in ('completed','failed','cancelled')}
            busy_caches={Path(j['parent']['cache_dir']).resolve() for j in jobs if j['id'] in active and j.get('parent',{}).get('cache_dir')}
            result={}
            for job in jobs:
                if job['id'] not in identities or job['id'] in active:continue
                folder=Path(job['folder']).resolve()
                if folder.parent!=self.jobs.output_root:continue
                candidates=[]
                if job['id'] not in protected_views:candidates.append((folder/'playback','preview'))
                if include_cache and job.get('cache_dir'):
                    cache=Path(job['cache_dir']).resolve()
                    if cache.parent.parent==self.jobs.output_root and cache.name=='cache' and cache not in busy_caches:
                        candidates.append((cache,'cache'))
                for path,kind in candidates:
                    if path.is_dir() and not path.is_symlink() and not any(p==path or p.is_relative_to(path) for p in references):
                        result[path]=kind
            return result

    def plan(self,identities=None,include_cache=False,references=None):
        if not isinstance(include_cache,bool):raise ValueError('Ungültige Cache-Auswahl')
        with self.jobs.lock:
            if identities is None:identities=list(self.jobs.jobs)
            if not isinstance(identities,list) or len(identities)>512 or any(not isinstance(i,str) or i not in self.jobs.jobs for i in identities):raise ValueError('Ungültige Auftragsauswahl')
        refs=self._references(references or [])
        candidates=self._candidates(identities,include_cache,refs)
        identity=uuid.uuid4().hex
        with self.lock:
            self.plans={identity:dict(ids=identities,cache=include_cache,references=list(map(str,refs)),created=time.monotonic())}
        return dict(id=identity,bytes=sum(size(p) for p in candidates),folders=len(candidates),includes_cache=include_cache)

    def clean(self,identity):
        with self.lock:
            if identity not in self.plans:raise ValueError('Aufräumvorschau zuerst aktualisieren')
            plan=self.plans[identity]
            if time.monotonic()-plan['created']>300:raise ValueError('Aufräumvorschau ist abgelaufen. Bitte aktualisieren.')
        def action(progress):
            refs=self._references(plan['references'])
            protected=self.player.protected()
            removed=0;freed=0
            # Rename under the queue lock; queued refinements protect their raw data.
            with self.jobs.lock:
                candidates=self._candidates(plan['ids'],plan['cache'],refs)
                trash=[]
                for path,kind in candidates.items():
                    if kind=='preview' and path.parent.name in protected:continue
                    amount=size(path)
                    target=path.with_name('.cleanup-'+uuid.uuid4().hex)
                    path.rename(target);trash.append((target,amount))
            for index,(path,amount) in enumerate(trash):
                # Once renamed, finish removing disposable files even if shutdown arrives.
                shutil.rmtree(path)
                freed+=amount;removed+=1
                progress(index+1,len(trash),'Räume Zwischendaten auf')
            self.player.invalidate(set(plan['ids']))
            with self.lock:self.updated=0
            return dict(bytes=freed,folders=removed)
        return self.tasks.start(action)
