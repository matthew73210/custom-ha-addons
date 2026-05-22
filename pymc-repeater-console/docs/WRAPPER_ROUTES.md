# Wrapper Routes

This document inventories wrapper routes, proxy rules, and intercepted routes for `pymc-repeater-console`.

Classification:

- OK: transparent path/base-url/header/WebSocket proxy adaptation or clearly wrapper-owned diagnostics/static helpers.
- Suspicious: response content mutation, third-party content mutation, or hardcoded frontend rewrite.
- Violation: locally generated upstream-looking API response, SQLite-backed API recreation, synthetic telemetry, or auth behavior different from upstream.

## Route Inventory

| Path | Method | Handled by | Classification | Reason | Planned action |
|---|---|---|---|---|---|
| `/` | Any | Proxied to upstream pyMC Repeater at `127.0.0.1:8001` | Suspicious | Main proxying is OK, but current response handling injects wrapper scripts and rewrites frontend snippets with `sub_filter`. | Keep proxying. In Phase 4, reduce or document every remaining response rewrite and prefer path-level proxying/upstream base-path support. |
| Unmatched paths | Any | Proxied to upstream pyMC Repeater at `127.0.0.1:8001` | Suspicious | Default proxy behavior is valid ingress transport, but it shares the same response rewrite surface as `/`. | Keep default upstream proxying. Add contract tests for unchanged upstream API responses and static asset loading. |
| `/ha-ingress-proxy.js` | GET | Wrapper static file `/opt/pymc_repeater/ha-ingress-proxy.js` | OK | Wrapper-owned helper for browser-side ingress base-path URL adaptation. | Keep documented. Test that it only adapts request URLs and does not generate upstream API data. |
| `/ha-console-nav.js` | GET | Wrapper static file `/opt/pymc_repeater/ha-console-nav.js` | OK | Wrapper-owned navigation control between Console and Repeater UI. | Keep isolated and documented as wrapper UI chrome. |
| `/api/api/*` | Any | Nginx rewrite to `/api/*`, then normal upstream proxy | OK | Path-only duplicate-prefix normalization. It does not generate a response and should forward to upstream unchanged. | Keep only if contract tests prove response content is upstream unchanged. Document under ingress transport normalization. |
| `/api/recent_packets` | GET | Default proxy to upstream pyMC Repeater at `127.0.0.1:8001` | OK | Upstream receives the request and controls auth, schema, and response content. | Keep proxied unchanged; contract-test that wrapper does not intercept it. |
| `/api/bulk_packets` | GET | Default proxy to upstream pyMC Repeater at `127.0.0.1:8001` | OK | Upstream receives the request and controls auth, schema, and response content. | Keep proxied unchanged; contract-test that wrapper does not intercept it. |
| `/api/filtered_packets` | GET | Default proxy to upstream pyMC Repeater at `127.0.0.1:8001` | OK | Upstream receives the request and controls auth, schema, and response content. | Keep proxied unchanged; contract-test that wrapper does not intercept it. |
| `/api/analytics/*` | GET | Default proxy to upstream pyMC Repeater at `127.0.0.1:8001` | OK | The wrapper no longer synthesizes analytics. Upstream either serves the route or returns its native failure. | Keep proxied unchanged; do not fake analytics. |
| `/_pymc_map_proxy/basemaps/*` | GET | Wrapper same-origin proxy to `https://basemaps.cartocdn.com` | Suspicious | Not an upstream pyMC API, but it rewrites third-party JSON URLs for ingress/browser same-origin behavior. | Keep only if required. Document as ingress/map transport exception and add tests. |
| `/_pymc_map_proxy/tiles/*` | GET | Wrapper same-origin proxy to `https://tiles.basemaps.cartocdn.com` | Suspicious | Not an upstream pyMC API, but it rewrites third-party JSON URLs. | Keep only if required. Document as ingress/map transport exception and add tests. |
| `/repeater` | GET | Nginx redirect to `$ingress_prefix/repeater/` | OK | Wrapper path normalization for the preserved upstream Repeater UI. | Keep. Test direct and ingress-style redirect behavior. |
| `/repeater/` and `/repeater/*` | GET | Nginx static route from `/opt/pymc_repeater_original_web` | Suspicious | Serving preserved upstream UI files is OK, but current response handling injects wrapper scripts and rewrites a hardcoded router snippet. | Keep route. Phase 4: reduce hardcoded frontend rewrites or document as temporary exceptions. |
| `/ws/packets` | WebSocket | Default proxy to upstream pyMC Repeater | OK | Valid WebSocket forwarding when upgrade headers and messages pass through unchanged. | Add contract test proving upgrade succeeds and message content is not wrapper-mutated. |
| `/ws/companion_frame` | WebSocket | Default proxy to upstream pyMC Repeater | OK | Valid WebSocket forwarding when upgrade headers and messages pass through unchanged. | Add contract test proving upgrade succeeds and message content is not wrapper-mutated. |
| Other `/api/*` routes | Any | Default proxy to upstream pyMC Repeater unless explicitly intercepted above | OK | Transparent upstream API proxying is valid wrapper behavior. | Add tests that proxied APIs are upstream-controlled and not response-mutated. |

## Quarantined Compatibility API

`console_compat_api.py` remains in the repository as quarantined legacy code for now, but it is not in the s6 user bundle, has no ingress service dependency, and receives no normal Nginx traffic.

The quarantined file contains handlers for these old paths:

- `/health`
- `/api/recent_packets`
- `/api/bulk_packets`
- `/api/filtered_packets`
- `/api/analytics/topology`
- `/api/analytics/bucketed_stats`
- `/api/analytics/disambiguation`
- `/api/analytics/last_hop_neighbors`
- `/api/analytics/neighbor_affinity`
- `/api/analytics/mobile_nodes`
- `/api/analytics/path_health`
- `/api/analytics/tx_recommendations`
- `/api/analytics/sparklines`
- `/api/analytics/debug`

These handlers must not be reconnected to upstream-looking `/api/*` paths in normal operation.

## Upstream Routes That Should Pass Through

The wrapper should proxy upstream-provided routes unchanged. Current review identified these as upstream routes or upstream expectations:

- `/api/recent_packets`
- `/api/bulk_packets`
- `/api/filtered_packets`
- `/api/packet_stats`
- `/api/packet_type_graph_data`
- `/api/metrics_graph_data`
- `/api/noise_floor_history`
- `/api/crc_error_history`
- `/api/adverts_by_contact_type`
- `/api/db_stats`
- `/ws/packets`
- `/ws/companion_frame`

Contract tests verify these routes are not intercepted by wrapper Python code. If upstream provides them, upstream response content passes through unchanged.

## Routes Upstream Does Not Currently Provide

The review did not find upstream pyMC Repeater support for `/api/analytics/*`. After Phase 3 these routes are still forwarded upstream, but the wrapper does not synthesize responses.

Required behavior:

- Do not synthesize analytics.
- Do not read SQLite to recreate analytics APIs.
- Do not fake empty/default responses.
- Let Console fail clearly if it expects unavailable upstream APIs.
- Document unsupported Console pages or upstream version requirements.
