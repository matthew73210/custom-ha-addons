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

Current default upstream refs and the latest observed resolved SHAs are recorded in `compatibility/known-good-upstreams.json`.

## Current Default Upstream Refs

Current default refs:

- pyMC Repeater: `main`
- pyMC_core: `main`
- pyMC Console dist: `main`

These moving refs are the Dockerfile defaults for review and release/default builds. The Docker build records the resolved commit SHA for each image, so published images remain inspectable even though the requested ref is `main`. On 2026-05-23, pyMC Repeater `main` included the config-file radio selection branches for `radio_type: pymc_tcp` and `radio_type: pymc_usb`.

## Release Policy

Release/default builds currently track upstream `main`:

- `PYMC_REPEATER_REF=main`
- `PYMC_CORE_REF=main`
- `PYMC_CONSOLE_REF=main`

Builds may override refs manually with Docker build args when review or recovery needs a branch, tag, or explicit commit SHA. CI also has an upstream-candidate path for testing alternate moving or feature refs without publishing release images.

Candidate refs are configurable:

- `PYMC_REPEATER_CANDIDATE_REF`
- `PYMC_CONSOLE_CANDIDATE_REF`

The default candidate ref may be `main`, but it is not required to be `main`. For future upstream work that lives on `dev` or a feature branch before reaching upstream `main`, set the candidate ref to that branch explicitly.

Scheduled and manual candidate jobs should:

- Avoid publishing release images.
- Report failures as upstream candidate drift or contract change unless wrapper code changed.
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

## CI Hardening

Phase 5 adds GitHub Actions guardrails around wrapper purity and upstream tracking.

Normal push and manual release/default workflow paths:

- Validate wrapper source and metadata before building.
- Run source-level contract tests.
- Build an amd64 default-ref image and run live contract tests against it.
- Publish multi-arch images from the configured default upstream refs.

Pull requests run validation and contract tests against the default-ref image, but do not publish images.

Validation checks include:

- YAML syntax for add-on/workflow metadata.
- JSON syntax for repository and known-good upstream metadata.
- Shell syntax for startup/s6 scripts.
- Python syntax for wrapper Python and contract tests.
- Absence of removed Home Assistant runtime options from `config.yaml`.
- Absence of normal-operation `console_compat_api.py` routing and `127.0.0.1:8090` proxying.
- Absence of removed minified frontend rewrite patterns.
- Dockerfile parse checks.

Scheduled and manual candidate jobs:

- Build an amd64 image with candidate upstream refs.
- Run the same contract tests.
- Never publish release images.
- Treat failure as upstream candidate drift or contract change, not as proof that default release builds are broken.

## Scheduled Upstream-Candidate CI

Scheduled CI should:

- Build against configured upstream candidate refs.
- Run contract tests.
- Compare the scheduled result with default-ref results.
- Report upstream drift separately from wrapper failures.
- Avoid publishing release images.
- Avoid adding compatibility shims in response to failures.

Configure candidate refs with repository variables:

```text
PYMC_REPEATER_CANDIDATE_REF=dev
PYMC_CONSOLE_CANDIDATE_REF=main
```

Manual workflow dispatch can override those values for a single run. For a future pyMC Repeater feature branch before it reaches upstream `main`, set `PYMC_REPEATER_CANDIDATE_REF` or the dispatch input to that branch name or commit SHA.

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

CI runs both source-level tests and live-container tests. Live-container tests run against amd64 images because they are smoke/contract tests for wrapper behavior; release publishing still builds every supported Home Assistant architecture from the default refs.

## pyMC USB Tracking

The default pyMC Repeater upstream `main` ref supports the pymc-usb-compatible modem family in two transport configurations:

- Local serial: `radio_type: pymc_usb`, `pymc_usb.port`, optional `pymc_usb.baudrate`.
- Remote TCP/IP: `radio_type: pymc_tcp`, `pymc_tcp.host`, `pymc_tcp.port`.

Upstream `main` does not add `host`, `ip`, `tcp`, `socket`, `url`, or serial-over-TCP keys under `pymc_usb`; TCP/IP remains the `pymc_tcp` transport. The runtime USB serial path or remote TCP/IP endpoint is configured in `/config/pymc-repeater/config.yaml`; it is not a Home Assistant add-on UI option. See `docs/PYMC_USB.md` for the exact config shape and wrapper/device boundary.

## Failure Policy

When upstream changes break the wrapper contract:

- Do not insert fake/default fields.
- Do not synthesize analytics.
- Do not read SQLite to recreate upstream APIs.
- Do not rewrite upstream API JSON.
- Do not hide missing routes behind local substitutes.

Instead:

- Fail the contract test.
- Report the default requested ref, resolved upstream SHA, and tested upstream SHA.
- Identify the changed route, asset, schema, or WebSocket expectation.
- Decide whether to update the wrapper boundary docs, adjust the default refs, or request/follow an upstream change.
