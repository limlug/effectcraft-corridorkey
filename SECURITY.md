# Security and privacy

The bridge binds to 127.0.0.1 and requires a per-run access token. The token is stored in the private settings connection file; it is not embedded in JSX or committed to the repository. EffectCraft's control port also stays local. Do not expose these ports through port forwarding or a public reverse proxy.

The panel's file/network permission is needed for localhost communication and project/output access. The installer contacts upstream download services. Processing is local after setup; there is no add-on telemetry or upload endpoint.

Logs and project packages can contain media paths and private filenames. Review them before sharing. Never include connection files, model downloads or confidential footage in an issue.

Before a public release, enable GitHub private vulnerability reporting and use its “Report a vulnerability” link. While this repository is private/pre-release, contact its owner privately using an existing trusted channel. Do not post a suspected token exposure or exploit details in a public issue. No separate security email address has been invented for this project.
