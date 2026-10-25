"""Parent-side transport for one persistent GPU process."""
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import threading
import time


class Worker:
    def __init__(self, root, python):
        self.root, self.python = Path(root), str(python)
        self.process = None
        self.responses = queue.Queue()
        self.loaded = False
        self.loads = 0

    def _start(self):
        if self.process and self.process.poll() is None: return
        self.responses = queue.Queue()
        options = {"start_new_session": True} if os.name != "nt" else {}
        self.process = subprocess.Popen([self.python, "-u", str(Path(__file__).with_name("worker.py")), "--root", str(self.root)],
            cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", **options)
        responses, process = self.responses, self.process
        def read():
            try:
                for line in process.stdout:
                    try: responses.put(json.loads(line))
                    except ValueError: pass
            finally: responses.put({"ok": False, "error": "GPU-Prozess wurde beendet", "fatal": True})
        threading.Thread(target=read, daemon=True).start()

    def run(self, spec, cancel):
        self._start()
        self.process.stdin.write(json.dumps({"op": "run", "spec": spec}) + "\n")
        self.process.stdin.flush()
        deadline = None
        while True:
            try:
                result = self.responses.get(timeout=0.2)
                self.loaded = result.get("resident", False)
                self.loads = result.get("model_loads", self.loads)
                if not result.get("ok"): raise RuntimeError(result.get("error", "GPU-Auftrag fehlgeschlagen"))
                return result
            except queue.Empty:
                if cancel.is_set():
                    Path(spec["folder"], "cancel").touch()
                    deadline = deadline or (time.monotonic() + 20)
                    if time.monotonic() >= deadline:
                        self.close()
                        raise InterruptedError("Auftrag beendet; die GPU-Sitzung wird beim nächsten Start neu geladen")

    def release(self):
        # Release by closing the idle process; the next job starts it lazily.
        self.close()

    def close(self):
        process = self.process
        if process and process.poll() is None:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                else: os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=3)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if process.poll() is None:
                    if os.name == "nt": process.kill()
                    else: os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)
        self.process = None
        self.loaded = False
