# Matthew Maxwell-Burton Home Assistant Apps

This repository is a Home Assistant app repository. It contains custom Home Assistant apps, formerly known as add-ons, with each app stored in its own top-level folder.

## Add this repository to Home Assistant

In Home Assistant, open:

Settings -> Apps -> App store

Then use the repository option or store icon to add this app repository URL:

```text
https://github.com/matthew73210/custom-ha-addons
```

Home Assistant Supervisor reads the repository metadata at the root of this repository and discovers apps from top-level folders that contain their own `config.yaml`.

## Current Apps

- `placeholder-addon`: a non-production placeholder used only to validate and demonstrate the repository structure.
- `corescope`: CoreScope packaged as a Home Assistant app for MeshCore packet analysis.
- `pymc-repeater`: pyMC Repeater packaged as a Home Assistant app for MeshCore repeater deployments.
- `pymc-repeater-console`: pyMC Repeater packaged with the pyMC Console dashboard as the default UI.

Remove or replace the placeholder before publishing a real app for users.

## Attribution And Maintainer Note

This repository's Home Assistant app structure was inspired by the excellent alexbelgium/hassio-addons repository. Thanks to AlexBelgium for maintaining such a useful structural reference for the Home Assistant community.

AlexBelgium does not maintain or endorse this repository.

This repository is maintained by an electrical engineer, not a professional software developer. I am learning the Home Assistant app ecosystem as I go, so some development conventions, packaging details, or repository structure choices may not be perfect.

If issues arise, I will do my best to investigate and fix them, but please be patient and include clear logs, reproduction steps, and your Home Assistant version when opening an issue.

Parts of this repository's documentation and wrapper code were drafted or reviewed with AI assistance. Final changes, testing, and maintenance remain my responsibility.
