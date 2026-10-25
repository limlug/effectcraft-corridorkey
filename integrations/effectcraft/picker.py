"""Asynchronous OS file dialog; EffectCraft 0.16's File.openDialog is a stub."""
import json
import os
from pathlib import Path
from build_panel import LANGUAGES
import shutil
import subprocess
import sys
import threading
import uuid


class Picker:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = {}

    def start(self, kind, language="en"):
        if language not in LANGUAGES: raise ValueError('Unsupported language')
        if kind not in ('image', 'video', 'folder'): raise ValueError('Ungültige Dateiauswahl')
        with self.lock:
            if any(r['state'] == 'pending' for r in self.requests.values()): raise ValueError('Eine Dateiauswahl ist bereits geöffnet')
            identity = uuid.uuid4().hex
            self.requests = {identity: {'id': identity, 'state': 'pending'}}
        threading.Thread(target=self._run, args=(identity, kind, language), daemon=True).start()
        return self.status(identity)

    def _run(self, identity, kind, language):
        try:
            patterns = '*.png *.jpg *.jpeg' if kind == 'image' else '*.mov *.mp4 *.mkv *.avi *.webm *.m4v *.mxf'
            catalog=json.loads((Path(__file__).parent/'locales'/f'{language}.json').read_text(encoding='utf-8'))
            title='CorridorKey – '+catalog['Collect project and media…' if kind=='folder' else 'Choose mask…']
            label=catalog['Matte']
            if shutil.which('zenity'):
                args=['zenity','--file-selection','--title='+title]
                args += ['--directory'] if kind=='folder' else ['--file-filter='+label+' | '+patterns]
            else:
                script=('import tkinter as t;from tkinter import filedialog;'
                    'r=t.Tk();r.withdraw();r.attributes("-topmost",True);')
                script += ('p=filedialog.askdirectory(title='+repr(title)+');' if kind=='folder' else
                    'p=filedialog.askopenfilename(title='+repr(title)+',filetypes=[('+repr(label)+','+repr(patterns)+')]);')
                script += 'print(p);r.destroy()'
                args=[sys.executable,'-c',script]
            result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ,PYTHONIOENCODING="utf-8"), timeout=600)
            path = result.stdout.strip()
            if result.returncode not in (0, 1): raise RuntimeError('Dateiauswahl nicht verfügbar. Bitte den Pfad eintragen.')
            value = {'id': identity, 'state': 'selected' if path else 'cancelled', 'path': path}
        except Exception as error: value = {'id': identity, 'state': 'error', 'error': str(error)}
        with self.lock: self.requests[identity] = value

    def status(self, identity):
        with self.lock:
            if identity not in self.requests: raise ValueError('Unbekannte Dateiauswahl')
            return dict(self.requests[identity])
