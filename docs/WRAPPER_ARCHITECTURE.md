# Unmodified external CLI architecture (0.6 candidate)

The wrapper repository contains EffectCraft UI, orchestration and independently implemented image finishing. It does not contain model/runtime patches. Its Python modules do not import `corridorkey`, change its modules at runtime, copy its source, or call private runtime functions.

Flow:

1. The user installs the official CorridorKey source and weights from the original publishers. Setup pins the same recorded source/model revisions and refuses an existing checkout with modified tracked source or additional Python files.
2. The wrapper starts `python /external/CorridorKey2.0/infer.py` as a separate process using the original CLI options.
3. CorridorKey exports linear float EXR cutouts with zero despill. These are image outputs, stored locally as correction data, rather than a copied inference implementation.
4. The wrapper uses NumPy/OpenCV and ffmpeg for its own matte levels, morphological expansion/contraction, feathering, green-channel correction, MOV encoding and half/float EXR output.
5. The normal EffectCraft layer insertion, previews, retry, project package and storage features operate on those image/video outputs.

The external process is supervised as a process tree. Cancellation terminates that task, rather than injecting callbacks or modifying the original engine. Errors are preserved in diagnostics. An architecture test prohibits imports of CorridorKey modules in wrapper source. CI fetches the pinned original source without applying patches.

## Behavior changes

The original CLI loads the model for each AI job; persistent GPU model reuse is no longer offered. The corresponding controls are hidden. Cached finishing still avoids a new AI run. Image finishing is CPU-based, and each AI job first produces full-resolution float EXR files, even when correction data is not retained afterward. The space estimate therefore always includes temporary raw frames.

Old raw caches use the same linear BGRA image layout and can be read by the new finishing stage, but this branch does not claim pixel-identical export to the old patched engine. Review quality on your footage before replacing a production installation. The installed previous add-on is not automatically replaced by this branch.

## Legal boundary

This is a technical separation, not a legal finding. Using the external CorridorKey tool and models remains subject to their license. The reviewed wrapper-owned implementation is offered under MIT, with findings and limits recorded in SOURCE_AUDIT.md. No external implementation or models are relicensed, and no automatic exemption from external use conditions is claimed. Read LICENSING.md.
