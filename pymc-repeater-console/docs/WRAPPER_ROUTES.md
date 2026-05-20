# Wrapper Routes

This document classifies wrapper-owned routes and proxy rules for `pymc-repeater-console`.

Classification:

- OK: transparent path/base-url/header/WebSocket proxy adaptation.
- Suspicious: response content mutation or hardcoded frontend rewrite.
- Violation: locally generated upstream-looking API response or auth behavior different from upstream.

## Nginx Routes

| Path | Method | Type | Upstream target | Content changed | Classification | Notes |
|---|---|---|---|---|---|---|
| `/` and other unmatched paths | Any | Reverse proxy | `127.0.0.1:8001` | Sometimes, via `sub_filter` | Suspicious | Proxying is OK, but response injection/minified rewrites are suspicious. |
| `/ha-ingress-proxy.js` | GET | Wrapper static helper | Wrapper file | Yes, wrapper-owned file | OK | Provides ingress base-path URL adaptation. |
| `/ha-console-nav.js` | GET | Wrapper static helper | Wrapper file | Yes, wrapper-owned file | OK | Adds navigation between Console and Repeater UI. |
| `/api/api/*` | Any | Path normalization | Rewritten to `/api/*`, then upstream | No intended response change | OK | Accepted as duplicate-prefix transport normalization if tested. |
| `/_pymc_map_proxy/basemaps/*` | GET | Same-origin map proxy | `https://basemaps.cartocdn.com` | Yes, JSON URL rewrite | Suspicious | Not an upstream API, but mutates third-party map JSON. |
| `/_pymc_map_proxy/tiles/*` | GET | Same-origin map proxy | `https://tiles.basemaps.cartocdn.com` | Yes, JSON URL rewrite | Suspicious | Keep only if required for ingress map loading. |
| `/api/recent_packets` | GET | Local substitute API | `127.0.0.1:8090` | Yes, generated locally | Violation | Upstream currently provides this route; proxy upstream unchanged. |
| `/api/bulk_packets` | GET | Local substitute API | `127.0.0.1:8090` | Yes, generated locally | Violation | Upstream currently provides this route; proxy upstream unchanged. |
| `/api/filtered_packets` | GET | Local substitute API | `127.0.0.1:8090` | Yes, generated locally | Violation | Upstream currently provides this route; proxy upstream unchanged. |
| `/api/analytics/*` | GET | Local substitute API | `127.0.0.1:8090` | Yes, generated locally | Violation | Do not fake analytics when upstream does not provide it. |
| `/repeater` | GET | Redirect | Wrapper redirect | Redirect only | OK | Sends browser to `/repeater/` under ingress prefix. |
| `/repeater/*` | GET | Static route for preserved upstream Repeater UI | `/opt/pymc_repeater_original_web` | Sometimes, via `sub_filter` | Suspicious | Serving preserved files is OK; injected scripts and minified rewrites are suspicious. |

## Compatibility API Routes

Routes served by `console_compat_api.py`:

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

`/health` is acceptable only as a private wrapper diagnostic if it is not exposed as an upstream route.

All `/api/*` compatibility API routes are violations in normal operation because they generate upstream-looking responses locally.

## Upstream Routes That Should Be Proxied

Current upstream pyMC Repeater provides packet routes including:

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

The wrapper should proxy these unchanged when upstream provides them.

## Routes Upstream Does Not Currently Provide

Current upstream pyMC Repeater did not show `/api/analytics/*` routes during inspection.

Wrapper behavior must be:

- Do not synthesize those routes.
- Let the console fail clearly if it expects unavailable upstream APIs.
- Document unsupported Console pages or upstream requirements.
- Add contract tests that make missing upstream APIs visible.

