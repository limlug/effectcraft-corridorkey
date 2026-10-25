# Changelog

## 0.6.0 — external-wrapper candidate

- Removes runtime patches and all CorridorKey Python imports from wrapper code.
- Invokes the original CLI as a separate program and supervises cancellation.
- Implements independent image finishing and MOV/EXR export from its output images.
- Retains cached corrections, but removes persistent GPU warm mode.
- Refuses edited runtime checkouts instead of modifying them.
- Does not claim a legal exemption or change the repository license.

## 0.5.0 — release candidate

- Adds complete catalogs for the twelve EffectCraft languages, automatic host-language selection, manual panel override and safe English fallback.
- Localizes dynamic status text, file picker titles and service-error summaries while preserving technical diagnostics.
- Preserves preset names and internal option IDs across language changes.
- Adds a standalone add-on repository layout with a separately downloaded, pinned CorridorKey runtime and a reviewed runtime patch.
- Adds a setup helper, English/German entry guides, platform notes, troubleshooting, model/license notices and CI validation.

## 0.4.0 — local preview

- Cached matte/despill corrections, in-panel playback and scrubbing, job retries, verified project packages and protected temporary-file cleanup.

## 0.3.0 — local preview

- Short previews, trimmed/work-area processing, matte finishing, mask hints, batching, persistent model reuse, presets and animation-preserving MOV/EXR insertion.
