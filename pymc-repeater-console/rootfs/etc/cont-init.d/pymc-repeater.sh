#!/usr/bin/with-contenv bashio
set -euo pipefail

CONFIG_ROOT="/config/pymc-repeater"
DATA_ROOT="/data/pymc-repeater"
ETC_ROOT="/etc/pymc_repeater"
VAR_ROOT="/var/lib/pymc_repeater"
CONFIG_PATH="${CONFIG_ROOT}/config.yaml"
OPTIONS_PATH="/data/options.json"
CONSOLE_WEB_PATH="/opt/pymc_console/web/html"

mkdir -p "${CONFIG_ROOT}" "${DATA_ROOT}"

if [ -e "${ETC_ROOT}" ] && [ ! -L "${ETC_ROOT}" ]; then
  rm -rf "${ETC_ROOT}"
fi
ln -sfn "${CONFIG_ROOT}" "${ETC_ROOT}"

if [ -e "${VAR_ROOT}" ] && [ ! -L "${VAR_ROOT}" ]; then
  rm -rf "${VAR_ROOT}"
fi
ln -sfn "${DATA_ROOT}" "${VAR_ROOT}"

CONFIG_ACTION="$(python3 - <<'PY'
import copy
import json
import pathlib
import sys

import yaml

options_path = pathlib.Path("/data/options.json")
config_root = pathlib.Path("/config/pymc-repeater")
config_path = config_root / "config.yaml"

with options_path.open("r", encoding="utf-8") as handle:
    options = json.load(handle)


def option_str(name, default=""):
    value = options.get(name)
    if value is None:
        return default
    value = str(value)
    return value if value != "" else default


def option_int(name, default):
    value = options.get(name)
    if value is None or value == "":
        return default
    return int(value)


def option_float(name, default):
    value = options.get(name)
    if value is None or value == "":
        return default
    return float(value)


