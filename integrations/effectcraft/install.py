#!/usr/bin/env python3
"""Install the panel with a local connection-file locator (no credentials in JSX)."""
import argparse
import json
from pathlib import Path

from bridge import settings_dir
from build_panel import build_panel


def install(destination, effectcraft=None):
    destination = Path(destination).expanduser().resolve()
    panel = destination / "Scripts/ScriptUI Panels/CorridorKey.jsx"
    connection = destination / "corridorkey-connection.json"
    source = build_panel()
    content = "var CORRIDORKEY_CONNECTION_FILE = " + json.dumps(str(connection)) + ";\n" + source
    panel.parent.mkdir(parents=True, exist_ok=True)
    if panel.exists() and panel.read_text(encoding="utf-8") != content:
        panel.with_suffix(".jsx.bak").write_text(panel.read_text(encoding="utf-8"), encoding="utf-8")
    panel.write_text(content, encoding="utf-8")
    if effectcraft:
        app = Path(effectcraft).expanduser().resolve(strict=True)
        (destination / "corridorkey-launcher.json").write_text(json.dumps({"effectcraft": str(app)}, indent=2), encoding='utf-8')
    return panel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings-dir", type=Path, default=settings_dir())
    parser.add_argument("--effectcraft", type=Path, help="Path to the EffectCraft executable or AppImage")
    args = parser.parse_args()
    print("Panel installiert:", install(args.settings_dir, args.effectcraft))
