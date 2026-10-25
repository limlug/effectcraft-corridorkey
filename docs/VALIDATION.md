# Validation scope

## Automated contracts

The release candidate is checked with the bridge/localization Python suite, the installer contract suite, and 52 Node panel workflow checks. The panel suite exercises all twelve catalogs; keys, values, placeholder sets and UTF-8 integrity are checked separately. Tests also cover automatic language choice, system-locale aliases, manual override persistence, user names containing multiple scripts and recovery from localized service errors.

GPU-independent tests cover queue/retry/correction metadata, manifest recovery, cancellation, portable-package path containment, verified copying and cleanup protection. Numerical matte/mask/writer tests require the runtime dependencies and are skipped by the standard-library-only CI job.

CI configuration is supplied for Linux and Windows on Python 3.11 and 3.12. A separate CI job tests the CLI process boundary and fetches the unchanged upstream source. Supplying this configuration is not evidence that an unrun workflow passed.

## Native and GPU evidence

The earlier 0.4 functionality was tested with real CUDA inference on Linux, an RTX 3080 Laptop GPU (16 GB), Python 3.12 and EffectCraft 0.16.0. Checks included identity/changed cached corrections, MOV and half/float EXR exports, in-panel playback, insertion/Undo, moved portable projects and protected cleanup. Short portions of a local green-screen clip with hair and lace sleeves were reviewed. These samples are private and are not included in the repository. No ground-truth quantitative matting benchmark is claimed.

For 0.5, the eleven interface languages accepted by released EffectCraft 0.16 are checked in an isolated native profile with automatic host-language selection. The twelfth catalog, Georgian, is prepared for the current upstream source. On the released host, a readable English fallback is tested because that host lacks Georgian language/font support. Project contents, dirty state and Undo history must remain unchanged by language switching.

## Remaining release checks

- Keep MIT scope and external-use conditions explicit; obtain an agreement for uses where the external license requires it.
- A clean installation using the full downloader in a disposable Linux environment; existing weights must not conceal missing download/setup steps.
- End-to-end Windows installation, inference, file dialogs and import/Undo on a real Windows machine.
- Native-speaker review of translated terminology and longer help text.
- Georgian rendering in an EffectCraft build that actually supports it.
- Performance and VRAM characterization on additional GPUs and footage.

Keep Windows experimental and translations provisional. Version 0.8 is a minor release of the tested Linux workflow; the remaining installation, platform and review limits still apply. Do not advertise every OS or production scenario as validated.

## 0.6 external CLI verification

The new architecture has 40 bridge/localization/wrapper Python tests, 42 Node panel tests and 5 installer contracts. Numerical finishing tests use NumPy/OpenCV without importing CorridorKey. A real GPU test used an unmodified checkout at the recorded commit and local model-file links. Original CLI inference produced two test frames; the wrapper exported MOV and applied cached corrections plus half/float EXR without another AI run. The upstream tracked source remained unchanged. This does not establish complete Windows/native-host or long-clip quality validation for the new architecture.

## 0.7 quality-of-life verification

The expanded suite includes 49 bridge/localization/wrapper/image tests, 46 Node panel checks and 5 installer contracts (100 checks total). A numerical CI job installs the tested NumPy/OpenCV versions and FFmpeg, so synthetic selection, mask combination, colour/core/edge behavior, exact-frame inspection and bidirectional ordering run without skipped image dependencies. A standalone external-program fixture decodes numbered real frames and proves the forward/reversed merge preserves order and omits the duplicate reference.

On Linux, a three-frame 1280×720 sample from the existing project clip exercised a middle reference, both original-CLI passes, cached finishing, MOV and half/float EXR. The source checkout stayed unchanged. Native EffectCraft 0.16 checks exercised detail review, A/B/original, reference inspection and point selection, plus GPU status, with the test project unchanged. Colour selection was visually checked and revised after a poor foreground initialization was found; authored points for separate subject colours are required. These short workflow samples are not a quantitative quality benchmark or proof of long-shot temporal quality.

## 0.8 in-place verification

106 local checks passed: 49 Python bridge/wrapper/localization/image tests, 52 Node panel checks and 5 installer contracts. The six added panel checks cover automatic replacement without extra layers, Undo/reapply, opting out, shared/locked result protection, restoring the previous media after interpretation failure, and routing a selected cutout back to the original input.

In real EffectCraft 0.16 on Linux, cached corrections updated a three-frame test cutout without changing layer ID, layer/project-item counts, name, comment, source timing or animated position keys. Undo restored the prior generated file; reapplying and repeating the correction preserved the same layer. The test used an isolated profile/project and existing correction data, with no fresh model inference needed. The feature was installed into the user's running panel without restarting its service or changing the project. This does not extend the earlier GPU evidence to new hardware or claim native Windows validation.
