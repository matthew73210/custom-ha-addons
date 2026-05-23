from __future__ import annotations

import contextlib
import io
import sys
import types
from pathlib import Path

from helpers import ADDON_ROOT, CI_SAFE_CONFIG, CONT_INIT_SCRIPT


REMOVED_HA_OPTION_REFERENCES = {
    "/data/options.json",
    "bashio::config",
    "config_yaml",
    "frequency_hz",
    "frequency_preset",
    "glass_enabled",
    "glass_inform_interval_seconds",
    "kiss_baud_rate",
    "kiss_port",
    "map_region",
    "option_str",
    "option_int",
    "option_bool",
    "public_name",
    "pymc_tcp_connect_timeout",
    "pymc_tcp_host",
    "pymc_tcp_lbt_enabled",
    "pymc_tcp_lbt_max_attempts",
    "pymc_tcp_port",
    "pymc_tcp_token",
}

DEFAULT_EU_RADIO_VALUES = {
    "frequency": 869618000,
    "bandwidth": 62500,
    "spreading_factor": 8,
    "coding_rate": 8,
    "sync_word": 18,
    "preamble_length": 16,
    "tx_power": 14,
}

OLD_HOME_ASSISTANT_RUNTIME_OPTIONS = {
    "node_name",
    "public_name",
    "latitude",
    "longitude",
    "country",
    "radio_type",
    "map_region",
    "frequency_preset",
    "frequency_hz",
    "tx_power",
    "bandwidth",
    "spreading_factor",
    "coding_rate",
    "sync_word",
    "preamble_length",
    "kiss_port",
    "kiss_baud_rate",
    "pymc_tcp_host",
    "pymc_tcp_port",
    "pymc_tcp_token",
    "pymc_tcp_connect_timeout",
    "pymc_tcp_lbt_enabled",
    "pymc_tcp_lbt_max_attempts",
    "admin_password",
    "glass_enabled",
    "glass_base_url",
    "glass_inform_interval_seconds",
    "log_level",
    "config_yaml",
}


def extract_config_action() -> str:
    script = CONT_INIT_SCRIPT.read_text(encoding="utf-8")
    start_marker = 'CONFIG_ACTION="$("${PYTHON_BIN}" - <<\'PY\'\n'
    start = script.index(start_marker) + len(start_marker)
    end = script.index("\nPY\n)\"", start)
    return script[start:end]


def simple_yaml_dump(value, indent=0):
    lines = []
    prefix = " " * indent
    for key, item in value.items():
        if isinstance(item, dict):
            lines.append(f"{prefix}{key}:")
            lines.extend(simple_yaml_dump(item, indent + 2))
        elif isinstance(item, list):
            lines.append(f"{prefix}{key}: []")
        elif item is True:
            lines.append(f"{prefix}{key}: true")
        elif item is False:
            lines.append(f"{prefix}{key}: false")
        elif item == "":
            lines.append(f'{prefix}{key}: ""')
        else:
            lines.append(f"{prefix}{key}: {item}")
    return lines


def run_config_action(config_path: Path) -> str:
    code = extract_config_action()
    code = code.replace(
        'pathlib.Path("/config/pymc-repeater/config.yaml")',
        f"pathlib.Path({str(config_path)!r})",
    )
    code = code.replace(
        'persistent_root = "/config/pymc-repeater"',
        f"persistent_root = {str(config_path.parent)!r}",
    )

    def safe_dump(value, stream=None, **kwargs):
        text = "\n".join(simple_yaml_dump(value)) + "\n"
        if stream is not None:
            stream.write(text)
            return None
        return text

    previous_yaml = sys.modules.get("yaml")
    sys.modules["yaml"] = types.SimpleNamespace(safe_dump=safe_dump)
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {})
    finally:
        if previous_yaml is None:
            sys.modules.pop("yaml", None)
        else:
            sys.modules["yaml"] = previous_yaml
    return output.getvalue()


def test_existing_persistent_config_is_preserved_unchanged(tmp_path):
    config_path = tmp_path / "pymc-repeater/config.yaml"
    config_path.parent.mkdir()
    config_path.write_text("sentinel: keep-me\n", encoding="utf-8")

    before = config_path.read_text(encoding="utf-8")
    output = run_config_action(config_path)

    assert config_path.read_text(encoding="utf-8") == before
    assert "unchanged" in output


def test_missing_persistent_config_is_created_once(tmp_path):
    config_path = tmp_path / "pymc-repeater/config.yaml"

    first_output = run_config_action(config_path)
    first_content = config_path.read_text(encoding="utf-8")
    second_output = run_config_action(config_path)

    assert "Created default pyMC Repeater config" in first_output
    assert "radio_type: sx1262" in first_content
    assert config_path.read_text(encoding="utf-8") == first_content
    assert "unchanged" in second_output


def test_default_config_contains_eu_radio_defaults_once(tmp_path):
    config_path = tmp_path / "pymc-repeater/config.yaml"

    run_config_action(config_path)
    first_content = config_path.read_text(encoding="utf-8")
    for key, value in DEFAULT_EU_RADIO_VALUES.items():
        assert f"  {key}: {value}\n" in first_content

    user_content = first_content.replace("  tx_power: 14\n", "  tx_power: 7\n")
    config_path.write_text(user_content, encoding="utf-8")
    run_config_action(config_path)

    assert config_path.read_text(encoding="utf-8") == user_content


def test_default_config_contains_pymc_usb_and_tcp_sections(tmp_path):
    config_path = tmp_path / "pymc-repeater/config.yaml"

    run_config_action(config_path)
    content = config_path.read_text(encoding="utf-8")

    assert "pymc_usb:\n" in content
    assert "  port: /dev/ttyACM0\n" in content
    assert "  baudrate: 921600\n" in content
    assert "pymc_tcp:\n" in content
    assert '  host: ""\n' in content
    assert "  port: 5055\n" in content
    assert "  connect_timeout: 5.0\n" in content
    assert "  lbt_enabled: true\n" in content
    assert "  lbt_max_attempts: 5\n" in content


def test_removed_home_assistant_runtime_options_are_not_referenced_by_startup_scripts():
    startup_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ADDON_ROOT / "rootfs/etc").rglob("*")
        if path.is_file()
    )

    for removed in REMOVED_HA_OPTION_REFERENCES:
        assert removed not in startup_text


def test_addon_config_has_no_home_assistant_runtime_options_or_schema():
    config_yaml = (ADDON_ROOT / "config.yaml").read_text(encoding="utf-8")
    assert "\noptions:" not in config_yaml
    assert "\nschema:" not in config_yaml
    for option_key in OLD_HOME_ASSISTANT_RUNTIME_OPTIONS:
        assert f"{option_key}:" not in config_yaml


def test_sx1262_gpio_runtime_guard_remains_in_startup_script():
    startup_text = CONT_INIT_SCRIPT.read_text(encoding="utf-8")
    assert 'radio_type == "sx1262"' in startup_text
    assert 'gpiochip == "/dev/gpiochip0"' in startup_text
    assert "Configured radio_type=sx1262 requires /dev/gpiochip0" in startup_text


def test_ci_safe_contract_config_does_not_use_sx1262_default():
    config_yaml = CI_SAFE_CONFIG.read_text(encoding="utf-8")
    assert "radio_type: sx1262" not in config_yaml
    assert "radio_type: none" in config_yaml
    assert "/dev/gpiochip0" not in config_yaml
