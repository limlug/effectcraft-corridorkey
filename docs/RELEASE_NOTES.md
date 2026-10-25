# 0.6.0 — external-wrapper preview

Community EffectCraft panel for local CorridorKey background removal, with job queues, previews, cached edge/spill corrections, MOV transparency/EXR output and portable project collection.

The wrapper-owned code is MIT licensed. The installer fetches the unmodified official CorridorKey source and models separately at recorded revisions; their licenses and use conditions still apply. No models, runtime implementation, footage or compiled dependency binaries are bundled. The new repository starts with reviewed wrapper-only source; earlier private runtime-patch prototypes are excluded from its history.

All eleven EffectCraft 0.16 languages are included, plus Georgian for newer supporting hosts. Translations are provisional pending native-speaker review. Linux GPU smoke tests cover original-CLI inference and cached output correction. Windows is experimental; a fresh disposable-machine install and native Windows inference remain unverified. The model reloads for each AI job and temporary float EXR images require additional disk space. No GPU warm mode is offered.

See README.md for requirements and installation, docs/VALIDATION.md for exact test scope and docs/LICENSING.md for license boundaries. This is a prerelease, with no affiliation or endorsement by Corridor Digital or Storytold.
