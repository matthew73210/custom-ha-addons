#!/usr/bin/with-contenv bashio
set -euo pipefail

CONFIG_ROOT="/config/pymc-repeater"
DATA_ROOT="/data/pymc-repeater"
ETC_ROOT="/etc/pymc_repeater"
VAR_ROOT="/var/lib/pymc_repeater"
CONFIG_PATH="${CONFIG_ROOT}/config.yaml"
PYTHON_BIN="/opt/venv/bin/python3"

mkdir -p "${CONFIG_ROOT}" "${DATA_ROOT}"

if [ -e "${ETC_ROOT}" ] && [ ! -L "${ETC_ROOT}" ]; then
  rm -rf "${ETC_ROOT}"
fi
ln -sfn "${CONFIG_ROOT}" "${ETC_ROOT}"

if [ -e "${VAR_ROOT}" ] && [ ! -L "${VAR_ROOT}" ]; then
  rm -rf "${VAR_ROOT}"
fi
ln -sfn "${CONFIG_ROOT}" "${VAR_ROOT}"

MIGRATION_RESULT="$("${PYTHON_BIN}" - <<'PY'
import os
import pathlib
import shutil
import time

source = pathlib.Path("/data/pymc-repeater")
target = pathlib.Path("/config/pymc-repeater")

if not source.exists():
    print("No legacy /data/pymc-repeater directory found; migration skipped.")
    raise SystemExit(0)

try:
    if source.resolve() == target.resolve():
        print("Legacy data path already resolves to persistent config storage; migration skipped.")
        raise SystemExit(0)
except FileNotFoundError:
    pass

timestamp = time.strftime("%Y%m%d-%H%M%S")
conflict_root = target / ".migration-conflicts" / timestamp
migrated = []
replaced = []
conflicts = []
skipped = []

for item in sorted(source.rglob("*")):
    rel = item.relative_to(source)
    if ".migration-conflicts" in rel.parts:
        continue
    if item.is_dir():
        continue
    if item.is_symlink():
        skipped.append(f"{rel} (symlink)")
        continue

    destination = target / rel
    destination.parent.mkdir(parents=True, exist_ok=True)

    if rel == pathlib.Path("config.yaml") and destination.exists():
        skipped.append("config.yaml (persistent config preserved)")
        continue

    if not destination.exists():
        shutil.copy2(item, destination)
        migrated.append(str(rel))
        continue

    source_stat = item.stat()
    dest_stat = destination.stat()
    same_content_shape = source_stat.st_size == dest_stat.st_size and int(source_stat.st_mtime) == int(dest_stat.st_mtime)
    if same_content_shape:
        skipped.append(f"{rel} (already present)")
        continue

    if source_stat.st_mtime > dest_stat.st_mtime:
        backup_path = conflict_root / "replaced-targets" / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup_path)
        shutil.copy2(item, destination)
        replaced.append(str(rel))
    else:
        backup_path = conflict_root / "kept-targets" / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, backup_path)
        conflicts.append(str(rel))

if migrated:
    print("Migrated legacy files to /config/pymc-repeater: " + ", ".join(migrated))
if replaced:
    print("Replaced older persistent files with newer /data copies; previous files saved under " + str(conflict_root / "replaced-targets") + ": " + ", ".join(replaced))
if conflicts:
    print("Kept newer persistent files; older /data copies saved under " + str(conflict_root / "kept-targets") + ": " + ", ".join(conflicts))
if skipped:
    print("Skipped legacy files: " + ", ".join(skipped))
if not migrated and not replaced and not conflicts and not skipped:
    print("Legacy /data/pymc-repeater was empty; migration skipped.")
PY
)"

CONFIG_ACTION="$("${PYTHON_BIN}" - <<'PY'
import pathlib

import yaml

config_path = pathlib.Path("/config/pymc-repeater/config.yaml")
persistent_root = "/config/pymc-repeater"


