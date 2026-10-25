"""Small background operations for file copies and disposable-cache cleanup."""
import threading
import time
import uuid


class Tasks:
    def __init__(self):
        self.lock=threading.RLock()
        self.tasks={}
        self.closed=False

    def start(self, action):
        with self.lock:
            if self.closed:raise ValueError('Dienst wird beendet')
            if any(t['state']=='running' for t in self.tasks.values()):raise ValueError('Dateiaktion läuft bereits. Bitte kurz warten.')
            identity=uuid.uuid4().hex
            stop=threading.Event()
            task=dict(id=identity,state='running',message='Wird vorbereitet',done=0,total=0,stop=stop,thread=None)
            self.tasks[identity]=task
            while len(self.tasks)>30:del self.tasks[next(iter(self.tasks))]
        def progress(done,total,message):
            if stop.is_set():raise InterruptedError('Dateiaktion abgebrochen')
            with self.lock:task.update(done=done,total=total,message=message)
        def run():
            try:
                result=action(progress)
                with self.lock:task.update(state='completed',result=result,message='Fertig')
            except Exception as error:
                with self.lock:task.update(state='cancelled' if stop.is_set() else 'failed',error=str(error),message=str(error))
        thread=threading.Thread(target=run,daemon=True);task['thread']=thread;thread.start()
        return self.status(identity)

    def status(self,identity):
        with self.lock:
            if identity not in self.tasks:raise ValueError('Unbekannte Dateiaktion')
            return {k:v for k,v in self.tasks[identity].items() if k not in ('stop','thread')}

    def cancel(self,identity):
        with self.lock:
            if identity not in self.tasks:raise ValueError('Unbekannte Dateiaktion')
            self.tasks[identity]['stop'].set()
        return self.status(identity)

    def close(self):
        with self.lock:
            self.closed=True
            for task in self.tasks.values():task['stop'].set()
            threads=[t['thread'] for t in self.tasks.values()]
        deadline=time.monotonic()+4
        for thread in threads:thread.join(timeout=max(0,deadline-time.monotonic()))