def write_config(config):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = config_path.with_suffix(".yaml.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, default_flow_style=False, sort_keys=False)
    tmp_path.replace(config_path)


def enforce_wrapper_fields(config):
    if not isinstance(config, dict):
        raise TypeError("pyMC config must be a YAML mapping/object")

    config.setdefault("repeater", {})
    if "identity_key" not in config["repeater"]:
        config["repeater"].setdefault("identity_file", "/etc/pymc_repeater/identity.key")

    config.setdefault("storage", {})
    config["storage"]["storage_dir"] = "/var/lib/pymc_repeater"

    config.setdefault("http", {})
    config["http"]["host"] = "127.0.0.1"
    config["http"]["port"] = 8000

    config.setdefault("web", {})
    config["web"]["web_path"] = "/opt/pymc_console/web/html"

    config.setdefault("logging", {})
    config["logging"]["level"] = option_str("log_level", "info").upper()
    config["logging"].setdefault("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    return config


presets = {
    "EU_868": {
        "frequency": 869618000,
        "tx_power": 14,
        "bandwidth": 62500,
        "spreading_factor": 8,
        "coding_rate": 8,
        "preamble_length": 17,
        "sync_word": 13380,
    },
    "EU_868_LONG_RANGE": {
        "frequency": 869525000,
        "tx_power": 14,
        "bandwidth": 250000,
        "spreading_factor": 11,
        "coding_rate": 5,
        "preamble_length": 17,
        "sync_word": 13380,
    },
    "US_915": {
        "frequency": 910525000,
        "tx_power": 14,
        "bandwidth": 62500,
        "spreading_factor": 7,
        "coding_rate": 5,
        "preamble_length": 17,
        "sync_word": 13380,
    },
    "AU_915": {
        "frequency": 915800000,
        "tx_power": 14,
        "bandwidth": 250000,
        "spreading_factor": 10,
        "coding_rate": 5,
        "preamble_length": 17,
        "sync_word": 13380,
    },
    "NZ_917": {
        "frequency": 917375000,
        "tx_power": 14,
        "bandwidth": 62500,
        "spreading_factor": 7,
        "coding_rate": 5,
        "preamble_length": 17,
        "sync_word": 13380,
    },
}


def generated_config():
    preset_name = option_str("frequency_preset", "EU_868").upper()
    preset = dict(presets.get(preset_name, presets["EU_868"]))
    country = option_str("country", "FR").upper()
    radio = {
        "frequency": option_int("frequency_hz", preset["frequency"]),
        "tx_power": option_int("tx_power", preset["tx_power"]),
        "bandwidth": option_int("bandwidth", preset["bandwidth"]),
        "spreading_factor": option_int("spreading_factor", preset["spreading_factor"]),
        "coding_rate": option_int("coding_rate", preset["coding_rate"]),
        "preamble_length": preset["preamble_length"],
        "sync_word": preset["sync_word"],
    }
    map_region = option_str("map_region", option_str("region", "PAR")).upper()

    config = {
        "radio_type": option_str("radio_type", "sx1262"),
        "repeater": {
            "node_name": option_str("node_name", "pyMC Repeater"),
            "mode": "forward",
            "latitude": option_float("latitude", 0.0),
            "longitude": option_float("longitude", 0.0),
            "country": country,
            "identity_file": "/etc/pymc_repeater/identity.key",
            "owner_info": option_str("public_name", ""),
            "cache_ttl": 3600,
            "max_flood_hops": 64,
            "use_score_for_tx": False,
            "score_threshold": 0.3,
            "send_advert_interval_hours": 10,
            "allow_discovery": True,
            "security": {
                "max_clients": 1,
                "admin_password": option_str("admin_password", "change_me"),
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
        "radio": radio,
        "kiss": {
            "port": option_str("kiss_port", "/dev/ttyUSB0"),
            "baud_rate": option_int("kiss_baud_rate", 115200),
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
            "storage_dir": "/var/lib/pymc_repeater",
            "retention": {
                "sqlite_cleanup_days": 31,
            },
        },
        "mqtt": {
            "iata_code": map_region,
            "country": country,
            "status_interval": 300,
            "owner": "",
            "email": "",
            "brokers": [],
        },
        "glass": {
            "enabled": bool(options.get("glass_enabled", False)),
            "base_url": option_str("glass_base_url", "http://localhost:8080"),
            "inform_interval_seconds": option_int("glass_inform_interval_seconds", 30),
            "request_timeout_seconds": 10,
            "verify_tls": True,
            "api_token": "",
            "cert_store_dir": "/etc/pymc_repeater/glass",
        },
        "http": {
            "host": "127.0.0.1",
            "port": 8000,
        },
        "logging": {
            "level": option_str("log_level", "info").upper(),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "web": {
            "web_path": "/opt/pymc_console/web/html",
            "cors_enabled": False,
        },
    }
    return enforce_wrapper_fields(config)


raw_config = option_str("config_yaml", "").strip()
if raw_config:
    try:
        config = yaml.safe_load(raw_config) or {}
    except Exception as exc:
        print(f"Invalid config_yaml option: {exc}", file=sys.stderr)
        raise
    write_config(enforce_wrapper_fields(config))
    action = "wrote config_yaml option to persistent config"
elif config_path.exists():
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    enforced_config = enforce_wrapper_fields(copy.deepcopy(config))
    if enforced_config != config:
        write_config(enforced_config)
        action = "reused existing persistent config and updated wrapper runtime fields"
    else:
        action = "reused existing persistent config"
else:
    write_config(generated_config())
    action = "created persistent config from add-on options"

identity_path = config_root / "identity.key"
if identity_path.exists():
    identity_path.chmod(0o600)

print(action)
PY
)"

chmod -R u+rwX,g+rwX "${CONFIG_ROOT}" "${DATA_ROOT}"

bashio::log.info "${CONFIG_ACTION}: /etc/pymc_repeater/config.yaml -> ${CONFIG_PATH}."
bashio::log.info "Persistent pyMC Repeater data path is /var/lib/pymc_repeater -> ${DATA_ROOT}."

PREFLIGHT_RESULT="$(python3 - <<'PY'
import os
import pathlib
import sys

import yaml

config_path = pathlib.Path("/config/pymc-repeater/config.yaml")
with config_path.open("r", encoding="utf-8") as handle:
    config = yaml.safe_load(handle) or {}

radio_type = str(config.get("radio_type", "")).lower()
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
        "Configured radio_type=sx1262 requires /dev/gpiochip0, but this device is not available "
        "in the Home Assistant add-on container. Use KISS/serial config or expose the GPIO device."
    )
    sys.exit(1)

print("ok")
PY
)" || {
  bashio::log.fatal "${PREFLIGHT_RESULT}"
  exit 1
}

bashio::log.info "pyMC Repeater config preflight passed."
