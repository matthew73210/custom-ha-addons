from __future__ import annotations

import re

from helpers import ADDON_ROOT, NGINX_CONFIG, RUN_SCRIPT


INGRESS_HELPER = ADDON_ROOT / "rootfs/opt/pymc_repeater/ha-ingress-proxy.js"

# Audited against pyMC Console dist main at
# 2d961cef1ae1a355eb06e34fba99788d9ffca44a (Console 0.9.329).
CONSOLE_API_PATHS = {
    "/api/acl_clients",
    "/api/acl_info",
    "/api/acl_remove_client",
    "/api/acl_stats",
    "/api/advert_rate_limit_stats",
    "/api/adverts_by_contact_type",
    "/api/analytics/bucketed_stats",
    "/api/analytics/disambiguation",
    "/api/analytics/last_hop_neighbors",
    "/api/analytics/mobile_nodes",
    "/api/analytics/neighbor_affinity",
    "/api/analytics/path_health",
    "/api/analytics/sparklines",
    "/api/analytics/topology",
    "/api/analytics/tx_recommendations",
    "/api/auth/tokens",
    "/api/auth/tokens/",
    "/api/bulk_packets",
    "/api/check_pymc_console",
    "/api/companion/",
    "/api/crc_error_count",
    "/api/crc_error_history",
    "/api/crc_error_logs",
    "/api/create_identity",
    "/api/delete_identity",
    "/api/filtered_packets",
    "/api/hardware_processes",
    "/api/hardware_stats",
    "/api/identities",
    "/api/log_level",
    "/api/logs",
    "/api/metrics_graph_data",
    "/api/neighbor_remove",
    "/api/noise_floor_history",
    "/api/packet_by_hash",
    "/api/packet_stats",
    "/api/packet_type_graph_data",
    "/api/packet_type_stats",
    "/api/ping_neighbor",
    "/api/radio_presets",
    "/api/recent_packets",
    "/api/restart_service",
    "/api/room_clients",
    "/api/room_message",
    "/api/room_messages",
    "/api/room_messages_clear",
    "/api/room_post_message",
    "/api/room_stats",
    "/api/send_advert",
    "/api/send_room_server_advert",
    "/api/set_duty_cycle",
    "/api/set_mode",
    "/api/stats",
    "/api/transport_key/",
    "/api/transport_keys",
    "/api/unscoped_flood_policy",
    "/api/update/changelog",
    "/api/update/channels",
    "/api/update/check",
    "/api/update/install",
    "/api/update/progress",
    "/api/update/set_channel",
    "/api/update/status",
    "/api/update_advert_rate_limit_config",
    "/api/update_duty_cycle_config",
    "/api/update_identity",
    "/api/update_radio_config",
    "/api/update_web_config",
}

CONSOLE_AUTH_PATHS = {"/auth/login", "/auth/refresh"}
CONSOLE_WEBSOCKET_PATHS = {"/ws/companion_frame", "/ws/packets"}
CONSOLE_STATIC_PREFIXES = {"/assets/", "/favicon.ico"}


def test_console_namespaces_use_transparent_default_upstream_proxy():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")

    assert "location / {" in nginx
    assert "proxy_pass http://127.0.0.1:8001;" in nginx
    for path in CONSOLE_API_PATHS | CONSOLE_AUTH_PATHS | CONSOLE_WEBSOCKET_PATHS:
        assert f"location = {path}" not in nginx
        assert f"location ^~ {path}" not in nginx


def test_wrapper_exceptions_are_explicit_and_transport_only():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")

    for location in (
        "location ^~ /api/api/",
        "location ^~ /_pymc_map_proxy/basemaps/",
        "location ^~ /_pymc_map_proxy/tiles/",
        "location = /repeater",
        "location ^~ /repeater/",
    ):
        assert location in nginx


def test_ingress_helper_manages_console_absolute_route_namespaces():
    helper = INGRESS_HELPER.read_text(encoding="utf-8")

    for namespace in ("api", "auth", "ws", "assets", "_pymc_map_proxy"):
        assert namespace in helper
    for static_prefix in CONSOLE_STATIC_PREFIXES:
        name = static_prefix.lstrip("/").split("/", 1)[0]
        assert re.escape(name) in helper


def test_failed_console_route_diagnostics_cover_forwarded_namespaces():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")

    assert "~^/auth/.*:[45][0-9][0-9] 1;" in nginx
    assert "~^/api/.*:[45][0-9][0-9] 1;" in nginx
    assert "~^/ws/.*:[45][0-9][0-9] 1;" in nginx


def test_startup_diagnostics_report_lbt_requirements_without_faking_values():
    run_script = RUN_SCRIPT.read_text(encoding="utf-8")

    assert "Console LBT graphs require stored packets with lbt_attempts > 0." in run_script
    assert "packets_with_lbt_attempts_gt_zero" in run_script
    assert "log_lbt_diagnostics" in run_script
