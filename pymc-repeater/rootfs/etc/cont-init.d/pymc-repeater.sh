#!/usr/bin/with-contenv bashio
set -euo pipefail

CONFIG_ROOT="/config/pymc-repeater"
DATA_ROOT="/data/pymc-repeater"
ETC_ROOT="/etc/pymc_repeater"
VAR_ROOT="/var/lib/pymc_repeater"
CONFIG_PATH="${CONFIG_ROOT}/config.yaml"
OPTIONS_PATH="/data/options.json"

mkdir -p "${CONFIG_ROOT}" "${DATA_ROOT}"

if [ -e "${ETC_ROOT}" ] && [ ! -L "${ETC_ROOT}" ]; then
  rm -rf "${ETC_ROOT}"
fi
ln -sfn "${CONFIG_ROOT}" "${ETC_ROOT}"

if [ -e "${VAR_ROOT}" ] && [ ! -L "${VAR_ROOT}" ]; then
  rm -rf "${VAR_ROOT}"
fi
ln -sfn "${DATA_ROOT}" "${VAR_ROOT}"

python3 - <<'PY'
import json
import pathlib
import sys

import yaml

options_path = pathlib.Path("/data/options.json")
config_path = pathlib.Path("/config/pymc-repeater/config.yaml")
config_root = pathlib.Path("/config/pymc-repeater")

with options_path.open("r", encoding="utf-8") as handle:
    options = json.load(handle)

log_level = str(options.get("log_level") or "info").upper()
radio_type = str(options.get("radio_type") or "sx1262")
region = str(options.get("region") or "PAR").upper()
admin_password = str(options.get("admin_password") or "change_me")

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

raw_config = str(options.get("config_yaml") or "").strip()
if raw_config:
    try:
        config = yaml.safe_load(raw_config) or {}
    except Exception as exc:
        print(f"Invalid config_yaml option: {exc}", file=sys.stderr)
        raise
    if not isinstance(config, dict):
        raise TypeError("config_yaml must contain a YAML mapping/object")
else:
    preset_name = str(options.get("frequency_preset") or "EU_868")
    radio = dict(presets.get(preset_name, presets["EU_868"]))
    config = {
        "radio_type": radio_type,
        "repeater": {
            "node_name": f"pyMC Repeater {region}",
            "mode": "forward",
            "latitude": 0.0,
            "longitude": 0.0,
            "identity_file": "/etc/pymc_repeater/identity.key",
            "owner_info": "",
            "cache_ttl": 3600,
            "max_flood_hops": 64,
            "use_score_for_tx": False,
            "score_threshold": 0.3,
            "send_advert_interval_hours": 10,
            "allow_discovery": True,
            "security": {
                "max_clients": 1,
                "admin_password": admin_password,
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
            "port": options.get("kiss_port") or "/dev/ttyUSB0",
            "baud_rate": int(options.get("kiss_baud_rate") or 115200),
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
            "iata_code": region,
            "status_interval": 300,
            "owner": "",
            "email": "",
            "brokers": [],
        },
        "glass": {
            "enabled": False,
            "base_url": "http://localhost:8080",
            "inform_interval_seconds": 30,
            "request_timeout_seconds": 10,
            "verify_tls": True,
            "api_token": "",
            "cert_store_dir": "/etc/pymc_repeater/glass",
        },
        "http": {
            "host": "0.0.0.0",
            "port": 8000,
        },
        "logging": {
            "level": log_level,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "web": {
            "cors_enabled": False,
        },
    }

config.setdefault("repeater", {})
config["repeater"].setdefault("identity_file", "/etc/pymc_repeater/identity.key")
config["repeater"].setdefault("security", {})
config["repeater"]["security"].setdefault("admin_password", admin_password)
config.setdefault("storage", {})
config["storage"]["storage_dir"] = "/var/lib/pymc_repeater"
config.setdefault("http", {})
config["http"]["host"] = "0.0.0.0"
config["http"]["port"] = 8000
config.setdefault("logging", {})
config["logging"]["level"] = log_level
config["logging"].setdefault("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

config_path.parent.mkdir(parents=True, exist_ok=True)
tmp_path = config_path.with_suffix(".yaml.tmp")
with tmp_path.open("w", encoding="utf-8") as handle:
    yaml.safe_dump(config, handle, default_flow_style=False, sort_keys=False)
tmp_path.replace(config_path)

identity_path = config_root / "identity.key"
if identity_path.exists():
    identity_path.chmod(0o600)
PY

chmod -R u+rwX,g+rwX "${CONFIG_ROOT}" "${DATA_ROOT}"

bashio::log.info "Generated pyMC Repeater config at /etc/pymc_repeater/config.yaml -> ${CONFIG_PATH}."
bashio::log.info "Persistent pyMC Repeater data path is /var/lib/pymc_repeater -> ${DATA_ROOT}."
