# Changelog

## 0.2.28-dev

- Fixed pinned and candidate contract-test CI startup by using a CI-safe persisted config fixture with upstream-accepted `radio_type: none`.
- Kept the real runtime `sx1262` `/dev/gpiochip0` guard intact and added contract checks for it.
- Updated contract tests and workflow checks to prove CI fixtures do not boot with the hardware `sx1262` default.
- No runtime guard, production default config generation, ingress routing, compat API, or upstream source behavior changed.

## 0.2.27-dev

- Documented pymc-usb-compatible transport modes: local USB serial through `radio_type: pymc_usb` and remote TCP/IP through upstream `radio_type: pymc_tcp`.
- Clarified that TCP/IP mode uses `pymc_tcp.host` and `pymc_tcp.port`; `pymc_usb.baudrate` applies only to local serial mode.
- Added documentation contract checks so pymc_usb examples stay aligned with the upstream schema.
- Kept all pymc_usb connection settings in `/config/pymc-repeater/config.yaml`; no Home Assistant app options were added.
- No runtime, ingress, API, or upstream source behavior changed.

## 0.2.26-dev

- Added Phase 5 CI validation for wrapper source, add-on metadata, config-file-only settings, forbidden compat API routing, removed frontend rewrite patterns, and Dockerfile parsing.
- Added CI contract test jobs for source-level tests and live amd64 container tests against the pinned upstream image.
- Added scheduled/manual upstream-candidate drift testing with configurable candidate refs and no publishing.
- Kept release publishing on pinned upstream refs only.
- Documented pyMC USB runtime configuration in the persisted config file.
- No runtime, ingress, API, config authority, or upstream source behavior changed.

## 0.2.25-dev

- Kept pyMC Repeater runtime configuration file-only; no removed Home Assistant runtime options were restored.
- Corrected the one-time default persisted config template to use the intended EU radio defaults.
- Documented stale Supervisor option warnings as migration noise from old saved add-on options.
- Added contract coverage proving generated defaults are not reapplied over user-edited persisted config files.

## 0.2.24-dev

- Updated the pinned pyMC Repeater default ref to a buildable upstream commit that includes `radio_type: pymc_tcp` support.
- Kept the pyMC Console dist pin unchanged.
- Preserved the build guard so missing upstream `pymc_tcp` support still fails clearly.
- No upstream source files were patched.

## 0.2.23-dev

- Reduced fragile ingress response rewrites by removing one hardcoded Console history bundle rewrite and the unnecessary Carto tile JSON rewrite.
- Documented remaining ingress response rewrites and their wrapper-boundary classifications.
- Added contract tests for the frontend rewrite inventory.
- No upstream source files were changed.

## 0.2.22-dev

- Removed normal-operation routing to the local substitute Console compatibility API.
- Packet APIs now pass through the normal upstream proxy unchanged.
- Analytics APIs are no longer synthesized; upstream handles them or returns its native failure.
- Quarantined the old compatibility API by removing its s6 service from normal startup.
- Updated contract tests for Phase 3 API purity expectations.
- No upstream source files were changed.

## 0.2.21-dev

- Added the Phase 2 contract test suite for container smoke checks, route/proxy checks, ingress-style path checks, upstream API contract expectations, and config persistence.
- Marked current/future API wrapper-boundary expectations as `xfail` while the existing compatibility API remains in place.
- No runtime behavior, ingress routing, compat API behavior, or config authority changed.

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
