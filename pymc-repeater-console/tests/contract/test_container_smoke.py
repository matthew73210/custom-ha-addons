from __future__ import annotations

import subprocess

import pytest

from helpers import assert_not_gateway_error, docker_logs, http_request, run_command


def test_container_http_server_becomes_reachable(app):
    response = http_request(app.base_url, "/")
    assert_not_gateway_error(response)


def test_console_route_returns_expected_http_response(app):
    response = http_request(app.base_url, "/")
    assert response.status in {200, 301, 302, 401, 403}, response.text[:500]


def test_repeater_route_returns_expected_http_response(app):
    response = http_request(app.base_url, "/repeater/")
    assert response.status in {200, 301, 302, 401, 403}, response.text[:500]


def test_container_does_not_crash_immediately(app):
    if not app.container_id:
        pytest.skip("container state is only available when tests start Docker")

    result = run_command(
        ["docker", "inspect", "-f", "{{.State.Running}}", app.container_id],
        check=False,
    )
    assert result.returncode == 0, docker_logs(app.container_id)
    assert result.stdout.strip() == "true", docker_logs(app.container_id)


def test_upstream_build_metadata_file_exists_when_container_accessible(app):
    if not app.container_id:
        pytest.skip("metadata file check requires Docker container access")

    result = run_command(
        [
            "docker",
            "exec",
            app.container_id,
            "python3",
            "-m",
            "json.tool",
            "/usr/share/pymc-repeater-console/upstream-build-info.json",
        ],
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
