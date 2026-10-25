# Troubleshooting

## The panel cannot connect

Launch EffectCraft using the shared starter, not only the app icon. Check the script file/network permission. Keep the private connection file in the same settings folder as the installed panel; reinstall the panel if the settings folder moved. Do not paste your access token into a public issue.

For a useful service log, run the bridge in a terminal:

```bash
./venv/bin/python integrations/effectcraft/bridge.py
```

If another bridge is running, this command reuses it and exits. For custom ports, both the bridge's `--effectcraft-port` and the running EffectCraft `--control` port must agree. The main service port can be changed with `--port`; reinstall a matching panel with the appropriate settings directory if using separate instances.

## Stopping or restarting the bridge

Wait until all jobs and file operations have finished. If started in a terminal, press Ctrl+C there. If started in the background, `corridorkey-connection.json` contains its PID. Verify that this PID belongs to this add-on's `bridge.py` process before terminating it normally in your system's process manager. Never use a broad process-name kill that could stop EffectCraft or another Python program. Restart with the shared starter. Do not share the connection file: it contains the access token.

## GPU unavailable / missing dependencies

Run the prerequisite check with the exact `venv` interpreter from the installation instructions. Check that your NVIDIA driver supports the selected PyTorch CUDA wheels and that another environment has not been selected through `CORRIDORKEY_PYTHON`. The runtime currently requires NVIDIA CUDA; CPU-only PyTorch, AMD and Apple GPUs are not supported for AI inference.

If the error names a missing package, rerun setup or install the upstream requirements into this same environment. Model downloads require internet access. Check disk space before retrying. Do not substitute an unrelated CorridorKey checkpoint; the architecture and exported foundation statistics must match.

## GPU out of memory

Enable Reduce memory usage, close other GPU-heavy apps, shorten the range and test with a lower-resolution source. The external CorridorKey process exits after each AI job, releasing its GPU memory. This wrapper does not offer the earlier warm-model mode.

## Out of disk space

Correction caches are full-resolution float EXR sequences and can be large. Use Files → Estimate required space before starting. Preview cleanup first; deleting correction data is a separate option and disables instant correction for the affected jobs. Completed outputs and source media are never cleanup targets. Keep enough free space for both an export and any project package being created.

## Preview, alpha or import looks wrong

The panel's moving preview uses small proxies at up to 8 fps. Check a full-quality export for final judgement. MOV output uses straight alpha; EXR output is linear. The integration explicitly interprets imported footage where the host permits it. In EffectCraft 0.16 the new layer is rebuilt with supported transforms, masks and effects because native source replacement is unavailable. Advanced layer relationships are rejected before inference; render those sources first.

If the original source, timing or project changed after a job started, automatic insertion is refused. Restore the original context or import the output manually. Undo should restore the prior insertion. Original audio remains on the source layer, even when its picture is hidden.

## No correction data

An old output or an output created without retained raw data cannot be corrected from its final alpha video alone. Run AI once with Keep correction data enabled, then make further corrections from that new job.

## File picker does not open

Linux needs `zenity` or `tkinter` for the asynchronous picker. On Windows the configured Python must include tkinter. Enter mask paths manually if needed. Package destination selection requires a functioning directory picker.

## Language or glyph problems

Choose an explicit language in Service, then close and reopen the panel. Match System uses the locale exposed by the bridge process; restart the service after changing OS language. Missing square glyphs indicate missing system fonts for that script; install appropriate CJK/Georgian/Cyrillic fonts and reopen EffectCraft. Preserve custom preset and layer names exactly as entered when reporting problems.

## Reporting an issue

Include add-on version, EffectCraft version, OS, GPU, Python version, reproduction steps and whether it occurs in a short sample. Logs can contain private media paths. Remove tokens, usernames, source media and confidential project details before attaching them. Do not upload model weights or source footage without permission. The issue template lists the minimum useful information.
