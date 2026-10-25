# Quality-of-life controls in 0.7

## Exact-frame review

Detail review decodes the requested native output-frame index (zero based), independently of the existing lightweight 8-fps playback. Previous/next steps by one real frame. Zoom crops around Centre X/Y; 1x means the whole frame, not a promise of one source pixel per screen pixel. The display is bounded to 768×432; enlarge the zoom to inspect finer source detail. The separate View selector chooses composite, matte, original/result split or original. Move the comparison slider and press Update detail. White/black/grey/checkerboard backgrounds expose different edge defects. A background image/video can be selected; video time follows the result from zero, holding its last frame when shorter. These are inspection backgrounds and are not baked into the exported result.

Frame extraction runs in the background with a 60-second decoder timeout. Very long/slow files can exceed it. Helpers share the existing background-operation slot with packaging/cleanup; wait for the current operation. Buttons disable during helper work. No AI is run by detail inspection.

## A/B and original

Remember A/B bookmarks the currently selected completed job, not unapplied values in the Edges tab. First apply a cached correction and wait for its result, then remember it. View A/B switches between those results and updates the detail image without inserting layers or rerunning AI. Original result follows the correction-parent chain back to its available original. Bookmarks are stored locally; they require the job and source project records to remain available. They are not exported as standalone grading presets.

## Masks and reference time

The reference frame field uses an absolute, zero-based source-frame index. Blank means the actual processed range start, including any timing preroll. Use playhead converts the selected source layer's timeline time using stretch and interpreted frame rate. Inspect reference shows the exact frame and overlays a supplied image mask; a mismatched image size is rejected. Be aware that external image orientation/coordinates must already match the decoded source.

Click image points (on hosts supporting mouse events), or enter normalized point coordinates and Add point. Keep points are green; Remove points red. Mark all distinct subject colours: face, hands, clothing and hair, with background exclusions too. Build colour selection uses OpenCV GrabCut at up to 1280 pixels and produces a rough full-size binary hint; it does not recognize objects semantically. Small enclosed holes are filled, larger gaps remain. Review the overlay, add points or clear/rebuild. Generated hints automatically select Rough mask accuracy. Fine transparent edges are for CorridorKey to estimate, not a promised property of this colour selection. For difficult/same-colour subjects use authored masks instead.

Up to sixteen closed Add/Subtract layer masks can be sampled at the reference frame. Add masks are unioned; Remove masks exclude from that union regardless of order. With only Remove masks, the starting coverage is the whole image. Inversion, opacity, ordinary feather and expansion remain supported. Other modes and variable feather points are rejected. This is a snapshot; full animated-mask export is not implemented. An aligned external mask video remains the existing option for animation.

A chosen reference after the first processed frame requires an image/layer mask for that frame. The wrapper starts the unchanged official CLI forward from the reference and backward on a reversed preceding segment, then reorders the exported images, omitting the duplicate reference. Both passes load the model. The reversal is disk-backed with a conservative free-space check. Expect extra disk use and time; there is no arbitrary-frame flag added to upstream. Mask videos retain their source alignment and require an automatic/start reference. A reference outside a preview's short range is rejected rather than silently moved. Passing these workflow checks does not establish that reverse-time context produces equally good results for every shot; compare difficult motion at the reference boundary.

Reference sources, overlays and generated hints are retained under the local output `_review` folder, included in total storage usage. Detail images are bounded to the latest 64 files. Generated masks are preserved for retries, and are included when their completed job's media/cache are collected by the existing project packager. Do not delete a referenced hint while its jobs may be repeated. No images are uploaded.

## Finishing and GPU

Spill colour Green/Blue selects the channel for our additional finishing operation; Off preserves those colour channels. This does not change or retrain the external model. Opaque core fills only an eroded, already mostly opaque interior; Edge coverage independently scales soft alpha coverage. Defaults preserve the previous behavior. Both settings and spill colour work from cached exported images without another AI pass and are saved in named presets.

Automatic leaves the upstream memory/window choice intact. Manual windows map to the public `hann_chunk` CLI flag and a half-window stride; these are not the official plugin's independent look-ahead/look-behind control. Manual choices disable upstream automatic selection and can exhaust VRAM. Reduced memory mode remains separate. GPU refresh uses optional `nvidia-smi` and shows total process-independent usage for each detected GPU; missing telemetry never prevents use. It is not a forecast of model peak allocation or a guarantee that an out-of-memory job can spill to system RAM.

## Updating

Finish/cancel active jobs, close the previous local service, pull/extract this source and rerun setup_effectcraft.py. Relaunch with the shared starter. A 0.7 panel refuses a bridge without the new review capability; the launcher does not silently reuse a 0.6 bridge. Existing outputs and cached jobs remain readable with default values for new settings.

## In-place corrections (development update)

Edges → Update inserted result in place is enabled by default. The first result is inserted explicitly. Later cached corrections or reruns for an already inserted result automatically retarget that result's existing generated FootageItem when finished, without adding layers or project items. Selecting a linked cutout still processes its original input. Existing layer ID, name, position, animation, effects, masks, parenting, timing and original-audio handling stay intact because the layer itself is not rebuilt. The output media must retain its source-frame range/count/rate; the existing interpretation rate is preserved. The update has its own Undo group. Undo/redo reconciles record state against the actual file, and an undone correction can be reapplied without another AI run.

The captured target path is rechecked before an automatic update. Missing/locked/manually retargeted layers, changed processed ranges, or media shared by multiple layers are refused. Uncheck the option to explicitly insert another result layer using the previous behavior. Background failures leave the previously inserted media intact. A failed interpretation attempts to restore the previous generated file; files on disk are never overwritten. Completed render variants remain available for comparison. Updates apply only in the recorded original project; opening another project does not redirect them.
