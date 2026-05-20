# Wrapper Boundary

`pymc-repeater-console` is a Home Assistant wrapper around upstream pyMC Repeater and pyMC Console. It must not become a fork.

The wrapper may adapt packaging, process supervision, persistent paths, and Home Assistant ingress transport. It must not replace upstream behavior with local compatibility shims.

## Current Boundary Status

Build/filesystem status:

- Upstream source is cloned during the Docker build.
- Upstream source is not patched on disk.
- Upstream Console dist files are copied into the image as build artifacts.
- No upstream files are vendored in this repository.

Runtime/API status:

- Transparent reverse proxying and ingress base-path handling are wrapper behavior.
- `console_compat_api.py` is outside the wrapper boundary when it serves upstream-looking API responses.
- Any locally generated response under upstream API paths must be removed or moved to a wrapper-owned diagnostic namespace.

## Allowed Wrapper Behavior

- `repository.json` and Home Assistant add-on `config.yaml`.
- Docker build glue that installs upstream from documented repos and refs.
- s6 supervision and startup/shutdown scripts.
- Config generation from Home Assistant options when the result is a normal upstream config file.
- Persistence and path mapping for `/config`, `/etc/pymc_repeater`, and `/var/lib/pymc_repeater`.
- Ingress base-path and URL prefix handling.
- Reverse proxy headers such as `Host`, `X-Forwarded-*`, and `X-Ingress-Path`.
- Cookie path and redirect path adaptation for ingress.
- WebSocket upgrade forwarding.
- Diagnostics that are clearly wrapper-owned and do not alter upstream behavior.

## Forbidden Wrapper Behavior

- Local substitute APIs for upstream routes.
- JSON field insertion, renaming, deletion, or defaulting in upstream API responses.
- Synthetic telemetry or analytics values.
- SQLite reads used to recreate upstream API responses.
- Response body rewriting for upstream API JSON.
- Frontend bundle edits on disk.
- Hardcoded assumptions about minified upstream frontend internals unless documented as a temporary exception.
- Auth/JWT/API-token behavior that differs from upstream.

## Classification

OK:

- Transparent path/base-url/header/WebSocket proxy adaptations for Home Assistant ingress.
- Path-only normalization that forwards to upstream and passes upstream response content unchanged.

Suspicious:

- Frontend response rewriting.
- Minified bundle string rewrites.
- Third-party JSON URL rewriting for map assets.

Violation:

- Locally generated upstream-looking API responses.
- SQLite-backed API recreation.
- Synthetic analytics.
- Fake/default telemetry fields.
- Auth checks that are weaker or different than upstream.

## Exception Rule

An exception is allowed only when all of these are true:

- It is unavoidable for Home Assistant packaging or ingress.
- It is isolated in wrapper-owned infrastructure.
- It is documented in `docs/INGRESS_PROXYING.md` or `docs/WRAPPER_ROUTES.md`.
- Contract tests prove the exception does not hide upstream contract changes.
- Failure is clear when upstream changes break the wrapper assumption.

