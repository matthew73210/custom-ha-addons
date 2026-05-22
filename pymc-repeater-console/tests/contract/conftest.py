from __future__ import annotations

import os
import uuid

import pytest

from helpers import AppHandle, docker_available, docker_logs, docker_port_url, run_command, truthy, wait_for_http


CONTRACT_CONFIG = """\
radio_type: pymc_tcp
repeater:
  node_name: pyMC Contract Test
  mode: forward
  latitude: 0.0
  longitude: 0.0
  country: FR
  identity_file: /config/pymc-repeater/identity.key
  owner_info: ""
  cache_ttl: 3600
  max_flood_hops: 64
  use_score_for_tx: false
  score_threshold: 0.3
  send_advert_interval_hours: 10
  allow_discovery: true
  advert_rate_limit:
    enabled: true
    bucket_capacity: 2
    refill_tokens: 1
    refill_interval_seconds: 36000
    min_interval_seconds: 3600
  advert_penalty_box:
    enabled: true
    violation_threshold: 2
    base_penalty_seconds: 21600
    penalty_multiplier: 2.0
    max_penalty_seconds: 86400
    violation_decay_seconds: 43200
  advert_adaptive:
    enabled: true
    ewma_alpha: 0.1
    hysteresis_seconds: 300
    thresholds:
      quiet_max: 0.05
      normal_max: 0.20
      busy_max: 0.50
      normal: 1.0
      busy: 5.0
      congested: 15.0
  advert_dedupe:
    ttl_seconds: 120
    max_hashes: 10000
  security:
    max_clients: 1
    admin_password: change_me
    guest_password: ""
    allow_read_only: false
    jwt_secret: ""
    jwt_expiry_minutes: 60
mesh:
  unscoped_flood_allow: true
  path_hash_mode: 0
  loop_detect: minimal
identities:
  room_servers: []
  companions: []
radio:
  frequency: 869618000
  tx_power: 14
  bandwidth: 62500
  spreading_factor: 8
  coding_rate: 8
  preamble_length: 16
  sync_word: 18
pymc_tcp:
  host: 192.0.2.1
  port: 5055
  token: ""
  connect_timeout: 0.1
  lbt_enabled: true
  lbt_max_attempts: 1
storage:
  storage_dir: /config/pymc-repeater
  retention:
    sqlite_cleanup_days: 31
mqtt_brokers:
  iata_code: PAR
  country: FR
  status_interval: 300
  owner: ""
  email: ""
  brokers: []
mqtt: {}
glass:
  enabled: false
  base_url: http://localhost:8080
  inform_interval_seconds: 30
  request_timeout_seconds: 10
  verify_tls: true
  api_token: ""
  cert_store_dir: /config/pymc-repeater/glass
http:
  host: 127.0.0.1
  port: 8001
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
web:
  web_path: /opt/pymc_console/web/html
  cors_enabled: false
"""


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

    config_dir = tmp_path_factory.mktemp("pymc-repeater-config")
    persistent_dir = config_dir / "pymc-repeater"
    persistent_dir.mkdir(parents=True, exist_ok=True)
    (persistent_dir / "config.yaml").write_text(CONTRACT_CONFIG, encoding="utf-8")

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
