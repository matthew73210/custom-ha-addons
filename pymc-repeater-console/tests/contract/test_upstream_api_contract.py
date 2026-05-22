from __future__ import annotations

import pytest

from helpers import COMPAT_API, NGINX_CONFIG, http_request


FUTURE_CONTRACT_REASON = (
    "Phase 3 has not removed console_compat_api.py interception yet; "
    "this test documents the desired wrapper-only contract."
)


@pytest.mark.xfail(reason=FUTURE_CONTRACT_REASON, strict=False)
def test_packet_api_routes_are_not_intercepted_by_wrapper():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")
    for route in ("/api/recent_packets", "/api/bulk_packets", "/api/filtered_packets"):
        assert f"location = {route}" not in nginx
    assert "proxy_pass http://127.0.0.1:8090" not in nginx


@pytest.mark.xfail(reason=FUTURE_CONTRACT_REASON, strict=False)
def test_analytics_routes_are_not_synthesized_by_wrapper():
    compat = COMPAT_API.read_text(encoding="utf-8")
    assert "/api/analytics/" not in compat
    assert "build_topology" not in compat
    assert "bucketed_stats" not in compat


@pytest.mark.xfail(reason=FUTURE_CONTRACT_REASON, strict=False)
def test_wrapper_does_not_insert_packet_schema_fields():
    compat = COMPAT_API.read_text(encoding="utf-8")
    assert "packet_origin" not in compat
    assert "route_type" not in compat
    assert "payload_type" not in compat


@pytest.mark.xfail(reason=FUTURE_CONTRACT_REASON, strict=False)
def test_lbt_fields_are_not_wrapper_defaulted_or_selected_from_sqlite():
    compat = COMPAT_API.read_text(encoding="utf-8")
    assert "LBT_PACKET_COLUMNS" not in compat
    assert "lbt_attempts" not in compat
    assert "lbt_backoff_delays_ms" not in compat
    assert "lbt_channel_busy" not in compat


@pytest.mark.xfail(reason=FUTURE_CONTRACT_REASON, strict=False)
def test_live_analytics_endpoint_is_not_faked_when_upstream_lacks_it(app):
    response = http_request(
        app.base_url,
        "/api/analytics/debug",
        headers={"Authorization": "Bearer contract-test"},
    )
    if response.status == 404:
        return

    payload = response.json()
    assert not (
        response.status == 200
        and isinstance(payload, dict)
        and payload.get("success") is True
        and "db" in payload
    )


@pytest.mark.xfail(reason=FUTURE_CONTRACT_REASON, strict=False)
def test_live_packet_apis_do_not_return_wrapper_generated_bulk_metadata(app):
    response = http_request(
        app.base_url,
        "/api/bulk_packets?limit=1",
        headers={"Authorization": "Bearer contract-test"},
    )
    if response.status == 404:
        return

    payload = response.json()
    assert not (
        response.status == 200
        and isinstance(payload, dict)
        and payload.get("success") is True
        and payload.get("compressed") is False
    )
