from __future__ import annotations

from helpers import (
    COMPAT_SERVICE_INGRESS_DEPENDENCY,
    COMPAT_SERVICE_USER_ENTRY,
    NGINX_CONFIG,
    http_request,
)


def test_packet_api_routes_are_not_intercepted_by_wrapper():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")
    for route in ("/api/recent_packets", "/api/bulk_packets", "/api/filtered_packets"):
        assert f"location = {route}" not in nginx
    assert "proxy_pass http://127.0.0.1:8090" not in nginx


def test_analytics_routes_are_not_intercepted_by_wrapper():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")
    assert "location ^~ /api/analytics/" not in nginx
    assert "proxy_pass http://127.0.0.1:8090" not in nginx


def test_compat_service_is_not_started_in_normal_operation():
    assert not COMPAT_SERVICE_USER_ENTRY.exists()
    assert not COMPAT_SERVICE_INGRESS_DEPENDENCY.exists()


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


def test_normal_packet_path_cannot_insert_wrapper_telemetry_fields():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")
    assert "/api/recent_packets" not in nginx
    assert "/api/bulk_packets" not in nginx
    assert "/api/filtered_packets" not in nginx
    assert not COMPAT_SERVICE_USER_ENTRY.exists()


def test_normal_packet_path_cannot_default_lbt_fields_from_wrapper_sqlite():
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")
    assert "127.0.0.1:8090" not in nginx
    assert not COMPAT_SERVICE_USER_ENTRY.exists()
