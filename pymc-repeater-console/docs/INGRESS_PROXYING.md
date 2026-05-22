# Ingress Proxying

Home Assistant ingress support is valid wrapper behavior when it adapts transport details without replacing upstream behavior.

Ingress adaptation is about getting the same browser request to the same upstream service under a Home Assistant base path. It is not permission to generate upstream API responses locally.

## Current Ports

- Home Assistant ingress target: `8080`
- Direct wrapper access: `8000`
- Upstream pyMC Repeater backend: `127.0.0.1:8001`
- Local compatibility API: `127.0.0.1:8090`

The `8090` compatibility API is not ingress transport adaptation. It serves local substitute API responses and is classified in the action plan as a violation when exposed under upstream-looking `/api/*` paths.

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

## Auth And JWT Handling

Expected behavior:

- Upstream API auth remains upstream auth.
- The wrapper may pass `Authorization` headers and token query strings through.
- The wrapper must not accept or reject upstream-looking API routes using local auth semantics.
- A route must not be considered authorized only because an `Authorization` header or `token` query parameter exists.
- Wrapper diagnostics, if exposed, must use a wrapper-owned namespace and documented auth behavior.

## Suspicious Response Mutations

The following behavior exists today and is not fixed by this document. It is classified as suspicious because it mutates response content or depends on upstream frontend internals.

### Script Injection Via `sub_filter`

Current Nginx behavior injects:

- `/ha-ingress-proxy.js`
- `/ha-console-nav.js`

Reason:

- Enables ingress URL adaptation and wrapper navigation without patching files on disk.

Risk:

- Mutates upstream HTML/JS responses.
- May break when upstream frontend structure changes.
- Must be documented and contract-tested until removed or replaced by upstream-supported base-path configuration.

### Hardcoded Minified Bundle Rewrites

Current Nginx behavior rewrites hardcoded frontend snippets such as:

- `history:r(\`/\`),routes:`
- `F.jsx(E7,{children:F.jsx(Die,{})})`

Reason:

- Attempts to make upstream frontend routing work under Home Assistant ingress and `/repeater/`.

Risk:

- Depends on minified bundle internals.
- Can silently stop working when upstream Console or Repeater frontend changes.
- Should be reduced in Phase 4 and replaced with path-level proxying or upstream-supported base-path handling where possible.

### Carto JSON URL Rewriting

Current Nginx behavior proxies Carto basemap and tile requests through same-origin wrapper routes and rewrites embedded JSON URLs.

Reason:

- Allows map assets to load under ingress and browser same-origin constraints.

Risk:

- Mutates third-party JSON responses.
- Is not an upstream pyMC API, but still increases the wrapper content-rewrite surface.
- Should remain only if required, with tests documenting exactly what is rewritten.

## Forbidden Ingress Claims

Do not describe local substitute APIs as ingress support.

Specifically:

- `/api/recent_packets` served by `console_compat_api.py` is API reimplementation.
- `/api/bulk_packets` served by `console_compat_api.py` is API reimplementation.
- `/api/filtered_packets` served by `console_compat_api.py` is API reimplementation.
- `/api/analytics/*` served by `console_compat_api.py` is API reimplementation or synthetic analytics.

The correct wrapper posture is to proxy upstream unchanged when upstream provides a route, or fail clearly when upstream does not.
