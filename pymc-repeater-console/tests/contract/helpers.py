from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, build_opener
from urllib.request import HTTPRedirectHandler


ADDON_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ADDON_ROOT.parent
RUN_SCRIPT = ADDON_ROOT / "rootfs/etc/s6-overlay/s6-rc.d/pymc-repeater/run"
CONT_INIT_SCRIPT = ADDON_ROOT / "rootfs/etc/cont-init.d/pymc-repeater.sh"
NGINX_CONFIG = ADDON_ROOT / "rootfs/etc/nginx/conf.d/pymc-repeater-ingress.conf"
COMPAT_API = ADDON_ROOT / "rootfs/opt/pymc_repeater/console_compat_api.py"
COMPAT_SERVICE_USER_ENTRY = (
    ADDON_ROOT / "rootfs/etc/s6-overlay/s6-rc.d/user/contents.d/pymc-console-compat-api"
)
COMPAT_SERVICE_INGRESS_DEPENDENCY = (
    ADDON_ROOT
    / "rootfs/etc/s6-overlay/s6-rc.d/pymc-repeater-ingress/dependencies.d/pymc-console-compat-api"
)


@dataclass(frozen=True)
class HttpResponse:
    url: str
    status: int
    headers: Mapping[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> object:
        return json.loads(self.text)


@dataclass
class AppHandle:
    base_url: str
    ingress_base_url: str
    container_id: str | None = None
    config_dir: Path | None = None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        return None


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def test_timeout() -> float:
    return float(os.environ.get("PYMC_REPEATER_CONSOLE_TEST_TIMEOUT", "60"))


def join_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def http_request(
    base_url: str,
    path: str,
    *,
    headers: Mapping[str, str] | None = None,
    timeout: float | None = None,
    follow_redirects: bool = True,
) -> HttpResponse:
    request = Request(join_url(base_url, path), headers=dict(headers or {}), method="GET")
    opener = build_opener() if follow_redirects else build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=timeout or test_timeout()) as response:
            return HttpResponse(
                url=request.full_url,
                status=response.getcode(),
                headers=dict(response.headers.items()),
                body=response.read(),
            )
    except HTTPError as exc:
        return HttpResponse(
            url=request.full_url,
            status=exc.code,
            headers=dict(exc.headers.items()),
            body=exc.read(),
        )


def assert_not_gateway_error(response: HttpResponse) -> None:
    assert response.status not in {500, 502, 503, 504}, (
        f"{response.url} returned {response.status}: {response.text[:500]}"
    )


def wait_for_http(base_url: str, timeout: float) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = http_request(base_url, "/", timeout=2)
            if response.status < 500:
                return
        except Exception as exc:  # pragma: no cover - exercised in live Docker runs
            last_error = exc
        time.sleep(1)
    raise AssertionError(f"HTTP did not become reachable at {base_url}: {last_error}")


def docker_available() -> bool:
    return shutil.which("docker") is not None


def run_command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def docker_port_url(container_id: str, container_port: str) -> str:
    for _ in range(30):
        result = run_command(["docker", "port", container_id, container_port], check=False)
        if result.returncode == 0 and result.stdout.strip():
            host_port = result.stdout.strip().splitlines()[0].rsplit(":", 1)[-1]
            return f"http://127.0.0.1:{host_port}"
        time.sleep(0.2)
    raise AssertionError(f"Docker did not publish {container_port} for {container_id}")


def docker_logs(container_id: str) -> str:
    result = run_command(["docker", "logs", container_id], check=False)
    return (result.stdout or "") + (result.stderr or "")


def websocket_handshake(
    base_url: str,
    path: str,
    *,
    headers: Mapping[str, str] | None = None,
    timeout: float = 5,
) -> int:
    parsed = urlparse(join_url(base_url, path))
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if parsed.scheme == "https":
        raise RuntimeError("Raw TLS WebSocket checks are not implemented for contract tests")

    key = base64.b64encode(uuid.uuid4().bytes).decode("ascii")
    request_path = parsed.path or "/"
    if parsed.query:
        request_path += "?" + parsed.query

    lines = [
        f"GET {request_path} HTTP/1.1",
        f"Host: {host}:{port}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {key}",
        "Sec-WebSocket-Version: 13",
    ]
    for name, value in (headers or {}).items():
        lines.append(f"{name}: {value}")
    payload = ("\r\n".join(lines) + "\r\n\r\n").encode("ascii")

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(payload)
        response = sock.recv(512).decode("iso-8859-1", errors="replace")

    status_line = response.splitlines()[0]
    parts = status_line.split()
    if len(parts) < 2 or not parts[1].isdigit():
        raise AssertionError(f"Invalid WebSocket handshake response: {status_line!r}")
    return int(parts[1])
