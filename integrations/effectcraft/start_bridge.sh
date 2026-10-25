#!/usr/bin/env bash
set -euo pipefail
addon_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$addon_dir/../.." && pwd)"
runtime_python="${CORRIDORKEY_PYTHON:-$project_dir/venv/bin/python}"
if [[ ! -x "$runtime_python" ]]; then
    runtime_python="$(command -v python3)"
fi
if [[ "${1:-}" == "--launch" ]]; then
    shift
    exec "$runtime_python" "$addon_dir/launch.py" "$@"
fi
exec "$runtime_python" "$addon_dir/bridge.py" "$@"
