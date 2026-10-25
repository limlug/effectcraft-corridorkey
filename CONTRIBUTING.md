# Contributing

This is an independent community integration. Read LICENSE and docs/LICENSING.md before redistributing changes. Contributions to wrapper-owned files are submitted under MIT. Do not copy external implementation code or assume MIT overrides external runtime/model conditions.

Use Python 3.11/3.12 and Node.js 20 or newer for development. Most bridge and panel tests use fake workers and need no weights, GPU, network or open EffectCraft instance:

```bash
python3 -m unittest discover -s integrations/effectcraft -p 'test_*.py' -v
node integrations/effectcraft/test_panel.cjs
```

Use the installer-created venv for numerical tests. Keep GPU/native tests separate from user projects, and explicitly state which tests you ran. Do not claim Windows or another host version is validated from Linux tests alone.

Translations live in `integrations/effectcraft/locales`; see docs/LANGUAGES.md. Keep API IDs, preset identities and user filenames independent of labels. Run the catalog tests after every translation change.

This wrapper must not patch or import the external runtime. Keep communication at the original CLI boundary, and implement image finishing from exported files in wrapper-owned modules. Update the recorded source version only after checking CLI compatibility. Never commit downloaded runtimes, weights, private samples or connection files. Run test_wrapper.py to enforce the boundary.

Describe a reproducible problem, its user-visible improvement and relevant verification in changes. Avoid screenshots or logs containing private paths or footage. Report security issues through the private process in SECURITY.md.
