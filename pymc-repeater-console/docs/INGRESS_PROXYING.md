# Ingress Proxying

Home Assistant ingress support is valid wrapper behavior when it adapts transport details without replacing upstream behavior.

## Valid Ingress Adaptations

Allowed ingress behavior includes:

- Mapping Home Assistant ingress paths to the container service.
- Preserving request methods, query strings, headers, and bodies.
- Forwarding `Host`, `X-Forwarded-*`, and `X-Ingress-Path`.
- Rewriting cookie paths and redirects so browser navigation stays under the ingress prefix.
- Forwarding WebSocket upgrade headers.
- Rewriting request URLs from browser code so they include the ingress base path.
- Path-only normalization before forwarding to upstream.

These adaptations are OK only when upstream ultimately receives the request and response content is passed through unchanged.

## Current Ports

- Home Assistant ingress target: `8080`
- Direct wrapper access: `8000`
- Upstream pyMC Repeater backend: `127.0.0.1:8001`
- Local compatibility API: `127.0.0.1:8090`

The `8090` compatibility API is not ingress transport adaptation. It serves local substitute API responses and is covered by the action plan as a violation.

## Base Path Handling

The wrapper currently derives the ingress prefix from:

- `X-Ingress-Path`
- Browser paths containing `/api/hassio_ingress/<token>/`

Path/base-url rewriting for fetch, XHR, EventSource, WebSocket, Worker, SharedWorker, forms, links, images, and scripts is acceptable when it only makes upstream browser requests reach the same upstream route under HA ingress.

## `/api/api/*` Normalization

Current behavior:

- `/api/api/<path>` is rewritten to `/api/<path>`.
- The resulting request continues through the normal proxy path.
- The wrapper does not generate the response.

Classification: OK as ingress transport normalization, provided contract tests confirm it is path-only and response content is upstream unchanged.

Required documentation/testing:

- Explain which UI condition emits the duplicate prefix.
- Verify the normalized route reaches upstream.
- Verify response content is not changed by the wrapper.

## Content Rewrites

Current response mutations include:

- Injecting `ha-ingress-proxy.js`.
- Injecting `ha-console-nav.js`.
- Rewriting static asset URLs in HTML/JS responses.
- Rewriting hardcoded minified frontend router snippets.
- Rewriting Carto map JSON URLs for same-origin map loading.

Classification: suspicious.

These may be temporarily necessary for ingress, but each remaining rewrite must be:

- Documented in `docs/WRAPPER_ROUTES.md`.
- Covered by contract tests.
- Removed when path-level proxying or upstream base-path support can replace it.

## WebSocket Handling

Expected behavior:

- `/ws/packets` is forwarded to upstream.
- `/ws/companion_frame` is forwarded to upstream.
- `Upgrade` and `Connection` headers are preserved.
- Browser WebSocket URLs may be rewritten to the ingress base path.
- WebSocket message content must not be changed by the wrapper.

## Auth Handling

Expected behavior:

- Upstream API auth remains upstream auth.
- The wrapper may pass `Authorization` headers and token query strings through.
- The wrapper must not accept a route only because an auth header exists.
- Wrapper diagnostics, if exposed, must use a wrapper-owned namespace and documented auth behavior.

