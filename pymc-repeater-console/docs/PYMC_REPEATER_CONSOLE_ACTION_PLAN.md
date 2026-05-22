# pyMC Repeater Console Wrapper Action Plan

Date: 2026-05-20

This plan turns the wrapper review into concrete follow-up work. The prime directive is that `pymc-repeater-console` must remain a Home Assistant wrapper, not a fork of pyMC Repeater or pyMC Console.

Ingress and base-path adaptation are valid wrapper behavior. Local substitute APIs are not ingress adaptation.

## 1. Current Verdict

Current status after Phase 3: **wrapper-pure for upstream-looking API routes, with suspicious ingress response rewrites remaining for Phase 4**.

Build and filesystem purity:

- The repository does not vendor pyMC Repeater or pyMC Console source.
- The Dockerfile clones upstream repositories during build.
- No `sed`, `perl`, `patch`, or `git apply` operation patches upstream files on disk.
- The Dockerfile copies upstream assets and licenses as build inputs.
- Verdict: **build/filesystem layer is currently wrapper-only**.

Runtime and API purity:

- Nginx transparently proxies most routes to upstream pyMC Repeater.
- Home Assistant ingress path, header, cookie, redirect, and WebSocket adaptations are valid wrapper behavior when request and response content remain upstream-controlled.
- Nginx transparently proxies `/api/recent_packets`, `/api/bulk_packets`, `/api/filtered_packets`, and `/api/analytics/*` to upstream pyMC Repeater.
- `console_compat_api.py` remains quarantined legacy code but is not started and is not routed to in normal operation.
- Verdict: **runtime/API layer is wrapper-pure for upstream-looking API routes**.

## 2. Wrapper Boundary

Allowed wrapper behavior:

- Home Assistant repository metadata and add-on metadata in `repository.json` and `config.yaml`.
- Container build glue that installs upstream from documented repositories and refs without patching source.
- s6 supervision, service startup, readiness checks, shutdown handling, and log redaction.
- One-time default upstream config creation when `/config/pymc-repeater/config.yaml` is missing.
- Preserving an existing `/config/pymc-repeater/config.yaml` unchanged on later starts.
- Config persistence and path mapping for `/config/pymc-repeater`, `/etc/pymc_repeater`, and `/var/lib/pymc_repeater`.
- Ingress base-path, path prefix, header, cookie, redirect, and WebSocket transport adaptation.
- Transparent reverse proxying where upstream receives the request and upstream response content is passed through unchanged.
- Wrapper diagnostics that do not masquerade as upstream APIs and do not alter upstream behavior.

Forbidden wrapper behavior:

- Local substitute APIs that expose upstream-looking routes.
- Response JSON mutation for upstream APIs.
- Fake, defaulted, inserted, renamed, or inferred upstream telemetry fields.
- SQLite reads used to recreate upstream API responses.
- Frontend bundle patching or editing upstream static files on disk.
- Response rewriting that changes upstream application behavior beyond strictly necessary ingress transport adaptation.
- Bypassing or weakening upstream auth/JWT/API-token semantics.
- Compatibility shims that hide upstream API or schema changes.

Classification rules:

- OK: transparent path/base-url/header/WebSocket proxy adaptations for Home Assistant ingress.
- Suspicious: frontend response rewriting, response content mutation for non-API assets, or hardcoded minified bundle rewrites.
- Violation: locally generated API responses, SQLite reads that recreate upstream APIs, synthetic analytics, inserted/defaulted telemetry fields, or auth behavior that differs from upstream.

## 3. Findings To Fix

