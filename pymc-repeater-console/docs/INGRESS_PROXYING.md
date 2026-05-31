# Ingress Proxying

Home Assistant ingress support is valid wrapper behavior when it adapts transport details without replacing upstream behavior.

Ingress adaptation is about getting the same browser request to the same upstream service under a Home Assistant base path. It is not permission to generate upstream API responses locally.

## Current Ports

- Home Assistant ingress target: `8080`
- Direct wrapper access: `8000`
- Upstream pyMC Repeater backend: `127.0.0.1:8001`

The old `8090` compatibility API is no longer started or routed to in normal operation. It was not ingress transport adaptation and must not be reintroduced under upstream-looking `/api/*` paths.

## Valid Ingress Adaptations

Allowed ingress behavior includes:

- Mapping Home Assistant ingress paths to the container service.
- Preserving request methods, query strings, headers, cookies, and bodies.
- Forwarding `Host`, `X-Forwarded-*`, and `X-Ingress-Path`.
- Rewriting cookie paths and redirects so browser navigation stays under the ingress prefix.
- Forwarding WebSocket upgrade headers.
- Rewriting browser request URLs so fetch, XHR, EventSource, WebSocket, Worker, SharedWorker, forms, links, images, and scripts include the ingress base path.
- Path-only normalization before forwarding to upstream.

These adaptations are OK only when upstream ultimately receives the request and response content remains upstream-controlled.

## Base Path Handling

The wrapper currently derives the ingress prefix from:

- `X-Ingress-Path`
- Browser paths containing `/api/hassio_ingress/<token>/`

Browser-side URL adaptation is allowed when it only adjusts where the request is sent. It must not fabricate upstream API payloads or hide missing upstream routes.

## `/api/api/*` Normalization

Current behavior:

- `/api/api/<path>` is rewritten to `/api/<path>`.
- The normalized request continues through normal upstream proxy handling.
- The wrapper does not generate the response.

Classification: OK as ingress transport normalization, provided contract tests confirm it is path-only and response content is upstream unchanged.

Required tests:

- Verify the duplicate-prefix request reaches the matching upstream route.
- Verify request method, query string, body, and relevant auth headers are preserved.
- Verify response status, headers that matter to the app, and response body are not generated or mutated by wrapper code.

## WebSocket Handling

Expected behavior:

- `/ws/packets` is forwarded to upstream.
- `/ws/companion_frame` is forwarded to upstream.
- `Upgrade` and `Connection` headers are preserved.
- Browser WebSocket URLs may be rewritten to include the ingress base path.
- WebSocket message content must not be changed by the wrapper.

This is OK wrapper behavior when it is transparent transport forwarding.

## Audited Console Route Namespaces

The Console dist `main` audit at commit `2d961cef1ae1a355eb06e34fba99788d9ffca44a`
(`0.9.329`) found these browser-facing route groups:

- `/api/*` for REST, history, graph, config, room, companion, update, and analytics requests.
- `/auth/login` and `/auth/refresh` for sessions.
- `/ws/packets` and `/ws/companion_frame` for live WebSocket traffic.
- `/assets/*` and `/favicon.ico` for Console static files and worker scripts.
- Carto style and tile URLs routed through `/_pymc_map_proxy/basemaps/*` and `/_pymc_map_proxy/tiles/*`.

The default Nginx proxy forwards the upstream namespaces unchanged. Explicit locations are limited to wrapper-owned helper assets, duplicate `/api/api/*` path normalization, the preserved `/repeater/` UI mount, and the Carto same-origin proxy.

Current Console dist calls `/api/analytics/*`, but the audited pyMC Repeater `main` source does not provide that namespace. The wrapper forwards those calls and preserves the native upstream failure.

## Diagnosing Failures

Nginx writes failure-only diagnostics for `/auth/*`, `/api/*`, `/ws/*`, and `/_pymc_map_proxy/*`. Each line includes status, upstream address, auth-header presence, token-query presence, upgrade header, host, and ingress prefix presence without logging token values.

When persisted `logging.level` is `DEBUG`, startup compares direct-wrapper and ingress responses for representative Console auth, history, graph, hardware, companion, and analytics routes. Matching status and response metadata show that ingress forwarding is transparent even when upstream intentionally returns `401`, `404`, or `405`.

## Auth And JWT Handling

Expected behavior:

- Upstream API auth remains upstream auth.
- The wrapper may pass `Authorization` headers and token query strings through.
- The wrapper must not accept or reject upstream-looking API routes using local auth semantics.
- A route must not be considered authorized only because an `Authorization` header or `token` query parameter exists.
- Wrapper diagnostics, if exposed, must use a wrapper-owned namespace and documented auth behavior.

## Response Rewrite Inventory

Phase 4 reduced but did not eliminate response rewriting. The remaining rules are documented here so future upstream frontend changes fail visibly in contract tests.

| Rewrite | Classification | Status | Reason |
|---|---|---|---|
| Inject `/ha-ingress-proxy.js` into Console and Repeater HTML | KEEP | Required ingress transport adaptation | Installs stable wrapper helper logic for fetch, XHR, WebSocket, Worker, EventSource, and DOM URL base-path adaptation. |
| Inject `/ha-console-nav.js` into Console and Repeater HTML | KEEP | Wrapper UI helper | Adds navigation between Console and the preserved Repeater UI without patching upstream files on disk. |
| Rewrite static `href="/..."`, `src="/..."`, and `action="/..."` attributes | KEEP | Required ingress transport adaptation | Parser-created static asset/form URLs may load before helper monkey-patches can affect them. |
| Rewrite Repeater static asset URLs under `/repeater/assets/` and `/repeater/favicon.ico` | KEEP | Required `/repeater/` path adaptation | The preserved upstream Repeater UI is mounted under `/repeater/` while its asset references are root-relative. |
| Rewrite `/api/api/*` to `/api/*` | KEEP | Path-only transport normalization | Some Repeater panels emit duplicate API prefixes. The response is still upstream-controlled. |
| Rewrite Console `history:r(\`/\`),routes:` | REMOVE | Removed in Phase 4 | This exact minified Console history rewrite was redundant with the remaining Console basename rewrite and helper script. |
| Rewrite Repeater `history:r(\`/\`),routes:` | DEFER | Still suspicious | Needed for the preserved Repeater UI mounted at `/repeater/`; depends on upstream minified bundle shape and is covered by contract tests. |
| Rewrite Console `F.jsx(E7,{children:F.jsx(Die,{})})` | DEFER | Still suspicious | Needed to give the Console router an ingress basename; depends on upstream minified bundle shape and is covered by contract tests. |
| Rewrite Carto basemap JSON URLs | DEFER | Browser/ingress same-origin exception | Map style JSON embeds absolute Carto URLs. The same-origin proxy keeps map assets loadable under ingress. |
| Rewrite Carto tile proxy responses | REMOVE | Removed in Phase 4 | Tile responses are not the basemap style JSON that needs embedded URL rewriting. |

Remaining `sub_filter` rules are asserted by `tests/contract/test_frontend_rewrites.py`. Adding, removing, or changing one requires updating this document and the explicit test inventory.

## Forbidden Ingress Claims

Do not describe local substitute APIs as ingress support.

Before Phase 3 these routes were incorrectly served by local wrapper code. They now go through the default upstream proxy:

- `/api/recent_packets`
- `/api/bulk_packets`
- `/api/filtered_packets`
- `/api/analytics/*`

The correct wrapper posture is to proxy upstream unchanged when upstream provides a route, or fail clearly when upstream does not.
