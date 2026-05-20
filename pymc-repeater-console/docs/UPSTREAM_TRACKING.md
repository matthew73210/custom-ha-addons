# Upstream Tracking

This wrapper should detect upstream breakage, not hide it.

## Upstream Projects

pyMC Repeater:

- Repository: `https://github.com/pyMC-dev/pyMC_Repeater.git`
- Current build argument: `PYMC_REPEATER_REF`
- Current release risk: default value is `main`

pyMC Console dist:

- Repository: `https://github.com/dmduran12/pymc_console-dist.git`
- Current build argument: `PYMC_CONSOLE_REF`
- Current release risk: default value is `main`

## Observed Upstream Refs

Observed on 2026-05-20:

- pyMC Repeater `main`: `a36cb6af44ab63247dd6d0f414afc6e53de18012`
- pyMC Console dist `main`: `2d961cef1ae1a355eb06e34fba99788d9ffca44a`
- pyMC Console dist version: `0.9.329`

These observed refs are recorded in `compatibility/known-good-upstreams.json`. They are not a release pin until CI and Docker build args use the SHA directly.

## Release Policy

Release builds must use pinned commit SHAs:

- `PYMC_REPEATER_REF=<commit sha>`
- `PYMC_CONSOLE_REF=<commit sha>`

Development and scheduled CI may test upstream `main`, but those jobs must not publish release images.

## Build Metadata

Build logs should include:

- Requested upstream repository.
- Requested upstream ref.
- Resolved upstream SHA.
- Add-on version.
- Build architecture.

Image labels should include:

- `org.opencontainers.image.pymc_repeater.repo`
- `org.opencontainers.image.pymc_repeater.ref`
- `org.opencontainers.image.pymc_repeater.revision`
- `org.opencontainers.image.pymc_console.repo`
- `org.opencontainers.image.pymc_console.ref`
- `org.opencontainers.image.pymc_console.revision`

## Startup Metadata

Startup logs should include upstream version metadata without changing runtime behavior:

- pyMC Repeater package version if available.
- pyMC Repeater resolved SHA if recorded at build time.
- pyMC Console dist version if available.
- pyMC Console resolved SHA if recorded at build time.

## Scheduled Upstream-Main CI

Scheduled CI should:

- Build against upstream `main`.
- Run contract tests.
- Report upstream drift separately from wrapper failures.
- Avoid publishing release images.
- Avoid adding compatibility shims in response to failures.

## Contract Expectations

The wrapper may assume only documented upstream behavior. Tests should verify:

- Expected upstream routes exist when the wrapper proxies them.
- Packet schema fields come from upstream.
- LBT fields appear only when upstream provides them.
- Static frontend assets remain loadable through ingress path adaptation.
- WebSocket routes still pass through.
- Missing upstream APIs fail clearly instead of being faked.