| Finding | File/path | Current behavior | Classification | Why it matters | Proposed fix | Risk | Runtime behavior change |
|---|---|---|---|---|---|---|---|
| Local compatibility API | `rootfs/opt/pymc_repeater/console_compat_api.py` | Quarantined legacy file; no s6 service and no Nginx route use it in normal operation. | OK quarantine | It no longer serves upstream-looking API responses. | Keep unused or delete in a later cleanup. | Low | No current runtime API behavior |
| Intercepted packet APIs | `rootfs/etc/nginx/conf.d/pymc-repeater-ingress.conf` | Special `8090` locations removed; default upstream proxy handles `/api/recent_packets`, `/api/bulk_packets`, and `/api/filtered_packets`. | OK | Upstream controls auth, schema, and response content. | Keep proxied unchanged. | Low | Implemented in Phase 3 |
| Intercepted analytics APIs | `rootfs/etc/nginx/conf.d/pymc-repeater-ingress.conf` | Special `8090` location removed; default upstream proxy handles `/api/analytics/*`. | OK | The wrapper no longer fakes analytics; upstream serves or fails natively. | Keep proxied unchanged and document unsupported upstream pages if needed. | Low | Implemented in Phase 3 |
| SQLite-backed API recreation | `console_compat_api.py` | Quarantined legacy code still contains SQLite readers, but no normal route or service reaches it. | OK quarantine | Runtime no longer ties upstream-looking APIs to private SQLite internals. | Keep unreachable or delete in a later cleanup. | Low | Implemented in Phase 3 |
| Inserted packet fields | `console_compat_api.py` | Quarantined legacy code still contains field insertion logic, but no normal route or service reaches it. | OK quarantine | Runtime no longer changes packet API schema. | Keep unreachable or delete in a later cleanup. | Low | Implemented in Phase 3 |
| Synthetic analytics values | `console_compat_api.py` | Quarantined legacy code still contains synthetic analytics handlers, but no normal route or service reaches it. | OK quarantine | Runtime no longer returns wrapper-invented analytics. | Keep unreachable or delete in a later cleanup. | Low | Implemented in Phase 3 |
| Auth presence check | `console_compat_api.py` | Quarantined legacy code still contains local auth checks, but no normal route or service reaches it. | OK quarantine | Runtime API auth is upstream auth again. | Keep unreachable or delete in a later cleanup. | Low | Implemented in Phase 3 |
| `/api/api/*` duplicate-prefix rewrite | `pymc-repeater-ingress.conf` | Rewrites `/api/api/<path>` to `/api/<path>` and forwards onward. | OK | This is path-only transport normalization and does not generate or mutate responses. | Keep only if contract tests show it corrects an ingress/base-client duplicate-prefix issue. Document as ingress transport normalization. | Low | No immediate change |
| Main reverse proxy | `pymc-repeater-ingress.conf` | Proxies most routes to upstream `127.0.0.1:8001` with HA forwarding headers, redirects, cookies, and WebSocket upgrades. | OK | Required for HA ingress and direct access. | Keep. Add route/proxy contract tests. | Medium | No |
| HA ingress JS helper | `rootfs/opt/pymc_repeater/ha-ingress-proxy.js` | Rewrites browser request, asset, worker, EventSource, and WebSocket URLs to ingress base paths. | OK if path-only | Valid when limited to transport/base-url adaptation. | Document allowed scope and test that request/response bodies are unchanged. | Medium | No immediate change |
| Navigation helper | `rootfs/opt/pymc_repeater/ha-console-nav.js` | Adds wrapper-owned navigation between Console and Repeater UI. | OK | Wrapper UX chrome, not upstream API behavior. | Document as wrapper UI helper. Keep isolated. | Low | No |
| Script injection via `sub_filter` | `pymc-repeater-ingress.conf` | Injects wrapper JS into upstream HTML/JS responses. | Suspicious | It mutates upstream response content, even for ingress support. | Prefer upstream-supported base path config or proxy-only path handling. Document any remaining injection as an exception. | Medium | Yes, in Phase 4 if reduced |
| Hardcoded minified bundle rewrites | `pymc-repeater-ingress.conf` | Rewrites minified React/router snippets such as `history:r(...)` and `F.jsx(E7,...)`. | Suspicious | Depends on fragile upstream build internals and may silently break on upstream releases. | Remove where possible. Replace with path-level proxying or fail-fast contract tests. | High | Yes, in Phase 4 |
| Carto map same-origin proxy | `pymc-repeater-ingress.conf` | Proxies Carto basemap and tile JSON and rewrites embedded URLs. | Suspicious | Mutates third-party JSON, though for browser same-origin/ingress transport. | Keep only if required; document as non-upstream transport exception and test it. | Medium | Maybe in Phase 4 |
| Startup storage diagnostics | `rootfs/etc/s6-overlay/s6-rc.d/pymc-repeater/run` | Reads config and SQLite counts for logs only. | OK diagnostics | Does not serve upstream-looking API responses or alter behavior. | Keep as diagnostics; ensure secrets remain redacted. | Low | No |
| Upstream release refs | `Dockerfile`, `.github/workflows/build-pymc-repeater-console.yml` | Dockerfile default refs are pinned to known-good candidate SHAs; workflows can still override refs for dev/testing. | OK with remaining CI follow-up | Default builds are reproducible, while future scheduled CI should still test upstream drift separately. | Keep pinned defaults. Add scheduled upstream-main CI in Phase 5. | Medium | Build behavior only |
| Missing contract tests | `tests/contract/` | No contract test suite exists. | Suspicious process gap | Wrapper purity relies on manual inspection. | Add container and route tests proving transparent proxying and clear failures. | High | No direct runtime change |

