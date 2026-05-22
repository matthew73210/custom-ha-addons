# Changelog

## 0.2.18-dev

- Removed Home Assistant runtime options that duplicated pyMC Repeater config.
- pyMC Repeater runtime config now comes only from `/config/pymc-repeater/config.yaml`.
- Existing persistent config files are preserved unchanged; a default config is created only when missing.
- Documented that radio config values must be edited directly in the persistent pyMC Repeater config file.
- No wrapper-side protocol shim, transport bridge, fake API, synthetic telemetry, or SQLite-backed modem compatibility path was added.

## 0.2.16-dev

- Bumped the app to a dev version for upstream `pymc_tcp` testing.
- Changed the pyMC_Repeater default ref to upstream `dev` because PR #240 merged `pymc_tcp` / `pymc_usb` Wi-Fi support there, but not yet into a tagged pyMC_Repeater release.
- Documented that tracking upstream `dev` is only for this dev app version and is not release-stable pinning.
- Pinned pyMC_core to commit `3987d3e8863bdf078bc9a9a7e3d29320028f49ee` and added build/runtime sanity checks for `TCPLoRaRadio`.
- Added temporary app-option support for TCP modem host, port, token, connect timeout, and LBT settings.
- Added default-config support for upstream `radio_type: pymc_tcp` and the `pymc_tcp:` config block.
- Ensured temporary `pymc_tcp_*` option keys were consumed by the wrapper and not written into the upstream config.
- No wrapper-side protocol shim, transport bridge, fake API, synthetic telemetry, or SQLite-backed modem compatibility path was added.

## 0.2.15

- Fixed LBT graph issues in signal lab

## 0.2.14

- Fixed Contacts live map rendering under Home Assistant ingress with a wrapper-owned same-origin map proxy.
- Restored Console Livetrace/graph history routes through wrapper-normalized packet and analytics APIs.
- Fixed original Repeater UI settings saves, including TX Delays, when the UI emits duplicate `/api/api/...` paths.
- Added build metadata and CI matrix entries for `aarch64`, `amd64`, `armhf`, `armv7`, and `i386`.
- Updated GitHub Actions to Node 24-capable action majors.
