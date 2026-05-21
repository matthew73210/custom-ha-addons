# Changelog

## 0.2.16-dev

- Bumped the app to a dev version for upstream `pymc_tcp` testing.
- Pinned pyMC_Repeater to upstream dev commit `8f3477ddd6fa879368dad99e18b258770bdeb380` because `pymc_tcp` / `pymc_usb` Wi-Fi support is not yet in a tagged pyMC_Repeater release or upstream `main`.
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