## 4. Priority Order

### Phase 0 - Documentation only

Goal: make the wrapper boundary explicit before runtime changes.

- Add `docs/WRAPPER_BOUNDARY.md`.
- Add `docs/WRAPPER_ROUTES.md`.
- Add `docs/INGRESS_PROXYING.md`.
- Add `docs/UPSTREAM_TRACKING.md`.
- Add `compatibility/known-good-upstreams.json`.
- Add this action plan.
- No runtime behavior changes.

Deliverable: documentation and metadata only.

### Phase 1 - Upstream tracking

Goal: make releases reproducible and upstream drift visible.

- Pin release/default builds to known-good upstream SHAs.
- Preserve manual build-arg overrides for dev/testing.
- Record requested refs and resolved upstream SHAs in build logs.
- Add OCI labels for upstream repo, requested ref, and the metadata-file path.
- Store resolved SHAs and Console version in `/usr/share/pymc-repeater-console/upstream-build-info.json` because Docker labels cannot truthfully receive values discovered inside `RUN` steps.
- Add startup log showing upstream requested refs, resolved SHAs, and Console version.
- Add a diagnostics endpoint only if it is clearly wrapper-owned, does not shadow an upstream route, and does not alter upstream behavior.

Deliverable: reproducible release builds and visible upstream version metadata.

### Phase 2 - Contract tests

Goal: detect upstream breakage instead of hiding it.

- Added smoke tests for container start and HTTP readiness in `tests/contract/test_container_smoke.py`.
- Added route tests for Console `/`, Repeater `/repeater/`, helper scripts, `/api/api/*` normalization, and default proxy behavior.
- Added ingress-style tests for `X-Ingress-Path`, helper assets, redirects, and WebSocket upgrade path behavior.
- Added config persistence tests for preserving existing config, one-time default creation, removed option references, and missing `options:`/`schema:`.
- Added upstream API contract tests that now pass once Phase 3 removed normal compat API routing.
- Configurable port coverage currently comes from direct `8000` vs ingress `8080` URL selection through environment variables.

Deliverable: contract suite that fails when current wrapper routing/config/API purity assumptions break.

### Phase 3 - Remove or quarantine fork-like behavior

Goal: restore runtime/API wrapper purity.

- Removed Nginx interception of `/api/recent_packets`, `/api/bulk_packets`, `/api/filtered_packets`, and `/api/analytics/*`.
- Default proxying now sends those routes to upstream unchanged.
- If upstream does not provide `/api/analytics/*`, the wrapper no longer fakes it.
- Removed the compat API from normal s6 startup and ingress dependencies.
- Left `console_compat_api.py` as quarantined legacy code that is not started or routed to.

Deliverable: no local substitute upstream APIs in normal operation.

### Phase 4 - Reduce fragile frontend rewrites

Goal: keep ingress support while reducing response mutation.

- Removed the redundant Console `history:r(window.PyMCIngressBasePath...)` minified rewrite.
- Removed response-body rewriting from the Carto tile proxy.
- Kept the Repeater router basename rewrite and Console router basename rewrite as documented deferred exceptions.
- Kept ingress/base-path adaptations that are still required for static assets, helper script injection, redirects, cookies, browser request URLs, WebSockets, Workers, and map style JSON.
- Documented every remaining response rewrite in `docs/INGRESS_PROXYING.md`.
- Added contract tests that fail when the rewrite inventory or remaining upstream bundle snippets change.
- Prefer upstream build/config support for base paths if available.

Deliverable: smaller, documented, tested response rewrite surface.

### Phase 5 - CI hardening

Goal: make CI explain whether the wrapper or upstream changed.

