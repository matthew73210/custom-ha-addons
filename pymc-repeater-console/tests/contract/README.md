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

If the image needs real radio hardware or a site-specific config to stay running, prefer the running-container form above.

## Test Groups

- `test_container_smoke.py`: container starts, HTTP routes become reachable, startup does not crash immediately, and build metadata exists when Docker access is available.
- `test_routes.py`: Console, Repeater, helper scripts, duplicate `/api/api/*` normalization, and default proxy behavior.
- `test_ingress_paths.py`: simulated Home Assistant ingress headers, helper assets, redirect prefix behavior, and WebSocket upgrade path behavior.
- `test_upstream_api_contract.py`: upstream API boundary checks that verify normal traffic does not reach the quarantined compatibility API.
- `test_config_persistence.py`: persisted config preservation, one-time default creation, and removal of Home Assistant runtime option references from startup scripts.

## API Purity Tests

The API contract tests cover:

- packet APIs are not intercepted by `console_compat_api.py`;
- analytics APIs are not routed to local synthetic handlers;
- the compat API service is not started in normal operation;
- wrapper code cannot insert/default packet telemetry fields through the normal packet path;
- LBT fields, if present, come from upstream rather than wrapper SQLite/default logic;
- live analytics and bulk packet responses do not show wrapper-generated compatibility payloads.