def write_config(config):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = config_path.with_suffix(".yaml.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, default_flow_style=False, sort_keys=False)
    tmp_path.replace(config_path)


def default_config():
    return {
        "radio_type": "sx1262",
        "repeater": {
            "node_name": "pyMC Repeater",
            "mode": "forward",
            "latitude": 0.0,
            "longitude": 0.0,
            "country": "FR",
            "identity_file": f"{persistent_root}/identity.key",
            "owner_info": "",
            "cache_ttl": 3600,
            "max_flood_hops": 64,
            "use_score_for_tx": False,
            "score_threshold": 0.3,
            "send_advert_interval_hours": 10,
            "allow_discovery": True,
            "advert_rate_limit": {
                "enabled": True,
                "bucket_capacity": 2,
                "refill_tokens": 1,
                "refill_interval_seconds": 36000,
                "min_interval_seconds": 3600,
            },
            "advert_penalty_box": {
                "enabled": True,
                "violation_threshold": 2,
                "base_penalty_seconds": 21600,
                "penalty_multiplier": 2.0,
                "max_penalty_seconds": 86400,
                "violation_decay_seconds": 43200,
            },
            "advert_adaptive": {
                "enabled": True,
                "ewma_alpha": 0.1,
                "hysteresis_seconds": 300,
                "thresholds": {
                    "quiet_max": 0.05,
                    "normal_max": 0.20,
                    "busy_max": 0.50,
                    "normal": 1.0,
                    "busy": 5.0,
                    "congested": 15.0,
                },
            },
            "advert_dedupe": {
                "ttl_seconds": 120,
                "max_hashes": 10000,
            },
            "security": {
                "max_clients": 1,
                "admin_password": "change_me",
                "guest_password": "",
                "allow_read_only": False,
                "jwt_secret": "",
                "jwt_expiry_minutes": 60,
            },
        },
        "mesh": {
            "unscoped_flood_allow": True,
            "path_hash_mode": 0,
            "loop_detect": "minimal",
        },
        "identities": {
            "room_servers": [],
            "companions": [],
        },
        "ch341": {
            "vid": 0x1A86,
            "pid": 0x5512,
        },
        "radio": {
            "frequency": 869618000,
            "tx_power": 14,
            "bandwidth": 62500,
            "spreading_factor": 8,
            "coding_rate": 8,
            "preamble_length": 16,
            "sync_word": 18,
        },
        "kiss": {
            "port": "/dev/ttyUSB0",
            "baud_rate": 115200,
        },
        "pymc_usb": {
            "port": "/dev/ttyACM0",
            "baudrate": 921600,
            "lbt_enabled": True,
            "lbt_max_attempts": 5,
        },
        "pymc_tcp": {
            "host": "",
            "port": 5055,
            "token": "",
            "connect_timeout": 5.0,
            "lbt_enabled": True,
            "lbt_max_attempts": 5,
        },
        "sx1262": {
            "bus_id": 0,
            "cs_id": 0,
            "cs_pin": 21,
            "reset_pin": 18,
            "busy_pin": 20,
            "irq_pin": 16,
            "txen_pin": -1,
            "rxen_pin": -1,
            "txled_pin": -1,
            "rxled_pin": -1,
            "use_dio3_tcxo": False,
            "dio3_tcxo_voltage": 1.8,
            "use_dio2_rf": False,
            "is_waveshare": False,
        },
        "delays": {
            "tx_delay_factor": 1.0,
            "direct_tx_delay_factor": 0.5,
        },
        "duty_cycle": {
            "enforcement_enabled": False,
            "max_airtime_per_minute": 3600,
        },
        "storage": {
            "storage_dir": persistent_root,
            "retention": {
                "sqlite_cleanup_days": 31,
            },
        },
        "mqtt_brokers": {
            "iata_code": "PAR",
            "country": "FR",
            "status_interval": 300,
            "owner": "",
            "email": "",
            "brokers": [],
        },
        "mqtt": {},
        "glass": {
            "enabled": False,
            "base_url": "http://localhost:8080",
            "inform_interval_seconds": 30,
            "request_timeout_seconds": 10,
            "verify_tls": True,
            "api_token": "",
            "cert_store_dir": f"{persistent_root}/glass",
        },
        "http": {
            "host": "127.0.0.1",
            "port": 8001,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "web": {
            "web_path": "/opt/pymc_console/web/html",
            "cors_enabled": False,
        },
    }


if config_path.exists():
    print(f"Using existing pyMC Repeater config unchanged: {config_path}")
else:
    write_config(default_config())
    print(f"Created default pyMC Repeater config: {config_path}")

identity_path = config_path.parent / "identity.key"
if identity_path.exists():
    identity_path.chmod(0o600)
PY
)"

chmod -R u+rwX,g+rwX "${CONFIG_ROOT}" "${DATA_ROOT}"

while IFS= read -r line; do
  bashio::log.info "${line}"
done <<< "${MIGRATION_RESULT}"

while IFS= read -r line; do
  bashio::log.info "${line}"
done <<< "${CONFIG_ACTION}"
bashio::log.info "/etc/pymc_repeater/config.yaml -> ${CONFIG_PATH}."
bashio::log.info "/var/lib/pymc_repeater -> ${CONFIG_ROOT}."
bashio::log.info "Persistent pyMC Repeater data path is ${CONFIG_ROOT}."

PREFLIGHT_RESULT="$("${PYTHON_BIN}" - <<'PY'
import os
import pathlib
import socket
import sys

import yaml

config_path = pathlib.Path("/config/pymc-repeater/config.yaml")
with config_path.open("r", encoding="utf-8") as handle:
    config = yaml.safe_load(handle) or {}

radio_type = str(config.get("radio_type", "")).lower().strip()
disabled_types = {"", "none", "null", "disabled", "off", "no_radio"}
supported_types = {
    "sx1262",
    "sx1262_ch341",
    "kiss",
    "kiss-modem",
    "pymc_tcp",
    "pymc_usb",
}

if radio_type in disabled_types:
    print(f"Radio disabled by configuration (radio_type={config.get('radio_type')!r}); startup preflight skipped.")
    sys.exit(0)

if radio_type not in supported_types:
    print(
        f"Unsupported radio_type={config.get('radio_type')!r} in /config/pymc-repeater/config.yaml. "
        "Supported values: sx1262, sx1262_ch341, kiss, kiss-modem, pymc_tcp, pymc_usb, none."
    )
    sys.exit(1)

def require_mapping(section_name):
    section = config.get(section_name) or {}
    if not isinstance(section, dict):
        print(f"Configured radio_type={radio_type} requires {section_name}: to be a mapping in /config/pymc-repeater/config.yaml.")
        sys.exit(1)
    return section

def require_int(value, label, minimum=None, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        print(f"Configured radio_type={radio_type} requires integer {label}; got {value!r}.")
        sys.exit(1)
    if minimum is not None and number < minimum:
        print(f"Configured radio_type={radio_type} requires {label} >= {minimum}; got {number}.")
        sys.exit(1)
    if maximum is not None and number > maximum:
        print(f"Configured radio_type={radio_type} requires {label} <= {maximum}; got {number}.")
        sys.exit(1)
    return number

def require_serial_device(path_value, label):
    path = str(path_value or "").strip()
    if not path:
        print(f"Configured radio_type={radio_type} requires {label} in /config/pymc-repeater/config.yaml.")
        sys.exit(1)
    device = pathlib.Path(path)
    if not device.exists():
        print(
            f"Configured radio_type={radio_type} uses {label}={path}, but that serial device is not present "
            "inside the add-on container. Check the device path, prefer /dev/serial/by-id/..., and confirm "
            "Home Assistant exposes the USB/UART device to this add-on."
        )
        sys.exit(1)
    if not device.is_char_device():
        print(f"Configured radio_type={radio_type} uses {label}={path}, but it is not a character device.")
        sys.exit(1)
    if not os.access(path, os.R_OK | os.W_OK):
        print(
            f"Configured radio_type={radio_type} uses {label}={path}, but the add-on cannot read/write it. "
            "Check serial device permissions and the add-on USB/UART mapping."
        )
        sys.exit(1)
    return path

def require_tcp_endpoint(section):
    host = str(section.get("host", "")).strip()
    if not host:
        print("Configured radio_type=pymc_tcp requires pymc_tcp.host in /config/pymc-repeater/config.yaml.")
        sys.exit(1)
    port = require_int(section.get("port", 5055), "pymc_tcp.port", 1, 65535)
    timeout = float(section.get("connect_timeout", 5.0) or 5.0)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except socket.gaierror as exc:
        print(f"Configured radio_type=pymc_tcp host {host!r} could not be resolved: {exc}.")
        sys.exit(1)
    except TimeoutError as exc:
        print(f"Configured radio_type=pymc_tcp endpoint {host}:{port} timed out after {timeout}s: {exc}.")
        sys.exit(1)
    except OSError as exc:
        print(
            f"Configured radio_type=pymc_tcp endpoint {host}:{port} is not reachable: {exc}. "
            "Check the modem IP/hostname, port, firewall, and that pymc_usb TCP mode is running."
        )
        sys.exit(1)
    return host, port

sx1262_config = config.get("sx1262") or {}
if not isinstance(sx1262_config, dict):
    sx1262_config = {}

gpiochip = (
    sx1262_config.get("gpiochip")
    or sx1262_config.get("gpio_chip")
    or sx1262_config.get("gpio_chip_path")
    or sx1262_config.get("gpiochip_path")
    or "/dev/gpiochip0"
)

if radio_type == "sx1262" and gpiochip == "/dev/gpiochip0" and not os.path.exists(gpiochip):
    print(
        "Configured radio_type=sx1262 requires /dev/gpiochip0, but /dev/gpiochip0 is not "
        "available in this Home Assistant add-on container. Edit "
        "/config/pymc-repeater/config.yaml to use KISS/serial config or expose the GPIO device."
    )
    sys.exit(1)

if radio_type == "pymc_tcp":
    host, port = require_tcp_endpoint(require_mapping("pymc_tcp"))
    print(f"pymc_tcp endpoint reachable: {host}:{port}")

if radio_type == "pymc_usb":
    pymc_usb_config = require_mapping("pymc_usb")
    require_serial_device(pymc_usb_config.get("port"), "pymc_usb.port")
    require_int(pymc_usb_config.get("baudrate", 921600), "pymc_usb.baudrate", 1)

if radio_type in {"kiss", "kiss-modem"}:
    kiss_config = require_mapping("kiss")
    require_serial_device(kiss_config.get("port"), "kiss.port")
    require_int(kiss_config.get("baud_rate", 115200), "kiss.baud_rate", 1)

print("ok")
PY
)" || {
  bashio::log.fatal "${PREFLIGHT_RESULT}"
  exit 1
}

while IFS= read -r line; do
  if [ "${line}" != "ok" ]; then
    bashio::log.info "preflight | ${line}"
  fi
done <<< "${PREFLIGHT_RESULT}"
bashio::log.info "pyMC Repeater config preflight passed."
