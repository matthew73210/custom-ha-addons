# Matthew Maxwell-Burton Home Assistant Add-ons

This repository is a Home Assistant Supervisor add-on repository. It is intended to hold custom Home Assistant add-ons, with each add-on stored in its own top-level folder.

## Add this repository to Home Assistant

In Home Assistant, open:

Settings -> Add-ons -> Add-on Store -> ⋮ -> Repositories

Then add:

```text
https://github.com/matthew73210/custom-ha-addons
```

Home Assistant Supervisor reads the repository metadata at the root of this repository and discovers add-ons from top-level folders that contain their own `config.yaml`.

## Current add-ons

- `placeholder-addon`: a non-production placeholder used only to validate and demonstrate the repository structure.
- `corescope`: CoreScope packaged as a Home Assistant Supervisor add-on for MeshCore packet analysis.
- `pymc-repeater`: pyMC Repeater packaged as a Home Assistant Supervisor add-on for MeshCore repeater deployments.

Remove or replace the placeholder before publishing a real add-on for users.

## Attribution

This repository's Home Assistant add-on structure was inspired by the excellent alexbelgium/hassio-addons repository. Thanks to AlexBelgium for maintaining such a useful reference for the Home Assistant community.

AlexBelgium does not maintain or endorse this repository.

## Codex

Codex was used to assist with repository setup, CoreScope packaging, and maintenance.
