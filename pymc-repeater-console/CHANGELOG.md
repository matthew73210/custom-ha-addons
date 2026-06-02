# Changelog

## 0.3.2

- Added the read-only **Check pyMC Upstream Mergeability** scheduled/manual workflow for pyMC Repeater, pyMC Core, and pyMC Console dist.
- Fixed upstream-watch ref resolution to use `git ls-remote` without temporary Git clones, avoiding `.git` cleanup failures after successful resolution.
- Pinned release/default wrapper builds to the reviewed upstream SHAs recorded in compatibility metadata; watched upstream refs are tested temporarily and must be pinned manually after review.
- Kept upstream-watch CI non-publishing and non-mutating: it cannot publish images, push commits, rewrite refs, or patch upstream source.
- Audited bundled pyMC Console `0.9.329` API, auth, WebSocket, static, and Carto map paths against the transparent ingress proxy.
- Expanded failure-only Nginx diagnostics to cover all forwarded `/auth/*`, `/api/*`, and `/ws/*` paths so frontend/upstream route drift is visible without logging successful API traffic.
- Added startup LBT diagnostics for the selected upstream radio path, configured `pymc_usb` or `pymc_tcp` LBT settings, and the count of stored packets with `lbt_attempts > 0`.
- Documented that Console LBT charts intentionally remain empty until upstream records a busy-channel CAD backoff with `lbt_attempts > 0`.
- Added contract coverage for the audited Console route inventory and both Console WebSocket paths.
- Kept all application source unchanged; the update is wrapper diagnostics, tests, documentation, and metadata only.

## 0.3.1

- Verified current upstream `main` refs: pyMC Repeater `e17d1137ab2d2d5b86d03c99523272289b7688aa`, pyMC_core `330e32d57b9321afd63c38e634fa076a5049afee`, and pyMC Console dist `2d961cef1ae1a355eb06e34fba99788d9ffca44a` (`0.9.329`).
- Removed 32-bit add-on builds and metadata; only `amd64` and `aarch64` remain supported.
- Changed the backend launch path to the real persisted config file at `/config/pymc-repeater/config.yaml` and exports `PYMC_REPEATER_CONFIG` so upstream save paths do not depend on the `/etc/pymc_repeater` compatibility symlink.
- Fixed ingress helper injection for HTML responses so app UI save requests keep the Home Assistant ingress prefix instead of escaping to Home Assistant's own `/api`.
- Added startup preflight diagnostics for unsupported `radio_type`, missing or invalid `pymc_tcp` host/port, unreachable TCP modem endpoints, missing KISS or `pymc_usb` serial devices, non-character device paths, and serial permission failures.
- Fail fast before the backend is marked ready when the selected radio backend is unusable instead of letting upstream `pymc_tcp` deferred-connect mode appear healthy.

## 0.3.0

- Brings the app onto upstream `main` refs after the Phase 1-5 ingress/config work.
- Includes upstream pyMC Repeater `main` support for `radio_type: pymc_tcp` and `radio_type: pymc_usb`.
- Restored default pyMC Repeater, pyMC_core, and pyMC Console build refs to upstream `main` while preserving build-arg overrides.
- Updated CI and upstream-tracking metadata to build/test the default upstream `main` refs instead of release-pinned SHAs.
- Fixed default-ref and candidate contract-test CI startup by using a CI-safe persisted config fixture with upstream-accepted `radio_type: none`.
- Kept the real runtime `sx1262` `/dev/gpiochip0` guard intact and added contract checks for it.
- Updated contract tests and workflow checks to prove CI fixtures do not boot with the hardware `sx1262` default.
- No runtime guard, ingress routing, compat API, or upstream source behavior changed.

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

## 0.2.x config-file-only development update

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
