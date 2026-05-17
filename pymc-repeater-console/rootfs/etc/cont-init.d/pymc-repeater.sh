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
ln -sfn "${CONFIG_ROOT}" "${VAR_ROOT}"

MIGRATION_RESULT="$(python3 - <<'PY'
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

CONFIG_ACTION="$(python3 - <<'PY'
import copy
import json
import pathlib
import sys

import yaml

options_path = pathlib.Path("/data/options.json")
config_root = pathlib.Path("/config/pymc-repeater")
config_path = config_root / "config.yaml"
persistent_root = "/config/pymc-repeater"
identity_file = f"{persistent_root}/identity.key"

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
    config["repeater"]["identity_file"] = identity_file

    config.setdefault("storage", {})
    config["storage"]["storage_dir"] = persistent_root

    config.setdefault("http", {})
    config["http"]["host"] = "127.0.0.1"
    config["http"]["port"] = 8001

    config.setdefault("web", {})
    config["web"]["web_path"] = "/opt/pymc_console/web/html"

    config.setdefault("logging", {})
    config["logging"]["level"] = option_str("log_level", "info").upper()
    config["logging"].setdefault("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    return config


def config_path_string(parts):
    return ".".join(str(part) for part in parts)


def default_leaf_paths(value, prefix):
    if isinstance(value, dict) and value:
        paths = []
        for key, child in value.items():
            paths.extend(default_leaf_paths(child, prefix + [key]))
        return paths
    return [config_path_string(prefix)]


def add_default(mapping, key, value, path, added_defaults):
    if key not in mapping:
        mapping[key] = copy.deepcopy(value)
        added_defaults.extend(default_leaf_paths(value, path + [key]))


def merge_missing(config, defaults, added_defaults=None, path=None):
    if not isinstance(config, dict):
        return config

    if added_defaults is None:
        added_defaults = []
    if path is None:
        path = []

    for key, default_value in defaults.items():
        if key not in config:
            config[key] = copy.deepcopy(default_value)
            added_defaults.extend(default_leaf_paths(default_value, path + [key]))
        elif isinstance(config[key], dict) and isinstance(default_value, dict):
            merge_missing(config[key], default_value, added_defaults, path + [key])
    return config


def normalize_mqtt_config(config, added_defaults=None):
    if added_defaults is None:
        added_defaults = []

    country = option_str("country", "FR").upper()
    map_region = option_str("map_region", option_str("region", "PAR")).upper()

    add_default(config, "mqtt_brokers", {}, [], added_defaults)
    mqtt_brokers = config.get("mqtt_brokers")
    if isinstance(mqtt_brokers, dict):
        add_default(mqtt_brokers, "iata_code", map_region, ["mqtt_brokers"], added_defaults)
        add_default(mqtt_brokers, "country", country, ["mqtt_brokers"], added_defaults)
        add_default(mqtt_brokers, "status_interval", 300, ["mqtt_brokers"], added_defaults)
        add_default(mqtt_brokers, "owner", "", ["mqtt_brokers"], added_defaults)
        add_default(mqtt_brokers, "email", "", ["mqtt_brokers"], added_defaults)
        add_default(mqtt_brokers, "brokers", [], ["mqtt_brokers"], added_defaults)

    mqtt = config.get("mqtt")
    if isinstance(mqtt, dict) and mqtt:
        add_default(mqtt, "enabled", False, ["mqtt"], added_defaults)
        add_default(mqtt, "broker", "", ["mqtt"], added_defaults)
        add_default(mqtt, "port", 1883, ["mqtt"], added_defaults)
        add_default(mqtt, "username", None, ["mqtt"], added_defaults)
        add_default(mqtt, "password", None, ["mqtt"], added_defaults)
        add_default(mqtt, "use_websockets", False, ["mqtt"], added_defaults)
        add_default(mqtt, "tls", None, ["mqtt"], added_defaults)
        add_default(mqtt, "base_topic", None, ["mqtt"], added_defaults)
    elif "mqtt" not in config:
        config["mqtt"] = {}
        added_defaults.append("mqtt")

    return config


def carry_legacy_mqtt_metadata(config):
    mqtt = config.get("mqtt")
    mqtt_brokers = config.get("mqtt_brokers")
    if not isinstance(mqtt, dict) or not mqtt or not isinstance(mqtt_brokers, dict):
        return config

    legacy_key_map = {
        "iata_code": "iata_code",
        "country": "country",
        "status_interval": "status_interval",
        "owner": "owner",
        "email": "email",
    }
    for legacy_key, broker_key in legacy_key_map.items():
        if legacy_key in mqtt and mqtt[legacy_key] not in (None, ""):
            mqtt_brokers[broker_key] = mqtt[legacy_key]

    return config


def normalize_known_config_types(config, defaults, added_defaults=None):
    if added_defaults is None:
        added_defaults = []

    repeater = config.setdefault("repeater", {})
    default_repeater = defaults.get("repeater", {})

    for section in ("advert_rate_limit", "advert_penalty_box", "advert_adaptive", "advert_dedupe"):
        if not isinstance(repeater.get(section), dict):
            repeater[section] = copy.deepcopy(default_repeater.get(section, {}))
            added_defaults.extend(default_leaf_paths(repeater[section], ["repeater", section]))

    adaptive = repeater.setdefault("advert_adaptive", {})
    if not isinstance(adaptive.get("thresholds"), dict):
        adaptive["thresholds"] = copy.deepcopy(
            default_repeater.get("advert_adaptive", {}).get("thresholds", {})
        )
        added_defaults.extend(default_leaf_paths(adaptive["thresholds"], ["repeater", "advert_adaptive", "thresholds"]))

    return config


def apply_wrapper_defaults(config):
    had_mqtt_brokers = "mqtt_brokers" in config
    added_defaults = []
    defaults = generated_config()
    config = merge_missing(config, defaults, added_defaults)
    if not had_mqtt_brokers:
        carry_legacy_mqtt_metadata(config)
    normalize_known_config_types(config, defaults, added_defaults)
    normalize_mqtt_config(config, added_defaults)
    return enforce_wrapper_fields(config), sorted(set(added_defaults))


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
            "identity_file": identity_file,
            "owner_info": option_str("public_name", ""),
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
            "storage_dir": persistent_root,
            "retention": {
                "sqlite_cleanup_days": 31,
            },
        },
        "mqtt_brokers": {
            "iata_code": map_region,
            "country": country,
            "status_interval": 300,
            "owner": "",
            "email": "",
            "brokers": [],
        },
        "mqtt": {},
        "glass": {
            "enabled": bool(options.get("glass_enabled", False)),
            "base_url": option_str("glass_base_url", "http://localhost:8080"),
            "inform_interval_seconds": option_int("glass_inform_interval_seconds", 30),
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
            "level": option_str("log_level", "info").upper(),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "web": {
            "web_path": "/opt/pymc_console/web/html",
            "cors_enabled": False,
        },
    }
    normalize_mqtt_config(config)
    return enforce_wrapper_fields(config)


