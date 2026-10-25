# Recorded upstream versions

This repository contains only the integration, own image processing and documentation. Setup obtains CorridorKey separately.

- CorridorKey code: https://github.com/nikopueringer/CorridorKey2.0/tree/485f5e9ab759ead6138cc990776184b59d6ea971
- CorridorKey weights: https://huggingface.co/nikopueringer/CorridorKey2.0/tree/cf44a8db3f024bb49fd59daa408848ccf05f7477
- C-RADIO revision: `c0457f5dc26ca145f954cd4fc5bb6114e5705ad8` from NVIDIA's original model repository.
- MoGe weights revision: `ca5f0e07ff01d3e5a364c1d954ed12ee1814b368` from the upstream downloader's recorded publisher.
- RVM: original publisher URL and checksum from that same pinned downloader.
- EffectCraft source inspected for language definitions: https://github.com/storytold/effectcraft/tree/991904888a20b7da72b2a4880b21c7d912154736
- Native EffectCraft binary exercised: 0.16.0, Linux x86_64. It offers eleven languages. The inspected source additionally offers Georgian, so the candidate includes its translation but gates it by the host's advertised language support.

`LICENSE` covers our wrapper-owned material under MIT. `LICENSES/CorridorKey.txt` is the unchanged external license from the recorded CorridorKey code revision, retained for reference. THIRD_PARTY_NOTICES.md describes separately installed dependencies. Vendored MoGe belongs to the downloaded runtime checkout, not this add-on repository. EffectCraft is neither bundled nor modified by the installer.

Dependency ranges are inherited from CorridorKey. PyTorch/torchvision and code/model revisions are pinned, while transitive Python packages can vary. See docs/INSTALL.md and docs/VALIDATION.md for the resulting limits on reproducibility and tested platforms.

The 0.6 candidate invokes the original `infer.py` CLI in a separate process. No runtime patch is applied or shipped.
