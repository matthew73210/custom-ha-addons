# Upstream Tracking

This wrapper should detect upstream breakage, not hide it.

The goal is not to build compatibility shims that mask upstream changes. The goal is to know which upstream commits are known to work, test against upstream drift, and fail clearly when upstream breaks the wrapper contract.

## Upstream Projects

pyMC Repeater:

- Repository: `https://github.com/pyMC-dev/pyMC_Repeater.git`
- GitHub slug: `pyMC-dev/pyMC_Repeater`
- Build argument: `PYMC_REPEATER_REF`

pyMC Console dist:

- Repository: `https://github.com/dmduran12/pymc_console-dist.git`
- GitHub slug: `dmduran12/pymc_console-dist`
- Build argument: `PYMC_CONSOLE_REF`

Current pinned release defaults and known-good candidate refs are recorded in `compatibility/known-good-upstreams.json`.

## Current Pinned Release Defaults

Observed during wrapper review on 2026-05-20:

- pyMC Repeater: `a36cb6af44ab63247dd6d0f414afc6e53de18012`
- pyMC Console dist: `2d961cef1ae1a355eb06e34fba99788d9ffca44a`
- pyMC Console dist version: `0.9.329`

These SHAs are now the Dockerfile default refs for release/default builds. They remain known-good candidates rather than fully contract-tested refs until contract tests prove the wrapper routes, static assets, WebSocket forwarding, config persistence, direct access, and ingress-style access still satisfy the wrapper contract.

## Release Policy

Release builds should pin upstream commit SHAs:

- `PYMC_REPEATER_REF=<commit sha>`
- `PYMC_CONSOLE_REF=<commit sha>`

Release builds should not float on upstream `main` or another moving branch.

Development builds may override refs manually with Docker build args. Scheduled CI against upstream `main` is a later phase unless implemented separately, and those jobs should:

- Avoid publishing release images.
- Report failures as upstream drift unless wrapper code changed.
- Produce actionable failure text that says which upstream route, asset, schema, or WebSocket expectation changed.

## Build Metadata

Build logs should record:

- Requested upstream repository.
- Requested upstream ref.
- Resolved upstream SHA.
- Add-on version.
- Build architecture.
- pyMC Console dist version when available.

Current image labels include requested upstream repos/refs and a pointer to the build metadata file:

- `org.opencontainers.image.pymc_repeater.repo`
- `org.opencontainers.image.pymc_repeater.ref`
- `org.opencontainers.image.pymc_console.repo`
- `org.opencontainers.image.pymc_console.ref`
- `org.opencontainers.image.pymc_upstream_metadata`

Resolved SHAs and Console version are written to:

```text
/usr/share/pymc-repeater-console/upstream-build-info.json
```

Docker labels cannot be populated from values discovered inside a `RUN` step without passing those resolved values back into the build from outside Docker. The wrapper must not fake resolved-SHA labels. Use the metadata file as the source of truth for resolved upstream SHAs.

## Startup Metadata

Startup logs expose upstream version metadata from `/usr/share/pymc-repeater-console/upstream-build-info.json` without changing runtime behavior:

- pyMC Repeater requested ref and resolved SHA.
- pyMC Console dist requested ref and resolved SHA.
- pyMC Console dist version.

Diagnostics are acceptable only under a wrapper-owned namespace and only if they do not shadow upstream routes or change upstream behavior.

## Scheduled Upstream-Main CI

Scheduled CI should:

- Build against upstream `main`.
- Run contract tests.
- Compare the scheduled result with pinned-release results.
- Report upstream drift separately from wrapper failures.
- Avoid publishing release images.
- Avoid adding compatibility shims in response to failures.

## Contract Expectations

The wrapper may assume only documented upstream behavior. Contract tests should verify:

- Container starts.
- Console route `/` is reachable.
- Repeater route `/repeater/` is reachable.
- Static assets load under direct and ingress-style paths.
- WebSocket routes pass through.
- `/api/api/*` duplicate-prefix normalization is path-only and upstream-controlled.
- `/api/recent_packets` is reachable only if upstream provides it.
- `/api/bulk_packets` and `/api/filtered_packets` are proxied unchanged when upstream provides them.
- Packet schema comes from upstream.
- LBT fields are present only if upstream provides them.
- Config persistence works.
- Configurable ports work.
- Direct access and ingress-style access both route correctly.

Phase 2 adds the local contract test suite under:

```text
pymc-repeater-console/tests/contract
```

The suite can run against supplied direct/ingress URLs or start a Docker image when `PYMC_REPEATER_CONSOLE_IMAGE` is provided. Current-state route, config, and API-purity tests are normal tests after Phase 3 removed normal compat API routing.

## Failure Policy

When upstream changes break the wrapper contract:

- Do not insert fake/default fields.
- Do not synthesize analytics.
- Do not read SQLite to recreate upstream APIs.
- Do not rewrite upstream API JSON.
- Do not hide missing routes behind local substitutes.

Instead:

- Fail the contract test.
- Report the pinned upstream SHA and tested upstream SHA.
- Identify the changed route, asset, schema, or WebSocket expectation.
- Decide whether to update the wrapper boundary docs, update the pinned known-good refs, or request/follow an upstream change.
