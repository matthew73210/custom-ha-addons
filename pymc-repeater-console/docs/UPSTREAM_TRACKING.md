# Upstream Tracking

This wrapper should detect upstream breakage, not hide it.

The goal is not to build compatibility shims that mask upstream changes. The goal is to know which upstream commits are known to work, test against upstream drift, and fail clearly when upstream breaks the wrapper contract.

## Upstream Projects

OpenHop Repeater:

- Repository: `https://github.com/openhop-dev/openhop_repeater.git`
- GitHub slug: `openhop-dev/openhop_repeater`
- Build argument: `PYMC_REPEATER_REF`

OpenHop Core:

- Repository: `https://github.com/openhop-dev/openhop_core.git`
- GitHub slug: `openhop-dev/openhop_core`
- Build argument: `PYMC_CORE_REF`

pyMC Console dist:

- Repository: `https://github.com/dmduran12/pymc_console-dist.git`
- GitHub slug: `dmduran12/pymc_console-dist`
- Build argument: `PYMC_CONSOLE_REF`

Reviewed release refs are recorded in `compatibility/known-good-upstreams.json`. Watched refs and their reviewed comparison baselines are recorded in `compatibility/upstream-watch.json`.

## Current Default Upstream Refs

Current reviewed release pins:

- OpenHop Repeater: `60357f580876ceab5b3808a7ed00f81ae235c003`
- OpenHop Core source: `330e32d57b9321afd63c38e634fa076a5049afee`
- OpenHop Core runtime package: `openhop_core==1.1.1`
- pyMC Console dist: `2d961cef1ae1a355eb06e34fba99788d9ffca44a`

These fixed SHAs are the Dockerfile defaults and the publishing workflow defaults. On 2026-06-27, the reviewed OpenHop Repeater pin included the upstream rename plus config-file radio selection branches for `radio_type: pymc_tcp` and `radio_type: pymc_usb`.

## Release Policy

Release/default builds use reviewed commit SHAs:

- `PYMC_REPEATER_REF=60357f580876ceab5b3808a7ed00f81ae235c003`
- `PYMC_CORE_REF=330e32d57b9321afd63c38e634fa076a5049afee`
- `PYMC_CONSOLE_REF=2d961cef1ae1a355eb06e34fba99788d9ffca44a`

The authoritative release pin locations are:

- `pymc-repeater-console/Dockerfile`: default `PYMC_*_REF` build arguments for local/default builds.
- `.github/workflows/build-pymc-repeater-console.yml`: `PYMC_*_DEFAULT_REF` values used by release image builds.

`compatibility/upstream-watch.json` mirrors the reviewed baseline for drift comparison and reporting. `compatibility/known-good-upstreams.json` is the review record. The normal validation workflow checks that the Dockerfile, publishing workflow, and watch manifest remain aligned.

Build args may still override refs temporarily when review or recovery needs a branch, tag, or explicit commit SHA. Temporary override builds do not change release pins.

After a `MERGE READY` result and maintainer review, update all authoritative pin locations and both compatibility JSON files in one normal pull request. Do not have CI update refs or push a pin-update commit.

## Merge-Readiness Workflow

The **Check pyMC Upstream Mergeability** GitHub Actions workflow runs daily and supports `workflow_dispatch`. It reads `compatibility/upstream-watch.json`, resolves each pinned ref and watched ref with `git ls-remote`, and includes GitHub compare links. The resolve job does not create temporary Git clones or worktrees.

When drift exists, the workflow builds one temporary amd64 image with exact watched SHAs passed through Docker build arguments. It runs source-level wrapper-boundary and route-inventory tests, inspects the temporary image metadata, and runs the live container contract and smoke suite. The temporary image is local to the job.

The workflow has `contents: read` permission only. It never publishes images, pushes commits, edits refs, or modifies upstream source. Images are never published because the result is review evidence, not a release.

Run it manually from **Actions -> Check pyMC Upstream Mergeability -> Run workflow**.

Verdicts:

- `MERGE READY`: drift exists; temporary build, metadata inspection, wrapper-boundary tests, route inventory, ingress contracts, and live smoke tests all pass with no obvious pin/config mismatch.
- `NOT MERGE READY`: a required build or contract check fails, route inventory changes, wrapper boundaries break, or release-pin configuration is inconsistent.
- `NO UPSTREAM DRIFT`: every watched ref resolves to its reviewed pinned SHA.
- `CHECK INCONCLUSIVE`: refs cannot be resolved, Docker is unavailable, or the required test environment cannot finish.

`NOT MERGE READY` fails the workflow job. `NO UPSTREAM DRIFT` and `MERGE READY` succeed. `CHECK INCONCLUSIVE` is intentionally a successful run with a clear warning in the job summary so transient infrastructure issues remain distinguishable from an upstream contract break.

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

- OpenHop Repeater requested ref and resolved SHA.
- pyMC Console dist requested ref and resolved SHA.
- pyMC Console dist version.

Diagnostics are acceptable only under a wrapper-owned namespace and only if they do not shadow upstream routes or change upstream behavior.

## CI Hardening

Phase 5 adds GitHub Actions guardrails around wrapper purity and upstream tracking.

Normal push and manual release/default workflow paths:

- Validate wrapper source and metadata before building.
- Run source-level contract tests.
- Build an amd64 default-ref image and run live contract tests against it.
- Publish `amd64` and `aarch64` images from the configured default upstream refs.

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

Scheduled and manual upstream-watch jobs:

- Compare watched branches with reviewed release pins.
- Build an amd64 image with exact watched SHAs only when drift exists.
- Run the same contract tests.
- Never publish release images.
- Treat failure as upstream drift or contract change, not as proof that pinned release builds are broken.

## Scheduled Upstream-Watch CI

Scheduled CI should:

- Read pinned and watched refs from `compatibility/upstream-watch.json`.
- Compare pinned and watched SHAs before building.
- Build against exact watched SHAs only when drift exists.
- Run contract tests.
- Report upstream drift separately from wrapper failures.
- Avoid publishing release images.
- Avoid adding compatibility shims in response to failures.

The watched refs are manifest data, usually `main` or `dev`:

```text
PYMC_REPEATER_REF=main
PYMC_CORE_REF=main
PYMC_CONSOLE_REF=main
```

Changing a watched ref is a reviewed repository edit. It affects tracking/reporting only; it does not update release pins.

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

CI runs both source-level tests and live-container tests. Live-container tests run against amd64 images because they are smoke/contract tests for wrapper behavior; release publishing builds the supported 64-bit Home Assistant architectures, `amd64` and `aarch64`, from the default refs.

## pyMC USB Tracking

The reviewed OpenHop Repeater release pin supports the pymc-usb-compatible modem family in two transport configurations:

- Local serial: `radio_type: pymc_usb`, `pymc_usb.port`, optional `pymc_usb.baudrate`.
- Remote TCP/IP: `radio_type: pymc_tcp`, `pymc_tcp.host`, `pymc_tcp.port`.

The reviewed release pin does not add `host`, `ip`, `tcp`, `socket`, `url`, or serial-over-TCP keys under `pymc_usb`; TCP/IP remains the `pymc_tcp` transport. The runtime USB serial path or remote TCP/IP endpoint is configured in `/config/pymc-repeater/config.yaml`; it is not a Home Assistant add-on UI option. See `docs/PYMC_USB.md` for the exact config shape and wrapper/device boundary.

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
