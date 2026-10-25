# 0.7.0 prerelease release checklist

## Prepared

- [x] Eleven released EffectCraft catalogs plus Georgian for supporting newer hosts; translations provisional pending native-speaker review
- [x] Locale selection, placeholders and user-data preservation covered by automated tests
- [x] Readable Georgian fallback on EffectCraft 0.16
- [x] Separate official-runtime download with pinned code/model revisions
- [x] Original CLI process boundary; no runtime patches or CorridorKey module imports
- [x] Installation guides, troubleshooting and explicit platform limits
- [x] MIT only for wrapper-owned material; unchanged external license reference and accurate dependency notices
- [x] Source review recorded with methodology and limits in docs/SOURCE_AUDIT.md
- [x] New publication history excludes prototype patch commits; previous history preserved privately
- [x] Source-only archive excludes footage, credentials, runtime, environments and weights
- [x] Linux/Windows CI definitions and installer/CLI boundary contracts

## Before publishing a prerelease

- [x] Linux/Windows and image-workflow CI configured; publishing requires a successful run for the release commit
- [x] Final source archive, checksum and release notes reviewed
- [x] User authorized deploying the tested new version to GitHub; preserve current repository visibility

## Remaining validation (disclosed prerelease limitations)

- [ ] Full downloader/installation on a disposable Linux machine
- [ ] Real Windows installation, inference and host import/Undo (Windows experimental)
- [ ] Native-speaker translation review (catalogs provisional)
- [ ] Georgian rendering on a supporting host
- [ ] Longer-clip quality/performance tests and more GPUs

Existing Linux GPU smoke tests do not complete the remaining checks. No automatic publishing workflow is enabled. Do not upload private QA footage, logs, connection files, environments, runtime downloads or weights. MIT does not grant rights in external code/models or waive their use conditions. See docs/LICENSING.md.
