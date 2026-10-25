"""Bounded, asynchronous 8 fps image playback for EffectCraft's ScriptUI."""
import math
from pathlib import Path
import queue
import subprocess
import threading
import time
import uuid

VIEWS = ('checker','matte','comparison','original')
WINDOW = 6


class Player:
    def __init__(self, jobs):
        self.jobs = jobs
        self.lock = threading.RLock()
        self.leases = {}
        self.pending = set()
        self.errors = {}
        self.work = queue.Queue()
        self.stop = threading.Event()
        self.process = None
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    @property
    def fast_updates(self):
        with self.lock:
            return any(v['playing'] and time.monotonic()-v['touched']<3 for v in self.leases.values())

    def open(self, identity):
        with self.jobs.lock:
            if identity not in self.jobs.jobs: raise ValueError('Unbekannter Auftrag')
            job = self.jobs.jobs[identity]
            if job['state']!='completed' or not job.get('frame_count'): raise ValueError('Zuerst einen fertigen Auftrag auswählen')
            if not Path(job['output']).is_file(): raise ValueError('Ergebnisdatei fehlt')
            job = dict(job)
        lease = uuid.uuid4().hex
        fps = min(8, job['native_fps'])
        duration = job['frame_count']/job['native_fps']
        with self.lock:
            # Expire idle views, not the current view or its files.
            self.leases={k:v for k,v in self.leases.items() if time.monotonic()-v['touched']<60}
            self.leases[lease]=dict(job=job, fps=fps, duration=duration, touched=time.monotonic(), playing=False)
        return dict(id=lease, fps=fps, duration=duration, frames=max(1,math.ceil(duration*fps)))

    def frame(self, identity, seconds=0, view='checker', playing=False):
        from options import number
        number(seconds,'Vorschauzeit',0,1e9)
        if view not in VIEWS or not isinstance(playing,bool): raise ValueError('Ungültige Vorschauansicht')
        with self.lock:
            if identity not in self.leases: raise ValueError('Vorschau erneut öffnen')
            lease=self.leases[identity]
            lease.update(touched=time.monotonic(),playing=playing)
            count=max(1,math.ceil(lease['duration']*lease['fps']))
            index=min(count-1,int(round(seconds*lease['fps'])))
            window=index//int(WINDOW*lease['fps'])
            folder=Path(lease['job']['folder'])/'playback'/str(window)
            path=folder/(f'{view}_{index:06d}.jpg')
            if (folder/'ready').is_file() and path.is_file():
                return dict(state='ready',path=str(path),seconds=index/lease['fps'],index=index)
            key=(lease['job']['id'],window)
            if key in self.errors: raise ValueError(self.errors[key])
            if key not in self.pending:
                self.pending.add(key)
                self.work.put((key,dict(lease),window))
            return dict(state='preparing',seconds=index/lease['fps'],index=index)

    def close_view(self, identity):
        with self.lock: self.leases.pop(identity,None)
        return {'closed':True}

    def protected(self):
        with self.lock:
            return {v['job']['id'] for v in self.leases.values() if time.monotonic()-v['touched']<60} | {key[0] for key in self.pending}

    def invalidate(self, identities):
        with self.lock:
            for key in list(self.errors):
                if key[0] in identities:del self.errors[key]

    def _command(self,args):
        self.process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            while True:
                try:
                    _,err=self.process.communicate(timeout=.2)
                    break
                except subprocess.TimeoutExpired:
                    if self.stop.is_set():
                        self.process.terminate()
                        try:self.process.communicate(timeout=2)
                        except subprocess.TimeoutExpired:self.process.kill();self.process.communicate()
                        raise InterruptedError('Vorschau beendet')
            if self.process.returncode:raise RuntimeError(err.decode('utf8','replace')[-1000:])
        finally:self.process=None

    def _extract(self, source, seconds, fps, count, target):
        self._command(['ffmpeg','-v','error','-y','-ss',str(seconds),'-i',str(source),'-an',
            '-vf',f'fps={fps}:round=up:eof_action=pass,scale=384:-1','-frames:v',str(count),'-pix_fmt','rgba','-threads','2',str(target)])

    def _loop(self):
        while not self.stop.is_set():
            try:item=self.work.get(timeout=.25)
            except queue.Empty:continue
            key,lease,window=item
            try:self._build(lease,window)
            except Exception as error:
                with self.lock:self.errors[key]='Vorschau konnte nicht vorbereitet werden: '+str(error)
            finally:
                with self.lock:self.pending.discard(key)
                self.work.task_done()

    def _build(self,lease,window):
        import os
        os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
        import cv2
        import numpy as np
        import shutil
        job=lease['job'];fps=lease['fps'];first=window*int(WINDOW*fps)
        total=max(1,math.ceil(lease['duration']*fps));last=min(total,first+int(WINDOW*fps))
        folder=Path(job['folder'])/'playback'/str(window)
        temp=folder.with_name(str(window)+'.partial')
        shutil.rmtree(temp,ignore_errors=True);temp.mkdir(parents=True)
        try:
            start=first/fps
            self._extract(job['input'],job['first_frame']/job['native_fps']+start,fps,last-first,temp/'source_%06d.png')
            source=sorted(temp.glob('source_*.png'))
            if not source:raise ValueError('Quelldatei enthält keine passenden Vorschaubilder')
            if not job.get('sequence'):
                self._extract(job['output'],start,fps,last-first,temp/'rgba_%06d.png')
                cutouts=sorted(temp.glob('rgba_*.png'))
                if not cutouts:raise ValueError('Ausgabe enthält keine passenden Vorschaubilder')
            else:
                sequence=sorted(Path(job['output']).parent.glob('*.exr'))
            for index in range(first,last):
                if self.stop.is_set():raise InterruptedError('Vorschau beendet')
                local=index-first
                original=cv2.imread(str(source[min(local,len(source)-1)]))
                if job.get('sequence'):
                    frame=min(len(sequence)-1,int(round(index/fps*job['native_fps'])))
                    rgba=cv2.imread(str(sequence[frame]),cv2.IMREAD_UNCHANGED)
                    if rgba is None:raise ValueError('EXR-Vorschaubild fehlt')
                    rgb=rgba[...,:3]
                    rgba[...,:3]=np.where(rgb<=.0031308,rgb*12.92,1.055*np.maximum(rgb,0)**(1/2.4)-.055)
                    rgba=np.clip(rgba*255,0,255).astype('uint8')
                else:rgba=cv2.imread(str(cutouts[min(local,len(cutouts)-1)]),cv2.IMREAD_UNCHANGED)
                if rgba is None or rgba.ndim!=3 or rgba.shape[2]!=4:raise ValueError('Alphakanal fehlt')
                if rgba.dtype==np.uint16:rgba=(rgba/257).round().astype('uint8')
                h,w=original.shape[:2];rgba=cv2.resize(rgba,(w,h))
                alpha=rgba[...,3:4].astype('float32')/255
                y,x=np.indices((h,w));checker=np.where(((x//16+y//16)%2)[...,None],160,100)
                comp=np.clip(rgba[...,:3]*alpha+checker*(1-alpha),0,255).astype('uint8')
                matte=np.repeat(rgba[...,3:4],3,axis=2)
                comparison=comp.copy();comparison[:,:w//2]=original[:,:w//2]
                for view,pixels in zip(VIEWS,(comp,matte,comparison,original)):
                    if not cv2.imwrite(str(temp/f'{view}_{index:06d}.jpg'),pixels,[cv2.IMWRITE_JPEG_QUALITY,88]):raise OSError('Vorschaudatei konnte nicht geschrieben werden')
            for path in temp.glob('*.png'):path.unlink()
            (temp/'ready').touch()
            if folder.exists():shutil.rmtree(folder)
            temp.rename(folder)
            # Keep at most three six-second windows per result.
            windows=sorted([p for p in folder.parent.iterdir() if p.is_dir() and p.name.isdigit()],key=lambda p:p.stat().st_mtime)
            for old in windows[:-3]:
                if old!=folder:shutil.rmtree(old,ignore_errors=True)
        except Exception:
            shutil.rmtree(temp,ignore_errors=True)
            raise

    def close(self):
        self.stop.set()
        self.thread.join(timeout=4)
