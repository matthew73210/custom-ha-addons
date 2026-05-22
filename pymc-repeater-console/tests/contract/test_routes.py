from __future__ import annotations

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
