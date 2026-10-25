# External software and model notices

Our wrapper is MIT licensed; see LICENSE and docs/LICENSING.md. The source archive does not bundle the programs, libraries or models listed below. Installing them separately preserves their own licensing obligations.

| Component | Publisher / source | License / notice |
| --- | --- | --- |
| CorridorKey 2.0 code and primary weights | [CorridorKey](https://github.com/nikopueringer/CorridorKey2.0), Corridor Digital and contributors | [Corridor Key Licence](LICENSES/CorridorKey.txt), a custom license based on CC BY-NC-SA 4.0 with additional terms; not MIT |
| C-RADIOv4-SO400M | [NVIDIA](https://huggingface.co/nvidia/C-RADIOv4-SO400M) | NVIDIA Open Model License; consult the publisher's model card and license |
| MoGe-2 ViT-B | [Microsoft MoGe](https://github.com/microsoft/MoGe), [weights](https://huggingface.co/Ruicheng/moge-2-vitb-normal) | MIT; its DINOv2 dependency has Apache-2.0 notices in the separately downloaded runtime |
| RVM / Recurrent Video MAE | [Google DeepMind representations4d](https://github.com/google-deepmind/representations4d) | Apache-2.0 code; CC-BY-4.0 weights, as recorded by CorridorKey |
| NumPy | [NumPy](https://github.com/numpy/numpy/blob/main/LICENSE.txt) | BSD-3-Clause; installed package includes its notices |
| OpenCV | [OpenCV](https://github.com/opencv/opencv/blob/4.x/LICENSE) | Apache-2.0 for current 4.x code; packaged components retain additional notices |
| FFmpeg / ffprobe | [FFmpeg legal information](https://ffmpeg.org/legal.html) | LGPL-2.1-or-later or GPL depending on build; separately installed executables, no binaries bundled |
| EffectCraft | [Storytold / EffectCraft](https://github.com/storytold/effectcraft) | Separately installed host; consult its repository and distribution terms; no host source or binaries bundled |

CorridorKey 2.0 was created by Zachary Harris with Niko Pueringer and Corridor Digital. No affiliation or endorsement is implied. The upstream runtime's [THIRD_PARTY_NOTICES.md](https://github.com/nikopueringer/CorridorKey2.0/blob/485f5e9ab759ead6138cc990776184b59d6ea971/THIRD_PARTY_NOTICES.md) documents its own vendored code and foundation models. Those vendored directories belong to that external checkout, not this wrapper repository.

The installer obtains further runtime dependencies, including PyTorch, from upstream requirements. Their installed license/notices remain authoritative; this table is not a complete transitive dependency bill of materials. Redistributing an environment, executable bundle or model collection requires a separate review and is outside this source-only release.
