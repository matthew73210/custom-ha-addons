# Wrapper Boundary

`pymc-repeater-console` is a Home Assistant wrapper around upstream OpenHop Repeater, formerly pyMC Repeater, and pyMC Console. The prime directive is simple: this app must remain a wrapper, not a fork.

The wrapper may adapt packaging, persistence, process supervision, and Home Assistant ingress transport. It must not modify, patch, monkey-patch, replace, or reimplement upstream OpenHop Repeater or pyMC Console behavior unless an exception is unavoidable for Home Assistant packaging, clearly documented, and isolated as wrapper infrastructure.

## Current Boundary Status

Build/filesystem status:

- Upstream OpenHop Repeater and pyMC Console are fetched during the Docker build.
- No upstream Python source, frontend bundle, API module, static asset, or template is patched on disk by the wrapper.
- No upstream source tree is vendored in this repository.
- Build/filesystem layer verdict: wrapper-only.

Runtime/API status:

- Transparent reverse proxying and Home Assistant ingress base-path handling are wrapper behavior.
- Path-only ingress normalization, including duplicate-prefix correction, is acceptable when upstream receives the request and the upstream response body is passed through unchanged.
- `console_compat_api.py` is quarantined legacy code and is not started or routed to in normal operation.
- Runtime/API layer verdict after Phase 3: upstream-looking packet and analytics routes are no longer served by local wrapper code in normal operation.

## Allowed Wrapper Behavior

The wrapper may own:

- Home Assistant repository metadata and add-on metadata in `repository.json` and `config.yaml`.
- Container build glue that installs upstream projects from documented repositories and refs.
- s6 supervision, service startup, shutdown handling, readiness checks, and log redaction.
- One-time default config creation when `/config/pymc-repeater/config.yaml` is missing.
- Preservation of an existing `/config/pymc-repeater/config.yaml` unchanged on later starts.
- Config persistence and path mapping for `/config/pymc-repeater`, `/etc/openhop_repeater`, `/var/lib/openhop_repeater`, `/etc/pymc_repeater`, and `/var/lib/pymc_repeater`.
- Home Assistant ingress base-path, path prefix, header, cookie, redirect, and WebSocket transport adaptation.
- Transparent reverse proxying where upstream receives the request and upstream response content is passed through unchanged.
- Path-only normalization such as `/api/api/*` to `/api/*` when it corrects an ingress/client duplicate-prefix issue without changing request or response content.
- Wrapper-owned static helper files such as ingress URL adaptation and wrapper navigation, provided they are documented.
- Wrapper diagnostics that live under clearly wrapper-owned paths and do not masquerade as upstream APIs or alter upstream behavior.

## Forbidden Wrapper Behavior

The wrapper must not do any of the following in normal operation:

- Serve local substitute APIs under upstream-looking paths.
- Generate responses for upstream API routes.
- Mutate upstream API JSON responses.
- Insert, rename, delete, infer, default, or fake upstream JSON fields.
- Generate synthetic telemetry, analytics, packet history, or radio values.
- Read upstream SQLite storage to recreate upstream API responses.
- Patch or edit upstream frontend bundles, static assets, templates, or Python modules on disk.
- Hide upstream route, schema, auth, or frontend changes behind compatibility shims.
- Bypass, weaken, or replace upstream auth/JWT/API-token semantics.

## Ingress Adaptation Is Not API Reimplementation

Ingress/base-path adaptation is transport work. It is acceptable when it only helps the browser reach the same upstream route under Home Assistant ingress.

Examples that are OK when response content stays upstream-controlled:

- Adding or forwarding `Host`, `X-Forwarded-*`, and `X-Ingress-Path` headers.
- Preserving request methods, query strings, headers, cookies, bodies, and WebSocket upgrade headers.
- Rewriting browser request URLs to include the Home Assistant ingress prefix.
- Rewriting cookie paths or redirects to keep navigation under the ingress prefix.
- Normalizing `/api/api/<path>` to `/api/<path>` before forwarding to upstream.

Examples that are not ingress adaptation:

- Serving `/api/recent_packets` from local SQLite instead of upstream.
- Serving `/api/bulk_packets` or `/api/filtered_packets` from local Python code.
- Serving `/api/analytics/*` with locally synthesized analytics.
- Accepting an upstream-looking API request because a token or `Authorization` header exists when upstream did not make that decision.

## Classification Rules

OK:

- Transparent path, base-url, header, cookie, redirect, or WebSocket proxy adaptations required for Home Assistant ingress.
- Wrapper diagnostics under wrapper-owned paths that do not alter upstream behavior.
- Path-only normalization that forwards to upstream and passes upstream response content unchanged.

Suspicious:

- Frontend response rewriting.
- Hardcoded minified bundle string rewrites.
- Third-party JSON URL rewriting for map assets.
- Any content mutation that may be needed for ingress but depends on upstream frontend internals.

Violation:

- Locally generated upstream-looking API responses.
- SQLite-backed API recreation.
- Synthetic analytics or telemetry.
- Fake/defaulted/inserted upstream fields.
- Auth behavior that differs from upstream.

## Exception Rule

An exception is allowed only when all of these are true:

- It is unavoidable for Home Assistant packaging or ingress.
- It is isolated in wrapper-owned infrastructure.
- It is documented in `docs/INGRESS_PROXYING.md` or `docs/WRAPPER_ROUTES.md`.
- Contract tests prove the exception does not hide upstream contract changes.
- Failure is clear when upstream changes break the wrapper assumption.

Local substitute APIs under upstream-looking paths are not allowed in normal operation. If a temporary compatibility mode is kept during migration, it must be explicit, default off, documented as non-wrapper behavior, and removed after upstream-supported routing is restored.
