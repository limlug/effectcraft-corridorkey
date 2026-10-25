# Validation scope

## Automated contracts

The release candidate is checked with the bridge/localization Python suite, the installer contract suite, and 42 Node panel workflow checks. The panel suite exercises all twelve catalogs; keys, values, placeholder sets and UTF-8 integrity are checked separately. Tests also cover automatic language choice, system-locale aliases, manual override persistence, user names containing multiple scripts and recovery from localized service errors.

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

The current candidate must retain prerelease/experimental labels. Do not present remaining checks as completed or advertise every OS as supported.

## 0.6 external CLI verification

The new architecture has 40 bridge/localization/wrapper Python tests, 42 Node panel tests and 5 installer contracts. Numerical finishing tests use NumPy/OpenCV without importing CorridorKey. A real GPU test used an unmodified checkout at the recorded commit and local model-file links. Original CLI inference produced two test frames; the wrapper exported MOV and applied cached corrections plus half/float EXR without another AI run. The upstream tracked source remained unchanged. This does not establish complete Windows/native-host or long-clip quality validation for the new architecture.
