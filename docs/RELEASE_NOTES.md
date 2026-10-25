# 0.7.0-rc1 — detail review and mask workflow

New exact-frame inspection with previous/next, crop zoom, movable before/after split and white/black/grey/checkerboard or custom image/video review backgrounds. Bookmark completed A/B results and return through the correction chain to the original.

Adds Green/Blue/Off spill finishing, separate opaque-core and edge coverage, and preset persistence. Cached corrections still avoid another AI run. The mask assistant inspects the chosen source reference and checks image-mask dimensions. Coloured keep/remove points can generate a rough local GrabCut hint; this is not semantic AI segmentation or Magic Mask. Mark distinct subject colours separately. Up to sixteen Add/Subtract layer-mask snapshots are combined at the reference time.

A reference within the processed range can start original-CLI forward and reversed passes, with outputs restored to the original frame order. This requires a matching starting mask, two model loads and additional temporary disk space. Reversal is disk-backed. Mask videos retain their original timing and use the start reference. GPU telemetry and manual temporal-window options supplement the upstream automatic default.

The wrapper remains MIT licensed. The official CorridorKey source, weights and dependencies are obtained separately and retain their own licenses. No runtime patches or model implementation are bundled. See docs/QUALITY_OF_LIFE.md for control semantics and limits, and docs/LICENSING.md for the license boundary.

Linux GPU and native EffectCraft workflow tests were performed on the existing configured system and short samples of the user's project clip. Windows remains experimental. Fresh disposable-machine installation, native Windows inference, native-speaker translation review and Georgian rendering on a supporting host remain unverified. The twelve catalogs include the new controls, but translations are provisional. This is a prerelease, not a universal production-quality or long-shot matting guarantee.

Update: finish active jobs and stop the previous local service, rerun setup_effectcraft.py, then open the shared launcher. The new panel requires the 0.7 review-capable bridge; existing results and correction caches remain usable.
