# Agent Instructions

This is a Home Assistant Supervisor add-on repository.

## Repository Structure

- Each add-on must live in its own top-level folder.
- Each add-on must have its own `config.yaml`.
- Root repository metadata belongs in `repository.json`.
- Keep the repository clean and ready for real add-ons; avoid unrelated tooling or generated files unless they are needed.

## Reference Policy

- The AlexBelgium `hassio-addons` repository may be used only as a structural reference.
- Do not copy copyrighted files, text, branding, logos, icons, Dockerfiles, scripts, or add-on-specific files from AlexBelgium or any other repository.
- Write repository documentation, add-on metadata, Dockerfiles, and scripts specifically for this repository.

## Security

- Never commit credentials, secrets, tokens, private URLs, Home Assistant instance details, backup contents, or environment-specific configuration.
- Prefer placeholders and documented setup steps over hard-coded private values.
- Do not vendor third-party applications unless explicitly requested.
- Prefer wrapping upstream Docker images or reproducible source builds.
- Preserve upstream attribution and licensing.

## After Changes

After making repository or add-on changes, Codex and other AI coding agents should:

- Show the final file tree.
- Explain how Home Assistant Supervisor will detect the add-on repository and add-ons.
- List any manual follow-up steps for the maintainer.
