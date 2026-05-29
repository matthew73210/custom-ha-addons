from __future__ import annotations

import re
from collections import Counter

import pytest

from helpers import NGINX_CONFIG, assert_not_gateway_error, http_request


EXPECTED_SUB_FILTER_RULES = Counter(
    {
        "sub_filter 'https://basemaps.cartocdn.com/' '$ingress_prefix/_pymc_map_proxy/basemaps/';": 1,
        "sub_filter 'https://tiles.basemaps.cartocdn.com/' '$ingress_prefix/_pymc_map_proxy/tiles/';": 1,
        "sub_filter '<head>' '<head><script src=\"$ingress_prefix/ha-ingress-proxy.js\"></script><script src=\"$ingress_prefix/ha-console-nav.js\"></script>';": 2,
        "sub_filter 'href=\"/assets/' 'href=\"$ingress_prefix/repeater/assets/';": 1,
        "sub_filter 'src=\"/assets/' 'src=\"$ingress_prefix/repeater/assets/';": 1,
        "sub_filter 'href=\"/favicon.ico\"' 'href=\"$ingress_prefix/repeater/favicon.ico\"';": 1,
        "sub_filter 'history:r(`/`),routes:' 'history:r(window.PyMCRepeaterBasePath||`/repeater/`),routes:';": 1,
        "sub_filter 'href=\"/' 'href=\"$ingress_prefix/';": 1,
        "sub_filter 'src=\"/' 'src=\"$ingress_prefix/';": 1,
        "sub_filter 'action=\"/' 'action=\"$ingress_prefix/';": 1,
        "sub_filter 'F.jsx(E7,{children:F.jsx(Die,{})})' 'F.jsx(E7,{basename:window.PyMCIngressBasePath||`/`,children:F.jsx(Die,{})})';": 1,
    }
)


def nginx_text() -> str:
    return NGINX_CONFIG.read_text(encoding="utf-8")


def test_removed_console_history_minified_rewrite_is_absent():
    nginx = nginx_text()
    assert "history:r(window.PyMCIngressBasePath||`/`),routes:" not in nginx


def test_carto_tile_proxy_no_longer_rewrites_json_responses():
    nginx = nginx_text()
    tile_block = nginx.split("location ^~ /_pymc_map_proxy/tiles/ {", 1)[1].split("\n    }", 1)[0]
    assert "sub_filter" not in tile_block


def test_carto_proxy_routes_remain_transport_only_inventory():
    nginx = nginx_text()
    basemap_block = nginx.split("location ^~ /_pymc_map_proxy/basemaps/ {", 1)[1].split(
        "\n    }",
        1,
    )[0]
    tile_block = nginx.split("location ^~ /_pymc_map_proxy/tiles/ {", 1)[1].split("\n    }", 1)[0]

    assert "proxy_pass https://basemaps.cartocdn.com;" in basemap_block
    assert "proxy_pass https://tiles.basemaps.cartocdn.com;" in tile_block
    assert "$ingress_prefix/_pymc_map_proxy/tiles/" in basemap_block
    assert "sub_filter" not in tile_block


def test_remaining_sub_filter_rules_are_intentional_inventory():
    actual_rules = Counter(
        line.strip()
        for line in nginx_text().splitlines()
        if line.strip().startswith("sub_filter ")
    )
    assert actual_rules == EXPECTED_SUB_FILTER_RULES


def test_ingress_helper_injection_applies_to_html_responses():
    nginx = nginx_text()
    assert nginx.count("sub_filter_types text/html application/javascript text/javascript;") == 2


def test_remaining_minified_bundle_rewrites_are_limited_and_documented():
    nginx = nginx_text()
    remaining_patterns = [
        "history:r(window.PyMCRepeaterBasePath||`/repeater/`),routes:",
        "F.jsx(E7,{basename:window.PyMCIngressBasePath||`/`,children:F.jsx(Die,{})})",
    ]
    for pattern in remaining_patterns:
        assert pattern in nginx
    assert nginx.count("history:r(") == 2
    assert nginx.count("F.jsx(E7") == 2


def test_helper_scripts_still_load(app):
    for path in ("/ha-ingress-proxy.js", "/ha-console-nav.js"):
        response = http_request(app.base_url, path)
        assert response.status == 200
        assert_not_gateway_error(response)


def asset_paths_from_html(html: str) -> list[str]:
    paths = re.findall(r"""(?:href|src)=["']([^"']*(?:/assets/|favicon\.ico)[^"']*)["']""", html)
    return [path for path in paths if not path.startswith(("http://", "https://", "data:"))]


def normalize_asset_path(path: str) -> str:
    marker = "/api/hassio_ingress/contract-token"
    if path.startswith(marker):
        path = path[len(marker):] or "/"
    if not path.startswith("/"):
        path = "/" + path
    return path


def test_console_static_asset_loads_under_direct_access(app):
    page = http_request(app.base_url, "/")
    if page.status != 200:
        pytest.skip(f"console route returned HTTP {page.status}")
    assets = asset_paths_from_html(page.text)
    if not assets:
        pytest.skip("console page did not expose static asset links")

    response = http_request(app.base_url, normalize_asset_path(assets[0]))
    assert_not_gateway_error(response)


def test_console_static_asset_loads_with_ingress_header(app):
    ingress_header = {"X-Ingress-Path": "/api/hassio_ingress/contract-token"}
    page = http_request(app.ingress_base_url, "/", headers=ingress_header)
    if page.status != 200:
        pytest.skip(f"console route returned HTTP {page.status}")
    assets = asset_paths_from_html(page.text)
    if not assets:
        pytest.skip("console page did not expose static asset links")

    response = http_request(
        app.ingress_base_url,
        normalize_asset_path(assets[0]),
        headers=ingress_header,
    )
    assert_not_gateway_error(response)
