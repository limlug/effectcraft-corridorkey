#!/usr/bin/env python3
"""Local JSON-lines bridge for the CorridorKey EffectCraft panel (stdlib only)."""
from __future__ import annotations

import argparse
import hmac
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
import uuid

from runtime_paths import ADDON_ROOT, runtime_root
ROOT = ADDON_ROOT
MOVIES = {".mov", ".mp4", ".mkv", ".avi", ".webm", ".m4v", ".mxf"}
MAX_LINE = 1024 * 1024
TERMINAL = {"completed", "failed", "cancelled"}


def settings_dir():
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "EffectCraft"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/EffectCraft"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "effectcraft"


def publish_connection(path, port, token):
    """Publish credentials atomically for the same user's installed panel."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump({"api": 1, "port": port, "token": token, "pid": os.getpid(), "system_locale": os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "en"}, stream)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def existing_service(path, port):
    try:
        config = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(config, dict) or not isinstance(config.get("token"), str):
            return False
        if config.get("port") != port:
            return False
        with socket.create_connection(("127.0.0.1", port), timeout=0.5) as connection:
            connection.settimeout(0.5)
            with connection.makefile("rwb") as stream:
                stream.write((json.dumps({"method": "hello", "token": config["token"]}) + "\n").encode())
                stream.flush()
                reply = json.loads(stream.readline(MAX_LINE))
        return reply.get("ok") and reply.get("result", {}).get("api") == 1 and reply.get("result", {}).get("backend") == "stock-cli" and reply.get("result", {}).get("review_api") == 1
    except (OSError, ValueError, KeyError):
        return False


def describe_progress(detail, state):
    if state == "queued":
        return {"label": "Wartet auf die Grafikkarte", "done": None, "total": None}
    if state == "completed":
        return {"label": "Freistellung fertig", "done": None, "total": None}
    if state in ("cancelled", "cancelling", "failed"):
        return {"label": {"cancelled": "Abgebrochen", "cancelling": "Wird abgebrochen", "failed": "Verarbeitung fehlgeschlagen"}[state], "done": None, "total": None}
    finishing = re.findall(r"Finishing frame (\d+)/(\d+)", detail)
    if finishing:
        done,total=map(int,finishing[-1])
        return {"label":f"Kantenkorrektur · Bild {done} von {total}","done":done,"total":total}
    windows = re.findall(r"window (\d+)/(\d+)", detail)
    if windows:
        done, total = map(int, windows[-1])
        return {"label": f"Videoanalyse · Fenster {done} von {total}", "done": done, "total": total}
    if "RVM continuous prepass" in detail:
        label = "Bewegung im Clip analysieren"
    elif "loaded weights" in detail:
        label = "Video vorbereiten"
    elif "Loading CorridorKey" in detail:
        label = "KI-Modelle laden · beim Start kurz warten"
    else:
        label = "Verarbeitung wird vorbereitet"
    return {"label": label, "done": None, "total": None}


def explain_failure(detail, error):
    text = (detail + " " + (error or "")).lower()
    if "out of memory" in text:
        return "Der Grafikspeicher reicht nicht. Wähle Speichersparend und schließe andere GPU-Anwendungen."
    if "no module named" in text:
        return "Der Python-Umgebung fehlt ein benötigtes Paket. Bitte die Einrichtung prüfen."
    if "cuda" in text and any(word in text for word in ("unavailable", "requires", "driver")):
        return "Die NVIDIA-Grafikkarte ist nicht erreichbar. Bitte Treiber und CUDA-Umgebung prüfen."
    if "no space left" in text:
        return "Der Speicherplatz ist aufgebraucht. Bitte Platz für die Ausgabedatei schaffen."
    return "Der Clip konnte nicht verarbeitet werden. Unter Details steht die vollständige Fehlermeldung."


from jobs import Jobs
from picker import Picker
from player import Player
from tasks import Tasks
from bundles import Bundles
from storage import Storage
from review import Review,gpu_status


class Bridge:
    def __init__(self, jobs, token):
        self.jobs = jobs
        self.token = token
        self.auto_updates = False
        self.picker = Picker()
        self.tasks = Tasks()
        self.player = Player(jobs)
        self.bundles = Bundles(jobs,self.tasks)
        self.storage = Storage(jobs,self.player,self.tasks)
        self.review = Review(jobs,self.tasks)

    def dispatch(self, request):
        if not isinstance(request, dict):
            raise ValueError("Expected a JSON object")
        token = request.get("token")
        if not isinstance(token, str) or not hmac.compare_digest(token.encode(), self.token.encode()):
            raise ValueError("Invalid access token")
        params = request.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("params must be an object")
        method = request.get("method")
        if method in {"retry","refine","job.options","player.open","player.frame","player.close","storage.clean","package.start","task.status","task.cancel"}:
            if not isinstance(params.get("id"),str) or not 1<=len(params["id"])<=128:raise ValueError("Missing or invalid id")
        if method == "hello":
            return {"api": 1, "name": "CorridorKey for EffectCraft", "active": self.jobs.active,
                    "auto_updates": self.auto_updates, "version": "0.7.0-rc1", "backend": "stock-cli", "keep_warm_supported": False, "review_api": 1,
                    "resident": self.jobs.worker.loaded, "model_loads": self.jobs.worker.loads}
        if method == 'gpu.status': return gpu_status()
        if method == 'review.detail': return self.review.detail(params)
        if method == 'mask.reference': return self.review.reference(params)
        if method == 'mask.points': return self.review.select(params.get('id'),params.get('points'),True)
        if method == 'mask.select': return self.review.select(params.get('id'),params.get('points'))
        if method == "retry": return self.jobs.retry(params.get("id"),params.get("changes"))
        if method == "refine": return self.jobs.refine(params.get("id"),params.get("changes"))
        if method == "job.options": return self.jobs.options(params.get("id"))
        if method == "player.open": return self.player.open(params.get("id"))
        if method == "player.frame": return self.player.frame(params.get("id"),params.get("seconds",0),params.get("view","checker"),params.get("playing",False))
        if method == "player.close": return self.player.close_view(params.get("id"))
        if method == "storage.report": return self.storage.report()
        if method == "storage.plan": return self.storage.plan(params.get("ids"),params.get("include_cache",False),params.get("references"))
        if method == "storage.clean": return self.storage.clean(params.get("id"))
        if method == "package.prepare": return self.bundles.prepare()
        if method == "package.start": return self.bundles.start(params.get("id"),params.get("destination"),params.get("project"),params.get("jobs"),params.get("include_cache",True),params.get("presets","{}"))
        if method == "package.restore": return self.bundles.restore(params.get("project"))
        if method == "task.status": return self.tasks.status(params.get("id"))
        if method == "task.cancel": return self.tasks.cancel(params.get("id"))
        if method == "queue": return self.jobs.list()
        if method == "submit_batch": return self.jobs.submit_batch(params.get("items"))
        if method == "release_memory": return self.jobs.release()
        if method == "picker.start": return self.picker.start(params.get("kind"),params.get("language","en"))
        if method == "picker.status": return self.picker.status(params.get("id"))
        if method == "submit":
            return self.jobs.submit(params)
        if method in ("status", "cancel"):
            job_id = params.get("id")
            if not isinstance(job_id, str):
                raise ValueError("Missing job id")
            return getattr(self.jobs, method)(job_id)
        raise ValueError("Unknown method")

    def close(self):
        self.player.close()
        self.tasks.close()


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(5)
        try:
            # Exactly one JSON line per connection; HTTP requests cannot become jobs.
            raw = self.rfile.readline(MAX_LINE + 1)
            if len(raw) > MAX_LINE or not raw.endswith(b"\n"):
                raise ValueError("Request too long or incomplete")
            request = json.loads(raw.decode("utf-8"))
            reply = {"ok": True, "result": self.server.bridge.dispatch(request)}
        except (ValueError, OSError) as exc:
            reply = {"ok": False, "error": str(exc)}
        self.wfile.write((json.dumps(reply, ensure_ascii=True) + "\n").encode("utf-8"))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def pulse_panels(port, bridge, stop):
    """v0.16 exposes scheduleTask but does not drive it. Pulse only our named
    heartbeat control through the app's documented local control channel.
    The UI callback still owns all project and job operations.
    """
    def controls(node):
        yield node
        for child in node.get("children", []):
            yield from controls(child)

    while not stop.is_set():
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5) as connection:
                connection.settimeout(2)
                with connection.makefile("rwb") as stream:
                    def command(name, params):
                        stream.write((json.dumps({"id": 1, "method": "engine.execute",
                            "params": {"command": name, "params": params}}) + "\n").encode())
                        stream.flush()
                        reply = json.loads(stream.readline(1024 * 1024))
                        if not reply.get("ok"):
                            raise ValueError("EffectCraft command unavailable")
                        return reply["result"]
                    windows = command("scriptui.list", {})
                    bridge.auto_updates = True
                    for window in windows:
                        if window.get("title") != "CorridorKey":
                            continue
                        tree = command("scriptui.get", {"window": window["window"]})
                        if any(node.get("name") == "heartbeat" for node in controls(tree["root"])):
                            command("scriptui.click", {"window": window["window"], "widget": "heartbeat"})
        except (OSError, ValueError, KeyError, TypeError):
            bridge.auto_updates = False
        stop.wait(.125 if bridge.player.fast_updates else 1)


def check_runtime(root=None):
    root=Path(root) if root is not None else runtime_root()
    """Read-only setup check; importing CUDA stays in the selected Python process."""
    problems = []
    for module in ("torch", "cv2", "numpy", "transformers", "timm", "safetensors",
                   "huggingface_hub", "einops", "scipy", "PIL", "tqdm", "utils3d"):
        if importlib.util.find_spec(module) is None:
            problems.append(f"Missing Python dependency: {module}")
    for binary in ("ffmpeg","ffprobe"):
        if not shutil.which(binary):problems.append(f"{binary} is missing from PATH")
    for name in ("infer.py","corridorkey/runtime.py"):
        if not (root/name).is_file():problems.append(f"Missing original CorridorKey CLI: {name}")
    for name in ("weights/corridorkey_v2.safetensors", "weights/foundation_stats.safetensors",
                 "vfms/cradio/C-RADIOv4-SO400M/model.safetensors", "vfms/moge/model.pt",
                 "vfms/rvm/pretrain_rvm_small16_256_204031069.npz"):
        if not (Path(root) / name).is_file():
            problems.append(f"Missing model asset: {name}")
    if importlib.util.find_spec("torch") is not None:
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)"],
                capture_output=True, timeout=30, check=False)
            if result.returncode:
                problems.append("CUDA is unavailable in this Python environment")
        except (OSError, subprocess.TimeoutExpired) as exc:
            problems.append(f"CUDA check failed: {exc}")
    for problem in problems:
        print(f"[MISSING] {problem}")
    if not problems:
        print("Runtime prerequisites found. A real inference test is still required.")
    return 1 if problems else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9878)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "out_effectcraft")
    parser.add_argument("--python", default=sys.executable, help="Python with CorridorKey dependencies")
    parser.add_argument("--check", action="store_true", help="Check this Python's dependencies, CUDA and model files; exit")
    parser.add_argument("--connection-file", type=Path, default=settings_dir() / "corridorkey-connection.json")
    parser.add_argument("--background", action="store_true", help="Start the local service in the background, or reuse it")
    parser.add_argument("--effectcraft-port", type=int, default=9877, help="Local EffectCraft control port (v0.16 timer compatibility)")
    args = parser.parse_args()
    if args.check:
        raise SystemExit(check_runtime())
    if not 1 <= args.port <= 65535 or not 1 <= args.effectcraft_port <= 65535:
        parser.error("port must be between 1 and 65535")
    if existing_service(args.connection_file, args.port):
        print("CorridorKey ist bereits bereit. Öffne das CorridorKey-Panel in EffectCraft.")
        return
    if args.background:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        logpath = args.output_dir / "service.log"
        fd = os.open(logpath, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
        os.chmod(logpath, 0o600)
        command = [sys.executable, str(Path(__file__).resolve()), "--port", str(args.port),
                   "--output-dir", str(args.output_dir.resolve()), "--python", args.python,
                   "--connection-file", str(args.connection_file.resolve())]
        command += ["--effectcraft-port", str(args.effectcraft_port)]
        options = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NO_WINDOW}
        with os.fdopen(fd, "ab") as log:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **options)
        for _ in range(50):
            if existing_service(args.connection_file, args.port):
                print("CorridorKey ist bereit. Das EffectCraft-Panel verbindet sich automatisch.")
                return
            if process.poll() is not None:
                break
            time.sleep(0.1)
        raise SystemExit(f"CorridorKey konnte nicht gestartet werden. Details: {logpath}")
    token = secrets.token_urlsafe(24)
    jobs = Jobs(runtime_root(), args.output_dir, args.python)
    with Server(("127.0.0.1", args.port), Handler) as server:
        server.bridge = Bridge(jobs, token)
        publish_connection(args.connection_file, args.port, token)
        stop_pulse = threading.Event()
        pulse_thread = threading.Thread(target=pulse_panels, args=(args.effectcraft_port, server.bridge, stop_pulse), daemon=True)
        pulse_thread.start()
        # Normal service termination must also stop an active inference process.
        def stop_service(signum, frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, stop_service)
        print(f"CorridorKey bridge: 127.0.0.1:{args.port}\nAccess token: {token}\n"
              f"Outputs: {jobs.output_root}\nDas EffectCraft-Panel verbindet sich automatisch. Ctrl+C beendet den Dienst.", flush=True)
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            pass
        finally:
            stop_pulse.set()
            server.bridge.close()
            jobs.close()
            try:
                if json.loads(args.connection_file.read_text(encoding='utf-8')).get("token") == token:
                    args.connection_file.unlink()
            except (OSError, ValueError):
                pass


if __name__ == "__main__":
    main()
