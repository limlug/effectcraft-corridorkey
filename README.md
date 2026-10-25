# CorridorKey for EffectCraft

[External-wrapper architecture](docs/WRAPPER_ARCHITECTURE.md): no runtime patches, no CorridorKey module imports. The original CLI runs as a separate process. The wrapper-owned code is MIT licensed. Using the external tool and its models remains subject to their own licenses.

A community add-on that removes green-screen backgrounds inside [EffectCraft](https://github.com/storytold/effectcraft), using [CorridorKey 2.0](https://github.com/nikopueringer/CorridorKey2.0) locally on an NVIDIA GPU.

**0.7.0 quality-of-life preview · Linux tested · Windows experimental · NVIDIA CUDA required**

[Deutsch](docs/README.de.md) · [Complete installation](docs/INSTALL.md) · [User guide](integrations/effectcraft/README.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Languages](docs/LANGUAGES.md)

## What it does

- Removes backgrounds from selected video layers, including batches and trimmed/work-area ranges.
- Preserves the source layer and its audio; imports a new layer with MOV transparency or an EXR sequence. Undo restores the previous state.
- Adjusts matte black/white points, expansion, feathering and green spill. Cached corrections avoid another AI run.
- Plays and scrubs lightweight previews inside the panel, with original, matte, checkerboard and comparison views.
- Saves presets, retries jobs, collects portable project packages and cleans disposable caches.
- Provides all eleven languages in EffectCraft 0.16 and a Georgian catalog for newer hosts, selected automatically or manually.

## New in 0.7

- Exact-frame detail inspection, frame stepping, 1–16x crop zoom and a movable original/result comparison.
- White, black, grey, checkerboard or your own image/video as a review background.
- Green/blue/off spill correction and separate opaque-core/edge coverage controls.
- A/B bookmarks for completed results and a return to the original result.
- Reference-frame inspection, mask-size checks, coloured keep/remove seed markers and an optional local colour-based selection assistant. This is a rough GrabCut selection, not semantic AI segmentation or Resolve Magic Mask.
- Up to sixteen Add/Subtract layer-mask snapshots at the chosen reference frame.
- An optional reference anywhere inside the processed range, using original-CLI forward and reversed passes; an automatic range-start reference keeps the single-pass path.
- Optional GPU-memory display and explicit temporal windows, alongside the upstream automatic setting.

See [the new controls and their limits](docs/QUALITY_OF_LIFE.md). All new UI strings are included in the twelve catalogs; translations remain provisional.

## Before installing

You need the **desktop version of EffectCraft**, Python **3.11 or 3.12**, Git, **ffmpeg and ffprobe** on your PATH, and an NVIDIA RTX 30-series or newer GPU with a driver compatible with CUDA-enabled PyTorch 2.9.1 / CUDA 12.8. Linux with EffectCraft 0.16.0, Python 3.12 and an RTX 3080 Laptop GPU (16 GB) has been exercised. Windows installation is provided but has not been tested end to end. The web version and macOS inference are not supported.

Allow several gigabytes for the Python environment and approximately **5 GB for model downloads**, plus substantial space for footage, outputs and optional correction caches. Available VRAM limits usable resolution; enable reduced memory usage for smaller GPUs. No real-time performance or universal minimum VRAM is promised.

Read [LICENSE](LICENSE), [third-party model notices](THIRD_PARTY_NOTICES.md) and [license/release status](docs/LICENSING.md) before use. This is an independent integration, not the official paid CorridorKey plugin. The **wrapper-owned code is MIT licensed**; CorridorKey and its models retain their separate terms. See the [source review](docs/SOURCE_AUDIT.md).

## Quick start: Linux

Clone this add-on repository or download and extract its source archive. Open a terminal in that folder, then run:

```bash
python3 setup_effectcraft.py --effectcraft "/absolute/path/to/EffectCraft.AppImage"
```

The installer downloads the official CorridorKey source at a recorded commit, creates a local `venv`, installs PyTorch and dependencies, downloads the model files, installs the panel, and checks CUDA and required files. Model weights and the complete CorridorKey source are **not bundled in this add-on repository**.

In EffectCraft, enable **Allow Scripts to Write Files and Access Network**. Save your work and close EffectCraft normally once if it was started without the control connection. Start the app and panel together with:

```bash
./integrations/effectcraft/start_bridge.sh --launch
```

Open a saved project, select an unlocked video layer and start with **Short preview from playhead**. Then choose the desired time range and **Remove background**, followed by **Insert result**. Exact labels follow your chosen language.

## Quick start: Windows (experimental)

Install Python 3.12, Git and an ffmpeg distribution that includes ffprobe; enable their PATH options. In PowerShell inside this add-on folder:

```powershell
py -3.12 setup_effectcraft.py --effectcraft "C:\Path\To\EffectCraft.exe"
.\venv\Scripts\python.exe integrations\effectcraft\launch.py
```

Enable EffectCraft's script file/network permission as above. See [complete installation](docs/INSTALL.md) for verification, manual setup, updates and removal.

The separate CLI loads its model for every AI pass. A reference after the range start requires two passes and additional temporary disk space. Cached corrections remain available, but the previous GPU warm mode is not offered. Temporary float EXR frames are required for each AI job.

## Known limits

Processing requires video-file footage. Precompositions and source image sequences must first be rendered to video. With EffectCraft 0.16, 3D, time remapping, track mattes and active layer styles also require a rendered source. EXR output is supported. Preview playback uses up to eight proxy frames per second; exports retain the source frame rate.

Cached corrections require a job created with **Keep correction data for later edits** enabled. Older results need one fresh AI run. Project packages collect media declared in `.ecproj`; fonts, effect plugins and unlisted external dependencies are not collected.

## Development and validation

```bash
python3 -m unittest discover -s integrations/effectcraft -p 'test_*.py' -v
node integrations/effectcraft/test_panel.cjs
```

The standard-library suite works without weights or a GPU; numerical tests skip when their dependencies are unavailable. Use the configured `venv` for the full local suite. CI checks the external-program boundary and fetches the pinned original source without patches. See [validation scope](docs/VALIDATION.md) and [contributing](CONTRIBUTING.md).

## Attribution

CorridorKey 2.0 was created by Zachary Harris with Niko Pueringer and Corridor Digital. This repository contains the community EffectCraft integration and independent image finishing. Foundation models retain their publishers' licenses. EffectCraft is a separate project by Storytold and its contributors. No affiliation or endorsement is implied.
