from __future__ import annotations

import pytest

from helpers import assert_not_gateway_error, http_request


def test_console_root_route(app):
    response = http_request(app.base_url, "/")
    assert_not_gateway_error(response)


def test_repeater_route(app):
    response = http_request(app.base_url, "/repeater/")
    assert_not_gateway_error(response)


def test_ingress_helper_script_route(app):
    response = http_request(app.base_url, "/ha-ingress-proxy.js")
    assert response.status == 200
    assert "javascript" in response.headers.get("Content-Type", "").lower()


def test_console_nav_script_route(app):
    response = http_request(app.base_url, "/ha-console-nav.js")
    assert response.status == 200
    assert "javascript" in response.headers.get("Content-Type", "").lower()


def test_api_duplicate_prefix_normalization_is_routable(app):
    direct = http_request(app.base_url, "/api/stats?contract=direct")
    normalized = http_request(app.base_url, "/api/api/stats?contract=normalized")

    assert_not_gateway_error(direct)
    assert_not_gateway_error(normalized)
    assert normalized.status == direct.status


def test_default_proxy_for_unknown_safe_route_does_not_break_gateway(app):
    response = http_request(app.base_url, "/__pymc_contract_unknown_route__")
    assert_not_gateway_error(response)


@pytest.mark.parametrize(
    "path",
    [
        "/auth/refresh",
        "/api/stats?contract=route-inventory",
        "/api/recent_packets?limit=1",
        "/api/bulk_packets?limit=1",
        "/api/filtered_packets?limit=1",
        "/api/packet_by_hash?packet_hash=contract-missing",
        "/api/packet_stats?hours=24",
        "/api/packet_type_stats?hours=24",
        "/api/packet_type_graph_data?hours=24&resolution=average&types=all",
        "/api/metrics_graph_data?hours=24&resolution=average&metrics=rx_count,tx_count",
        "/api/noise_floor_history?hours=24",
        "/api/crc_error_count?hours=24",
        "/api/crc_error_history?hours=24",
        "/api/crc_error_logs?hours=24",
        "/api/adverts_by_contact_type?limit=1&hours=24",
        "/api/db_stats",
        "/api/hardware_stats",
        "/api/hardware_processes",
        "/api/advert_rate_limit_stats",
        "/api/transport_keys",
        "/api/unscoped_flood_policy",
        "/api/companion/stats?type=packets",
        "/api/analytics/topology",
    ],
)
def test_console_api_forward_inventory_is_routable(app, path):
    response = http_request(app.base_url, path)
    assert_not_gateway_error(response)