raw_config = option_str("config_yaml", "").strip()
if raw_config:
    try:
        config = yaml.safe_load(raw_config) or {}
    except Exception as exc:
        print(f"Invalid config_yaml option: {exc}", file=sys.stderr)
        raise
    enforced_config, added_defaults = apply_wrapper_defaults(config)
    write_config(enforced_config)
    action = "wrote config_yaml option to persistent config and merged missing defaults"
elif config_path.exists():
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    enforced_config, added_defaults = apply_wrapper_defaults(copy.deepcopy(config))
    if enforced_config != config:
        write_config(enforced_config)
        action = "reused existing persistent config and merged missing defaults/runtime fields"
    else:
        action = "reused existing persistent config"
else:
    write_config(generated_config())
    action = "created persistent config from add-on options"
    added_defaults = []

identity_path = config_root / "identity.key"
if identity_path.exists():
    identity_path.chmod(0o600)

print(action)
if added_defaults:
    print("Added default config keys: " + ", ".join(added_defaults))
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
        "Configured radio_type=sx1262 requires /dev/gpiochip0, but /dev/gpiochip0 is not "
        "available in this Home Assistant add-on container. Use KISS/serial config or expose "
        "the GPIO device."
    )
    sys.exit(1)

print("ok")
PY
)" || {
  bashio::log.fatal "${PREFLIGHT_RESULT}"
  exit 1
}

bashio::log.info "pyMC Repeater config preflight passed."
