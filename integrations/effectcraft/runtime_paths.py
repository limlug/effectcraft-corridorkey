"""Locate the add-on and its separately downloaded CorridorKey installation."""
import os
from pathlib import Path

ADDON_ROOT = Path(__file__).resolve().parents[2]


def runtime_root():
    override=os.environ.get('CORRIDORKEY_ROOT')
    if override:return Path(override).expanduser().resolve()
    return ADDON_ROOT/'runtime/CorridorKey2.0'
