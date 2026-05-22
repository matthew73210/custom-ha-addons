# pyMC Repeater Console Contract Tests

These tests exercise the `pymc-repeater-console` wrapper contract. They are intended to detect upstream or wrapper breakage, not hide it with compatibility shims.

Phase 3 removes normal-operation routing to `console_compat_api.py`. The API purity tests are now normal passing expectations: packet APIs proxy upstream unchanged, and analytics are not synthesized by the wrapper.

## Requirements

- Python with `pytest`
- A built add-on image, or an already running add-on/container reachable over HTTP
- Docker CLI only when tests should start the container themselves

The tests do not require Home Assistant Supervisor. Ingress behavior is simulated with the direct ingress-compatible port and `X-Ingress-Path` headers.

## Environment Variables

- `PYMC_REPEATER_CONSOLE_IMAGE`: image tag to start with Docker when no base URL is provided.
- `PYMC_REPEATER_CONSOLE_BASE_URL`: direct wrapper URL, usually port `8000`.
- `PYMC_REPEATER_CONSOLE_INGRESS_BASE_URL`: ingress-compatible URL, usually port `8080`; defaults to `PYMC_REPEATER_CONSOLE_BASE_URL`.
- `PYMC_REPEATER_CONSOLE_SKIP_DOCKER`: when truthy, skip Docker startup if no base URL is provided.
- `PYMC_REPEATER_CONSOLE_TEST_TIMEOUT`: startup and request timeout in seconds; default is `60`.
- `PYMC_REPEATER_CONSOLE_CONFIG_DIR`: optional host config directory to mount as `/config` when tests start Docker.

CI candidate-drift jobs also use upstream ref variables outside the pytest process:

- `PYMC_REPEATER_CANDIDATE_REF`: pyMC Repeater candidate ref for non-release drift tests. Set to `main`, `dev`, a feature branch, or a commit SHA.
- `PYMC_CONSOLE_CANDIDATE_REF`: pyMC Console dist candidate ref for non-release drift tests.

## Run Against A Running Container

```bash
PYMC_REPEATER_CONSOLE_BASE_URL=http://127.0.0.1:8000 \
PYMC_REPEATER_CONSOLE_INGRESS_BASE_URL=http://127.0.0.1:8080 \
python3 -m pytest pymc-repeater-console/tests/contract
```

## Run By Starting An Image

```bash
PYMC_REPEATER_CONSOLE_IMAGE=pymc-repeater-console:local \
python3 -m pytest pymc-repeater-console/tests/contract
```

When tests start Docker themselves, they create or use a persisted config under `/config/pymc-repeater/config.yaml`. The default test fixture is `tests/contract/fixtures/ci-safe-config.yaml`, which uses upstream-accepted `radio_type: none` so CI does not require GPIO, USB, serial, or TCP radio hardware.

The production first-run default still uses `radio_type: sx1262`; the startup guard that fails when `/dev/gpiochip0` is unavailable is intentional runtime behavior. Contract tests distinguish that runtime guard from CI startup by checking that the guard remains present while CI fixtures do not use `radio_type: sx1262`.

## Test Groups

- `test_container_smoke.py`: container starts, HTTP routes become reachable, startup does not crash immediately, and build metadata exists when Docker access is available.
- `test_routes.py`: Console, Repeater, helper scripts, duplicate `/api/api/*` normalization, and default proxy behavior.
- `test_ingress_paths.py`: simulated Home Assistant ingress headers, helper assets, redirect prefix behavior, and WebSocket upgrade path behavior.
- `test_frontend_rewrites.py`: response-rewrite inventory checks for removed minified rewrites, remaining `sub_filter` rules, helper scripts, and Carto proxy behavior.
- `test_upstream_api_contract.py`: upstream API boundary checks that verify normal traffic does not reach the quarantined compatibility API.
- `test_config_persistence.py`: persisted config preservation, one-time default creation, and removal of Home Assistant runtime option references from startup scripts.
- `test_pymc_usb_docs.py`: documentation guardrails for local USB serial and remote TCP/IP pymc-usb-compatible transport examples.

## API Purity Tests

The API contract tests cover:

- packet APIs are not intercepted by `console_compat_api.py`;
- analytics APIs are not routed to local synthetic handlers;
- the compat API service is not started in normal operation;
- wrapper code cannot insert/default packet telemetry fields through the normal packet path;
- LBT fields, if present, come from upstream rather than wrapper SQLite/default logic;
- live analytics and bulk packet responses do not show wrapper-generated compatibility payloads.

## Frontend Rewrite Tests

The frontend rewrite tests are source-level guardrails. They assert that the Phase 4 removals stay removed, and that every remaining `sub_filter` rule is part of an explicit inventory. The remaining hardcoded minified rewrites are deferred exceptions for router basename support; changing upstream bundles should fail these tests clearly instead of silently changing wrapper behavior.

## CI Behavior

Phase 5 runs the suite in two ways:

- Source-level mode with `PYMC_REPEATER_CONSOLE_SKIP_DOCKER=1`. Live-container tests are skipped, while source checks still validate routing, config persistence, and rewrite inventories.
- Live-container mode against an amd64 image built from pinned upstream refs. These tests exercise startup, routes, ingress-style paths, WebSocket forwarding, and metadata checks.

Scheduled/manual upstream-candidate CI builds a non-published amd64 image with candidate refs, then runs the same live suite. Candidate failures mean upstream drift or a contract change in the tested candidate; they do not automatically mean the pinned release image is broken.
