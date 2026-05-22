# Changelog

## 0.2.18-dev

- Added Home Assistant options for `sync_word` and `preamble_length`.
- For `radio_type: pymc_tcp`, `sync_word: 0` and `preamble_length: 0` now generate the upstream pymc_usb TCP modem defaults `sync_word: 18` and `preamble_length: 16` instead of forcing the EU preset values.
- Documented that pyMC_Repeater sends the generated radio config to the TCP modem during startup, so these values must match the modem and mesh.
- No wrapper-side protocol shim, transport bridge, fake API, synthetic telemetry, or SQLite-backed modem compatibility path was added.

## 0.2.16-dev

- Bumped the app to a dev version for upstream `pymc_tcp` testing.
- Changed the pyMC_Repeater default ref to upstream `dev` because PR #240 merged `pymc_tcp` / `pymc_usb` Wi-Fi support there, but not yet into a tagged pyMC_Repeater release.
- Documented that tracking upstream `dev` is only for this dev app version and is not release-stable pinning.
- Pinned pyMC_core to commit `3987d3e8863bdf078bc9a9a7e3d29320028f49ee` and added build/runtime sanity checks for `TCPLoRaRadio`.
- Added Home Assistant options for TCP modem host, port, token, connect timeout, and LBT settings.
- Added wrapper config generation for upstream `radio_type: pymc_tcp` and the `pymc_tcp:` config block.
- Ensured Home Assistant-only `pymc_tcp_*` option keys are consumed by the wrapper and not written into the upstream config.
- No wrapper-side protocol shim, transport bridge, fake API, synthetic telemetry, or SQLite-backed modem compatibility path was added.

## 0.2.15

- Fixed LBT graph issues in signal lab

## 0.2.14

- Fixed Contacts live map rendering under Home Assistant ingress with a wrapper-owned same-origin map proxy.
- Restored Console Livetrace/graph history routes through wrapper-normalized packet and analytics APIs.
- Fixed original Repeater UI settings saves, including TX Delays, when the UI emits duplicate `/api/api/...` paths.
- Added build metadata and CI matrix entries for `aarch64`, `amd64`, `armhf`, `armv7`, and `i386`.
- Updated GitHub Actions to Node 24-capable action majors.
