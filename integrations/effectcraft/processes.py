"""Supervise external programs without importing or changing their code."""
import os
from pathlib import Path
import signal
import subprocess
import tempfile

_active=set()


def check_cancel(path):
    if path is not None and Path(path).exists():raise InterruptedError('Job cancelled')


def stop(process):
    if process.poll() is not None:return
    if os.name=='nt':
        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
    else:
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:return
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        if os.name=='nt':process.kill()
        else:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        process.wait(timeout=3)


def stop_all():
    for process in list(_active):stop(process)


def run(args,cancel,log=None):
    check_cancel(cancel)
    with tempfile.TemporaryFile() as diagnostic:
        process=subprocess.Popen([str(a) for a in args],stdout=log if log is not None else subprocess.DEVNULL,
            stderr=diagnostic,start_new_session=os.name!='nt',env=dict(os.environ,PYTHONIOENCODING='utf-8'))
        _active.add(process)
        try:
            while True:
                try:code=process.wait(timeout=.2);break
                except subprocess.TimeoutExpired:check_cancel(cancel)
            check_cancel(cancel)
            if code:
                diagnostic.seek(0,2);diagnostic.seek(max(0,diagnostic.tell()-4096))
                raise RuntimeError(diagnostic.read().decode('utf-8','replace') or f'External process failed ({code})')
        finally:
            stop(process);_active.discard(process)