- Release workflow builds pinned refs.
- Scheduled workflow tests upstream `main` without publishing release images.
- CI smoke-runs the container.
- CI route/proxy tests direct and ingress-style access.
- CI warns when upstream API/frontend structure changes.
- CI failure text must say whether breakage came from wrapper changes, pinned upstream changes, or scheduled upstream-main drift.

Deliverable: CI that protects wrapper purity and upstream contract visibility.

## 5. Decision Points

- Should `console_compat_api.py` be removed immediately, or kept temporarily behind explicit compatibility mode?
- If compatibility mode exists temporarily, should it default to off? Recommended answer: **yes, default off**.
- Should analytics pages be disabled or clearly marked unsupported if upstream does not provide analytics APIs? Recommended answer: **yes**.
- Should releases pin upstream commits while dev builds can test `main`? Current answer: **yes; Dockerfile defaults pin SHAs, manual dev builds and future scheduled CI may override refs to test upstream drift**.
- Which ingress rewrites are strictly transport-only?
  - Path prefix joins for fetch, XHR, EventSource, WebSocket, Worker, static assets.
  - `X-Forwarded-*`, `X-Ingress-Path`, cookie path, and redirect path adaptation.
  - `/api/api/*` duplicate-prefix normalization if response content is upstream unchanged.
- Which ingress rewrites are content mutations?
  - `sub_filter` script injection.
  - Hardcoded minified router rewrites.
  - Carto JSON URL rewriting.
- Which content mutations are still necessary after proxy-only alternatives are tried?
- Should wrapper diagnostics be private-only or exposed under a reserved wrapper namespace such as `/_wrapper/diagnostics`?

## 6. Concrete File Changes

Files to add:

- `pymc-repeater-console/docs/WRAPPER_BOUNDARY.md`
- `pymc-repeater-console/docs/WRAPPER_ROUTES.md`
- `pymc-repeater-console/docs/INGRESS_PROXYING.md`
- `pymc-repeater-console/docs/UPSTREAM_TRACKING.md`
- `pymc-repeater-console/docs/PYMC_REPEATER_CONSOLE_ACTION_PLAN.md`
- `pymc-repeater-console/compatibility/known-good-upstreams.json`
- `pymc-repeater-console/tests/contract/README.md`
- `pymc-repeater-console/tests/contract/test_container_smoke.py`
- `pymc-repeater-console/tests/contract/test_routes.py`
- `pymc-repeater-console/tests/contract/test_ingress_paths.py`
- `pymc-repeater-console/tests/contract/test_upstream_api_contract.py`
- `pymc-repeater-console/tests/contract/test_config_persistence.py`

Files to modify:

- `.github/workflows/build-pymc-repeater-console.yml`
- `pymc-repeater-console/Dockerfile`
- `pymc-repeater-console/README.md`
- `pymc-repeater-console/rootfs/etc/nginx/conf.d/pymc-repeater-ingress.conf`
- `pymc-repeater-console/rootfs/etc/s6-overlay/s6-rc.d/pymc-repeater/run`

Runtime files to modify only in later phases:

- `pymc-repeater-console/rootfs/etc/nginx/conf.d/pymc-repeater-ingress.conf`
- `pymc-repeater-console/rootfs/opt/pymc_repeater/console_compat_api.py`
- `pymc-repeater-console/rootfs/opt/pymc_repeater/ha-ingress-proxy.js`

## 7. Acceptance Criteria

Done means:

- No upstream source is patched on disk.
- No upstream API response is generated locally unless it is explicitly documented as a wrapper diagnostic under a wrapper-owned namespace.
- No route under `/api/*` is served by wrapper code unless it is a documented wrapper diagnostic and cannot be confused with upstream.
- All ingress rewrites are path/transport-only or documented exceptions.
- `/api/api/*` is documented and tested as path-only ingress transport normalization, not API emulation.
- `/api/recent_packets`, `/api/bulk_packets`, and `/api/filtered_packets` are proxied to upstream when upstream provides them.
- `/api/analytics/*` is not faked when upstream does not provide it.
- Auth behavior for proxied upstream APIs remains upstream auth behavior.
- Upstream refs are pinned for release/default builds.
- Scheduled CI tests upstream `main` without publishing release images once Phase 5 is implemented.
- Contract tests pass.
- Known-good upstream versions are recorded.
- The action plan and supporting docs clearly distinguish ingress proxying from API reimplementation.
