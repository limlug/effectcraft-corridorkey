# Source and publication review — 2026-10-25

## Scope and findings

Reviewed candidate: stock-CLI wrapper 0.6.0. The public-source candidate contains the EffectCraft panel and language catalogs, local bridge, job/storage/package/preview orchestration, independent image finishing, installer, tests and documentation. No footage, runtime downloads, Python environments, weights or runtime patches are included. Dependency source and model revisions are recorded in UPSTREAM.md.

- Compared 29 wrapper Python files with all 55 tracked Python files at CorridorKey commit `485f5e9ab759ead6138cc990776184b59d6ea971`, ignoring comments and whitespace: no identical sequences of 40 successive tokens were found.
- Inspected imports and the execution path: the worker invokes the original CLI via `runtime_cli.py` and `processes.py`. Finishing in `postprocess.py` uses exported images and NumPy/OpenCV, without importing CorridorKey modules. Standard numerical formulas and command-line argument names are interface/algorithm elements; no claim of exclusive authorship in those elements is made.
- Compared the three wrapper JavaScript/test sources against the inspected EffectCraft `prelude.js` and `scriptui.js`: no identical normalized blocks of at least four lines and 120 characters were found. This is not a full comparison against every EffectCraft file.
- Reviewed the packaging boundary: the installer fetches upstream separately and rejects modified existing runtime checkouts. Source releases exclude that checkout, dependencies and model files.
- Replaced the inherited repository-wide CorridorKey license with MIT for wrapper-owned material, retaining an unchanged, explicitly scoped external license reference and upstream attribution.
- Prepared a new repository with a fresh root commit. Earlier prototype history containing runtime patches is retained in a separate private archive and a verified local Git bundle, not imported into this repository.

## Limits

The scans detect exact matches above chosen thresholds, not paraphrased code, short copied snippets, contractual obligations, or all copyright issues. The implementation was developed with AI assistance after interface inspection; this is not a formal clean-room provenance certification. MIT covers only the contributors' rights. No rights-holder approval or legal opinion has been obtained. The external tool's use conditions remain applicable. See LICENSING.md.

## Validation and release claims

The existing Linux GPU smoke test exercised original-CLI inference, MOV export, cached corrections and half/float EXR. Full local checks comprise 40 Python bridge/wrapper/localization tests, 5 installer contracts and 42 Node panel checks. CI runs Linux/Windows contract tests and verifies the upstream checkout boundary. CI is not a native Windows inference test.

A fresh disposable-machine installation, native Windows inference, native-speaker translation review and Georgian rendering on a supporting host remain unverified. Release the candidate only with those limitations stated; do not label it as a universally validated stable build.
