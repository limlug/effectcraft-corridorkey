#!/usr/bin/env python3
"""One-click desktop start: local service, EffectCraft and its CorridorKey panel."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from bridge import ROOT, settings_dir


def control(method, params):
    with socket.create_connection(("127.0.0.1", 9877), timeout=0.5) as connection:
        connection.settimeout(2)
        with connection.makefile("rwb") as stream:
            stream.write((json.dumps({"id": 1, "method": method, "params": params}) + "\n").encode())
            stream.flush()
            reply = json.loads(stream.readline(1024 * 1024))
            if not reply.get("ok"):
                raise ValueError(reply.get("error", "EffectCraft antwortet nicht"))
            return reply["result"]


def notify(message):
    print(message)
    binary = shutil.which("notify-send")
    if binary:
        subprocess.run([binary, "CorridorKey für EffectCraft", message], check=False)


def main():
    output = ROOT / "out_effectcraft"
    output.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    python = os.environ.get("CORRIDORKEY_PYTHON", str(runtime) if runtime.exists() else sys.executable)
    result = subprocess.run([python, str(Path(__file__).with_name("bridge.py")), "--background"],
                            capture_output=True, text=True, check=False)
    if result.returncode:
        notify("Der lokale Dienst konnte nicht starten. Details stehen in out_effectcraft/service.log.")
        return 1
    try:
        control("engine.execute", {"command": "scriptui.list", "params": {}})
    except (OSError, ValueError):
        # Never interrupt a normal EffectCraft instance to add a control port.
        lock = settings_dir() / "session.lock"
        try:
            state = json.loads(lock.read_text(encoding='utf-8'))
            os.kill(int(state["pid"]), 0)
        except (OSError, ValueError, KeyError):
            pass
        else:
            notify("Bitte EffectCraft regulär schließen und CorridorKey erneut starten. Dein Projekt vorher speichern. Der Dienst ist bereits bereit.")
            return 0
        config = settings_dir() / "corridorkey-launcher.json"
        app = json.loads(config.read_text(encoding='utf-8')).get("effectcraft") if config.exists() else shutil.which("effectcraft")
        if not app or not Path(app).is_file():
            notify("Den EffectCraft-Pfad einmalig mit install.py --effectcraft einrichten.")
            return 1
        with (output / "effectcraft.log").open("ab") as log:
            subprocess.Popen([app, "--control", "9877"], stdin=subprocess.DEVNULL,
                             stdout=log, stderr=subprocess.STDOUT, start_new_session=os.name != "nt")
        for _ in range(100):
            try:
                control("engine.execute", {"command": "scriptui.list", "params": {}})
                break
            except (OSError, ValueError):
                time.sleep(0.1)
        else:
            notify("EffectCraft konnte nicht geöffnet werden. Details stehen in out_effectcraft/effectcraft.log.")
            return 1
    windows = control("engine.execute", {"command": "scriptui.list", "params": {}})
    if not any(window.get("title") == "CorridorKey" for window in windows):
        control("engine.execute", {"command": "window.scriptPanel", "params": {"name": "CorridorKey.jsx"}})
    control("ui.focus", {})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
