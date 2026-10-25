# Installation, updates and removal

## Requirements

- EffectCraft desktop. Validated host: 0.16.0 on Linux. Newer versions need a compatibility check; the browser version cannot access this local service.
- Python 3.11 or 3.12 with venv and pip. The complete local test used 3.12.3.
- Git, ffmpeg and ffprobe available to the same terminal that starts the installer.
- NVIDIA RTX 30-series or newer GPU and a driver supporting the CUDA 12.8 PyTorch wheels. A separate CUDA toolkit is normally unnecessary for the prebuilt wheels. Refer to [PyTorch's versioned install commands](https://pytorch.org/get-started/previous-versions/).
- Network access during installation to GitHub, PyTorch's package index, PyPI, Hugging Face and the original model publishers. Inference runs locally after the required files are present.
- Several GB for dependencies and about 5 GB for weights, plus room for inputs, outputs and caches. Cached raw frames use 16 bytes per output pixel before EXR compression. Use the panel's space estimate before long clips.

On Debian/Ubuntu, these are typical prerequisite packages; use the equivalent packages on your distribution:

```bash
sudo apt install python3 python3-venv git ffmpeg
```

For the optional graphical file picker, install `zenity` or Python's `tkinter` package. Mask paths can also be entered manually. On Windows install Python, Git and an ffmpeg distribution including ffprobe, then reopen your terminal so PATH updates take effect. This project does not automatically install OS packages or GPU drivers.

## Recommended installation

Download this repository, extract it into a permanent writable folder, and run from that folder:

```bash
python3 setup_effectcraft.py --effectcraft "/absolute/path/to/EffectCraft.AppImage"
```

Windows PowerShell:

```powershell
py -3.12 setup_effectcraft.py --effectcraft "C:\Path\To\EffectCraft.exe"
```

Use `--dry-run` to print the complete installation plan without making changes. Use `--skip-weights` only if all required models already exist in the runtime checkout; the final prerequisite check still verifies them. `--launch` opens the app after a successful installation.

The installer:

1. Fetches official CorridorKey source into `runtime/CorridorKey2.0`, detached at `485f5e9ab759ead6138cc990776184b59d6ea971`.
2. Leaves that source unchanged. Existing edited checkouts are refused; no reset or patch is applied.
3. Creates `venv`, installs the recorded PyTorch wheels and the original requirements.
4. Runs the official downloader with the recorded CorridorKey model revision.
5. Installs the self-contained panel and checks prerequisites.

At runtime the wrapper launches the original `infer.py` in a separate process. It receives linear float EXR images and performs its own finishing/export. Each AI job loads its own model. Cached image correction requires no further inference. Temporary float image storage is required even when the cache is deleted after export.

The requirements inherited from CorridorKey contain version ranges. Code and model revisions are pinned; all transitive Python packages are not locked. Installing on another date can resolve different dependencies. If dependency resolution fails, report the package versions and use a fresh environment rather than changing a working installation blindly.

## Required EffectCraft setting

Enable **Allow Scripts to Write Files and Access Network** in EffectCraft preferences. This allows the JSX panel to read its connection file and contact the local bridge. The panel cannot start the bridge on its own.

The installer uses these settings directories:

| Platform | Settings directory |
| --- | --- |
| Linux | `$XDG_CONFIG_HOME/effectcraft`, normally `~/.config/effectcraft` |
| Windows | `%APPDATA%\EffectCraft` |
| macOS | Not supported for current CUDA inference |

Panel: `Scripts/ScriptUI Panels/CorridorKey.jsx`. Connection file: `corridorkey-connection.json`. Launcher configuration: `corridorkey-launcher.json`. Existing different panel contents are backed up as `CorridorKey.jsx.bak`.

## Start and verify

Linux:

```bash
./integrations/effectcraft/start_bridge.sh --launch
```

Windows:

```powershell
.\venv\Scripts\python.exe integrations\effectcraft\launch.py
```

The shared starter starts or reuses the bridge on loopback port 9878 and opens/reuses EffectCraft with control port 9877. If EffectCraft is already running without that connection, the starter asks you to save and close it normally; it does not terminate your app.

Verify that the panel says Connected in your chosen language. Save a project, import a short video and select its layer. Calculate a short preview before processing the complete range. Results live in the add-on's `out_effectcraft` folder.

Read-only environment check:

```bash
./venv/bin/python integrations/effectcraft/bridge.py --check
```

Windows uses `.\venv\Scripts\python.exe` in place of `./venv/bin/python`.

## Existing unmodified CorridorKey installation

Set `CORRIDORKEY_ROOT` to your original installation directory and `CORRIDORKEY_PYTHON` to a Python interpreter with its dependencies. The source must expose the recorded `infer.py` CLI and have its model files. The wrapper does not require or apply the old patch. Do not point this version at the previous patched checkout; use a clean copy. Setup refuses modified existing checkouts rather than resetting your files.

For a clean source checkout, use the official clone and recorded commit from UPSTREAM.md, install its original requirements and download the weights with its own script. Install the EffectCraft panel using this repository's `install.py`. The recommended setup helper performs those steps; `--dry-run` shows exact commands. There is no `git apply` step.

## Languages

The panel follows `general.language` in EffectCraft, including Match System where possible. You can override it under Service → Language. Reopen the panel after changing either language setting. Switching languages preserves jobs, presets and their original names. A stale service from an older version may need restarting to expose its system locale. See [language implementation and QA](LANGUAGES.md).

## Update

Save the project and wait for active processing and file operations to finish. Close EffectCraft normally and stop the bridge using the method described in [troubleshooting](TROUBLESHOOTING.md). Keep a backup of outputs and the settings folder. Download a new add-on version into a new folder, then run its setup. Reuse model files only after checking its recorded runtime/model revisions. Reopening the panel without restarting an old bridge does not update that bridge's running code.

Do not delete an older installation while project layers still refer to files in its `out_effectcraft` folder. Collect the project and media first, or keep those output folders in place.

## Removal

Save and close EffectCraft and stop the bridge. Remove the installed `CorridorKey.jsx`, its optional `.bak`, `corridorkey-connection.json` and `corridorkey-launcher.json` from the settings folder. Remove only shortcuts you created for CorridorKey. Delete the add-on folder only after moving or collecting any outputs referenced by projects. This also removes its virtual environment and downloaded runtime/models. EffectCraft's saved CorridorKey UI preferences are harmless and can remain.
