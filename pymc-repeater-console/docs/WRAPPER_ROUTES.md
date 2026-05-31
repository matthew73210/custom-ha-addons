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
| `/_pymc_map_proxy/tiles/*` | GET | Wrapper same-origin proxy to `https://tiles.basemaps.cartocdn.com` | OK transport exception | Same-origin tile proxy for browser/ingress loading; Phase 4 removed response-body rewriting from this route. | Keep documented and tested. |
| `/repeater` | GET | Nginx redirect to `$ingress_prefix/repeater/` | OK | Wrapper path normalization for the preserved upstream Repeater UI. | Keep. Test direct and ingress-style redirect behavior. |
| `/repeater/` and `/repeater/*` | GET | Nginx static route from `/opt/pymc_repeater_original_web` | Suspicious | Serving preserved upstream UI files is OK, but response handling injects wrapper scripts and still rewrites one hardcoded router snippet for `/repeater/` basename support. | Keep route. Contract tests document the remaining rewrite. |
| `/ws/packets` | WebSocket | Default proxy to upstream pyMC Repeater | OK | Valid WebSocket forwarding when upgrade headers and messages pass through unchanged. | Add contract test proving upgrade succeeds and message content is not wrapper-mutated. |
| `/ws/companion_frame` | WebSocket | Default proxy to upstream pyMC Repeater | OK | Valid WebSocket forwarding when upgrade headers and messages pass through unchanged. | Add contract test proving upgrade succeeds and message content is not wrapper-mutated. |
| Other `/api/*` routes | Any | Default proxy to upstream pyMC Repeater unless explicitly intercepted above | OK | Transparent upstream API proxying is valid wrapper behavior. | Add tests that proxied APIs are upstream-controlled and not response-mutated. |

## Bundled Console Route Audit

Audited against pyMC Console dist `main` commit
`2d961cef1ae1a355eb06e34fba99788d9ffca44a` (`0.9.329`).

Console REST paths found in the bundled frontend:

```text
/api/acl_clients
/api/acl_info
/api/acl_remove_client
/api/acl_stats
/api/advert_rate_limit_stats
/api/adverts_by_contact_type
/api/analytics/bucketed_stats
/api/analytics/disambiguation
/api/analytics/last_hop_neighbors
/api/analytics/mobile_nodes
/api/analytics/neighbor_affinity
/api/analytics/path_health
/api/analytics/sparklines
/api/analytics/topology
/api/analytics/tx_recommendations
/api/auth/tokens
/api/auth/tokens/
/api/bulk_packets
/api/check_pymc_console
/api/companion/
/api/crc_error_count
/api/crc_error_history
/api/crc_error_logs
/api/create_identity
/api/delete_identity
/api/filtered_packets
/api/hardware_processes
/api/hardware_stats
/api/identities
/api/log_level
/api/logs
/api/metrics_graph_data
/api/neighbor_remove
/api/noise_floor_history
/api/packet_by_hash
/api/packet_stats
/api/packet_type_graph_data
/api/packet_type_stats
/api/ping_neighbor
/api/radio_presets
/api/recent_packets
/api/restart_service
/api/room_clients
/api/room_message
/api/room_messages
/api/room_messages_clear
/api/room_post_message
/api/room_stats
/api/send_advert
/api/send_room_server_advert
/api/set_duty_cycle
/api/set_mode
/api/stats
/api/transport_key/
/api/transport_keys
/api/unscoped_flood_policy
/api/update/changelog
/api/update/channels
/api/update/check
/api/update/install
/api/update/progress
/api/update/set_channel
/api/update/status
/api/update_advert_rate_limit_config
/api/update_duty_cycle_config
/api/update_identity
/api/update_radio_config
/api/update_web_config
```

Other Console browser paths found:

```text
/auth/login
/auth/refresh
/ws/companion_frame
/ws/packets
/assets/*
/favicon.ico
```

All of these paths use the transparent default upstream proxy. Static helper routes,
the preserved `/repeater/` UI, duplicate `/api/api/*` normalization, and Carto
same-origin paths remain explicit wrapper exceptions.

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

## LBT Graph Requirement

Console filters Signal Lab LBT chart rows to packets where `lbt_attempts > 0`.
Upstream pyMC Repeater persists `lbt_attempts`, `lbt_backoff_delays_ms`, and
`lbt_channel_busy`, but the graph remains empty when the stored rows are
`0`, `null` or empty, and `false`.

For upstream `pymc_usb` and `pymc_tcp`, pyMC_core emits a positive attempt count
only when CAD finds the channel busy and performs a backoff. SX1262 also has an
upstream CAD-before-transmit path. Other radio paths may not emit LBT metadata.
The wrapper must not fabricate positive values to make the chart render.
