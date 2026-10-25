# Interface languages and translation QA

The 0.6.0 candidate has 206 catalog entries in each of twelve languages: eleven in released EffectCraft 0.16, plus Georgian in the current upstream source.

| Code | Language |
| --- | --- |
| en | English |
| cs | Čeština |
| de | Deutsch |
| es | Español |
| fr | Français |
| pt-br | Português (Brasil) |
| ru | Русский |
| uk | Українська |
| ka | ქართული |
| ja | 日本語 |
| zh-hans | 简体中文 |
| zh-hant | 繁體中文 |

The host language list and preference key were checked against the [official preference definitions](https://github.com/storytold/effectcraft/blob/main/crates/engine/src/prefs.rs) and [language implementation](https://github.com/storytold/effectcraft/blob/main/crates/ui-egui/src/i18n.rs). The exact inspected EffectCraft revision is recorded in `UPSTREAM.md`.

## Selection and coverage

The panel checks `prefs.pages` for the host language list. If the host does not offer Georgian, that option is hidden and an existing Georgian preference safely falls back to English with a readable notice. No unreadable Georgian labels are shown on that host.

The panel reads `prefs.get` with `general.language`. For Match System it uses the locale in the bridge's private connection file. Explicit Service → Language overrides only the panel. It never changes EffectCraft's preference. Unsupported locales fall back to English. Portuguese regional variants use Brazilian Portuguese; Chinese Taiwan/Hong Kong/Macao/Hant tags select Traditional Chinese. Reopen the panel to apply changes.

EffectCraft 0.16 exposes fixed `en_US` stubs for `app.isoLanguage` and `$.locale`, so those are not used as the sole source of truth.

Translated text includes buttons, help text, tabs, job states, validation, main progress/failure messages, storage estimates, file-operation status and the add-on's file-dialog titles. Native operating-system dialog buttons follow the OS. Technical logs, native error details, filenames, model identifiers, preset names and user content remain verbatim. Unknown service errors show a translated summary and keep the original diagnostic in Details.

## Catalog structure

`integrations/effectcraft/locales/*.json` use readable English keys and localized values. `i18n.js` handles normalization and named placeholders; `build_panel.py` embeds all catalogs in a single ASCII-escaped JSX payload, so installation needs only one panel file. Edit the source JSON, then reinstall; do not edit the generated installed JSX.

Preserve every `{name}` placeholder exactly once for each occurrence in the source key. Reorder placeholders as needed for natural grammar. Preserve line breaks where they improve readability. Do not translate command IDs, option enums, paths or saved preset identities.

## Validation scope

Automated checks verify identical key sets, nonempty values, placeholder parity and Unicode integrity. Panel tests exercise all languages through connection, preset storage, submission, insertion and validation. Native EffectCraft checks open every supported host language and inspect actual controls. Representative CJK and German renderings are checked visually; Georgian uses the explicit fallback on 0.16 and still needs a visual check on a supporting host. This verifies integration and rendering, not native-speaker proofreading. Community review of wording remains welcome before a stable public release.

When EffectCraft adds a language, add its code to `build_panel.py` and `i18n.js`, create its complete JSON catalog, extend this table, then run both test suites and a native visual check.
