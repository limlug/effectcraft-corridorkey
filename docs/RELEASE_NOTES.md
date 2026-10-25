# 0.8.0 — edit inserted cutouts in place

Further corrections now update the existing cutout layer automatically instead of adding another layer. The layer keeps its identity, name, timing, animation, effects and masks. The first insertion is still explicit; subsequent cached corrections or matching reruns update that inserted result when finished. Each update is undoable, and an undone correction can be reapplied without another AI run.

- Edges → **Update inserted result in place** is enabled by default. Turn it off to insert a separate variant.
- Selecting a linked cutout processes the original input, never the already keyed result.
- Replacements recheck the captured target and preserve its existing interpretation frame rate.
- Shared/locked result media, manually changed sources and changed source-frame ranges are protected. The current result stays intact if correction processing fails; failed interpretation attempts to restore the previous generated file.
- All twelve provisional language catalogs include the new controls and notices.

Includes the 0.7 detail-review, A/B comparison, mask/reference and GPU-memory controls. The wrapper remains MIT licensed; the separately obtained CorridorKey program, models and dependencies retain their own terms. No runtime patches, model implementation or weights are bundled.

Validation: 106 local automated checks passed (49 Python, 52 panel, 5 installer). Real EffectCraft 0.16 tests on Linux verified unchanged layer ID, layer/project-item counts, name, timing and position keyframes through repeated cached updates, Undo and reapply. See docs/VALIDATION.md for the full evidence and limits.

Windows remains experimental. Fresh disposable-machine installation, native Windows inference, native-speaker translation review and Georgian rendering on a supporting host remain unverified. A normal minor-release tag does not expand those platform claims.

Update: finish active jobs, close the old local service, extract/pull this source and rerun setup_effectcraft.py, then start through the shared launcher. Existing output files and correction caches remain available. In-place updates keep earlier generated files on disk for Undo and comparison.
