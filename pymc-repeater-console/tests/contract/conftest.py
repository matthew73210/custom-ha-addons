from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import pytest

from helpers import (
    AppHandle,
    CI_SAFE_CONFIG,
    docker_available,
    docker_logs,
    docker_port_url,
    run_command,
    truthy,
    wait_for_http,
)


def prepare_config_dir(default_config_dir: Path) -> Path:
    configured = os.environ.get("PYMC_REPEATER_CONSOLE_CONFIG_DIR")
    config_dir = Path(configured) if configured else default_config_dir
    persistent_dir = config_dir / "pymc-repeater"
    persistent_dir.mkdir(parents=True, exist_ok=True)

    config_path = persistent_dir / "config.yaml"
    if not config_path.exists():
        shutil.copyfile(CI_SAFE_CONFIG, config_path)

    return config_dir


@pytest.fixture(scope="session")
def timeout_seconds() -> float:
    return float(os.environ.get("PYMC_REPEATER_CONSOLE_TEST_TIMEOUT", "60"))


@pytest.fixture(scope="session")
def app(tmp_path_factory: pytest.TempPathFactory, timeout_seconds: float) -> AppHandle:
    base_url = os.environ.get("PYMC_REPEATER_CONSOLE_BASE_URL")
    ingress_base_url = os.environ.get("PYMC_REPEATER_CONSOLE_INGRESS_BASE_URL") or base_url
    if base_url:
        return AppHandle(base_url=base_url, ingress_base_url=ingress_base_url or base_url)

    if truthy(os.environ.get("PYMC_REPEATER_CONSOLE_SKIP_DOCKER")):
        pytest.skip("PYMC_REPEATER_CONSOLE_SKIP_DOCKER is set and no base URL was provided")

    image = os.environ.get("PYMC_REPEATER_CONSOLE_IMAGE")
    if not image:
        pytest.skip("Set PYMC_REPEATER_CONSOLE_IMAGE or PYMC_REPEATER_CONSOLE_BASE_URL to run live contract tests")

    if not docker_available():
        pytest.skip("docker CLI is not available")

    config_dir = prepare_config_dir(tmp_path_factory.mktemp("pymc-repeater-config"))

    name = f"pymc-contract-{uuid.uuid4().hex[:12]}"
    result = run_command(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-p",
            "127.0.0.1::8000",
            "-p",
            "127.0.0.1::8080",
            "-v",
            f"{config_dir}:/config",
            image,
        ]
    )
    container_id = result.stdout.strip()
    handle = AppHandle(
        base_url=docker_port_url(container_id, "8000/tcp"),
        ingress_base_url=docker_port_url(container_id, "8080/tcp"),
        container_id=container_id,
        config_dir=config_dir,
    )

    try:
        wait_for_http(handle.base_url, timeout_seconds)
        yield handle
    except Exception as exc:
        logs = docker_logs(container_id)
        raise AssertionError(f"container did not become ready: {exc}\n\nDocker logs:\n{logs}") from exc
    finally:
        run_command(["docker", "rm", "-f", container_id], check=False)
