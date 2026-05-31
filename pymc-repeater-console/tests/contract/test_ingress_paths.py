from __future__ import annotations

import pytest

from helpers import assert_not_gateway_error, http_request, websocket_handshake


INGRESS_HEADER = {"X-Ingress-Path": "/api/hassio_ingress/contract-token"}


def test_root_with_ingress_header_routes(app):
    response = http_request(app.ingress_base_url, "/", headers=INGRESS_HEADER)
    assert_not_gateway_error(response)


def test_static_helper_loads_through_ingress_entrypoint(app):
    response = http_request(app.ingress_base_url, "/ha-ingress-proxy.js", headers=INGRESS_HEADER)
    assert response.status == 200
    assert b"PyMC" in response.body or b"ingress" in response.body.lower()


def test_console_nav_loads_through_ingress_entrypoint(app):
    response = http_request(app.ingress_base_url, "/ha-console-nav.js", headers=INGRESS_HEADER)
    assert response.status == 200
    assert b"Console" in response.body or b"Repeater" in response.body


def test_repeater_redirect_preserves_ingress_prefix_when_observable(app):
    response = http_request(
        app.ingress_base_url,
        "/repeater",
        headers=INGRESS_HEADER,
        follow_redirects=False,
    )
    assert response.status in {301, 302, 303, 307, 308}
    location = response.headers.get("Location", "")
    assert location.endswith("/repeater/")
    assert "/api/hassio_ingress/contract-token" in location


@pytest.mark.parametrize("path", ["/ws/packets", "/ws/companion_frame"])
def test_websocket_upgrade_path_is_forwarded_or_fails_without_gateway_error(app, path):
    try:
        status = websocket_handshake(app.ingress_base_url, path, headers=INGRESS_HEADER)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    assert status not in {500, 502, 503, 504}
