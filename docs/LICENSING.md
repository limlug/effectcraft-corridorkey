# License scope

The wrapper-owned source, tests, translations and documentation in this repository are offered under the [MIT License](../LICENSE). This applies to the contributors' rights in those files. It does not relicense CorridorKey, its models, third-party dependencies, or the external license text reproduced in `LICENSES/CorridorKey.txt`.

## Separately obtained software

Setup downloads the official CorridorKey source and models from their original sources. The wrapper starts the unmodified `infer.py` command line in a separate process and processes its exported image files. No CorridorKey source implementation, patches, weights or vendored foundation-model implementation are included in the source release. See [architecture](WRAPPER_ARCHITECTURE.md), [recorded revisions](../UPSTREAM.md) and [external dependency notices](../THIRD_PARTY_NOTICES.md).

CorridorKey remains under the [Corridor Key Licence at the recorded revision](https://github.com/nikopueringer/CorridorKey2.0/blob/485f5e9ab759ead6138cc990776184b59d6ea971/LICENSE). Read the full terms before downloading or using it. In particular, its additional terms cover repackaging/redistribution (2a), paid inference (2b), freely accessible derivatives (2c), commercial software integration (2d), large organizations (3), attribution (4) and share-alike (5). Section 1b addresses ownership of produced images/video. The included reference copy is unchanged and is not the license of this wrapper.

MIT permission for the wrapper does not grant permission to sell or integrate the external tool contrary to its terms. Fetching it separately does not exempt its use from those conditions. Foundation models have additional publisher licenses. Neither project name nor the MIT notice implies official endorsement or grants trademark rights.

## Review and limits

A source/provenance review is recorded in [SOURCE_AUDIT.md](SOURCE_AUDIT.md). The reviewed tree contains our interface, orchestration and finishing implementation; comparisons found no matching 40-token Python windows against the pinned CorridorKey Python sources. This supports the chosen scope but cannot prove the absence of every protected contribution or determine legal independence.

The project was developed with AI assistance after inspecting upstream interfaces; no formal clean-room development is claimed. Earlier private prototypes patched the runtime. Those commits are excluded from the new publication repository, with the original private repository/history preserved separately. Changing Git history does not change rights in any code.

This technical review is not a binding legal opinion or rights-holder approval. No automatic exemption from the external license is asserted. A separate agreement is needed where the external license requires one; ask the rights holder or qualified counsel if a proposed commercial integration or derivative classification is uncertain. No one has contacted the rights holder on your behalf.
