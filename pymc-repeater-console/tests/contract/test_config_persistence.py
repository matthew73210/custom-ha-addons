from __future__ import annotations

import contextlib
import io
import sys
import types
from pathlib import Path

from helpers import ADDON_ROOT, CI_SAFE_CONFIG, CONT_INIT_SCRIPT, RUN_SCRIPT


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


def extract_preflight_action() -> str:
    script = CONT_INIT_SCRIPT.read_text(encoding="utf-8")
    start_marker = 'PREFLIGHT_RESULT="$("${PYTHON_BIN}" - <<\'PY\'\n'
    start = script.index(start_marker) + len(start_marker)
    end = script.index("\nPY\n)\" || {", start)
    return script[start:end]


class SilentFakeSerial:
    def __init__(self):
        self.closed = False
        self.opened = False
        self.reset_input_buffer_called = False
        self.writes: list[bytes] = []
        self.in_waiting = 0

    def open(self):
        self.opened = True

    def close(self):
        self.closed = True

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def read(self, _size: int = 1) -> bytes:
        return b""

    def reset_input_buffer(self):
        self.reset_input_buffer_called = True


class FastFakeTime:
    def __init__(self):
        self.now = 0.0

    def time(self) -> float:
        self.now += 0.25
        return self.now

    def sleep(self, seconds: float):
        self.now += seconds


def pymc_usb_runtime_config(device_path: Path, preflight: str | None = None) -> dict:
    config = {
        "radio_type": "pymc_usb",
        "pymc_usb": {
            "port": str(device_path),
            "baudrate": 921600,
        },
    }
    if preflight is not None:
        config["pymc_usb_preflight"] = preflight
    return config


def run_preflight_action(
    tmp_path: Path,
    config: dict,
    serial_factory=SilentFakeSerial,
) -> tuple[int, str, list[SilentFakeSerial]]:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("ignored: true\n", encoding="utf-8")

    code = extract_preflight_action()
    code = code.replace(
        'pathlib.Path("/config/pymc-repeater/config.yaml")',
        f"pathlib.Path({str(config_path)!r})",
    )

    serial_instances: list[SilentFakeSerial] = []

    def create_serial():
        instance = serial_factory()
        serial_instances.append(instance)
        return instance

    previous_yaml = sys.modules.get("yaml")
    previous_serial = sys.modules.get("serial")
    previous_time = sys.modules.get("time")
    original_is_char_device = Path.is_char_device

    device_path = Path(config.get("pymc_usb", {}).get("port", tmp_path / "ttyACM0"))
    device_path.parent.mkdir(parents=True, exist_ok=True)
    device_path.touch(exist_ok=True)

    def fake_is_char_device(self):
        if str(self) == str(device_path):
            return True
        return original_is_char_device(self)

    sys.modules["yaml"] = types.SimpleNamespace(safe_load=lambda _handle: config)
    sys.modules["serial"] = types.SimpleNamespace(Serial=create_serial)
    sys.modules["time"] = FastFakeTime()
    Path.is_char_device = fake_is_char_device

    output = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(output):
            try:
                exec(code, {})
            except SystemExit as exc:
                exit_code = exc.code if isinstance(exc.code, int) else 1
    finally:
        Path.is_char_device = original_is_char_device
        if previous_yaml is None:
            sys.modules.pop("yaml", None)
        else:
            sys.modules["yaml"] = previous_yaml
        if previous_serial is None:
            sys.modules.pop("serial", None)
        else:
            sys.modules["serial"] = previous_serial
        if previous_time is None:
            sys.modules.pop("time", None)
        else:
            sys.modules["time"] = previous_time

    return exit_code, output.getvalue(), serial_instances


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


def test_backend_uses_real_persistent_config_path_for_saves():
    run_script = RUN_SCRIPT.read_text(encoding="utf-8")
    assert 'CONFIG_PATH="/config/pymc-repeater/config.yaml"' in run_script
    assert 'export PYMC_REPEATER_CONFIG="${CONFIG_PATH}"' in run_script
    assert '--config "${CONFIG_PATH}"' in run_script


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


def test_addon_config_only_declares_64_bit_architectures():
    config_yaml = (ADDON_ROOT / "config.yaml").read_text(encoding="utf-8")
    assert "  - aarch64\n" in config_yaml
    assert "  - amd64\n" in config_yaml
    for removed_arch in ("armhf", "armv7", "i386"):
        assert removed_arch not in config_yaml


def test_sx1262_gpio_runtime_guard_remains_in_startup_script():
    startup_text = CONT_INIT_SCRIPT.read_text(encoding="utf-8")
    assert 'radio_type == "sx1262"' in startup_text
    assert 'gpiochip == "/dev/gpiochip0"' in startup_text
    assert "Configured radio_type=sx1262 requires /dev/gpiochip0" in startup_text


def test_radio_preflight_covers_bad_runtime_backends():
    startup_text = CONT_INIT_SCRIPT.read_text(encoding="utf-8")
    assert "import os" in startup_text
    assert "os.access" in startup_text
    expected_diagnostics = [
        "Unsupported radio_type",
        "pymc_tcp.host",
        "pymc_tcp.port",
        "could not be resolved",
        "timed out",
        "is not reachable",
        "pymc_usb.port",
        "kiss.port",
        "not a character device",
        "cannot read/write",
    ]
    for diagnostic in expected_diagnostics:
        assert diagnostic in startup_text


def test_pymc_usb_preflight_warn_mode_continues_when_serial_returns_zero_bytes(tmp_path):
    device_path = tmp_path / "ttyACM0"
    config = pymc_usb_runtime_config(device_path, preflight="warn")

    exit_code, output, serial_instances = run_preflight_action(tmp_path, config)

    assert exit_code == 0
    assert "pymc_usb selected: radio_type=pymc_usb" in output
    assert f"port={device_path}" in output
    assert "baudrate=921600" in output
    assert "preflight=warn" in output
    assert "DTR=False RTS=False" in output
    assert "pymc_usb preflight TX GET_VERSION: aa 70 00 00 94 14 (6 bytes)" in output
    assert "pymc_usb preflight TX PING: aa ff 00 00 ff 03 (6 bytes)" in output
    assert "bytes_read=0 non_sync_bytes=0" in output
    assert "pymc_usb preflight warning:" in output
    assert "Continuing startup because pymc_usb_preflight=warn" in output
    assert "ok" in output.splitlines()
    assert len(serial_instances) == 1
    assert serial_instances[0].opened is True
    assert serial_instances[0].closed is True
    assert serial_instances[0].reset_input_buffer_called is True
    assert serial_instances[0].writes == [
        bytes.fromhex("aa 70 00 00 94 14"),
        bytes.fromhex("aa ff 00 00 ff 03"),
    ]
    assert serial_instances[0].dtr is False
    assert serial_instances[0].rts is False


def test_pymc_usb_preflight_fatal_mode_exits_when_serial_returns_zero_bytes(tmp_path):
    device_path = tmp_path / "ttyACM0"
    config = pymc_usb_runtime_config(device_path, preflight="fatal")

    exit_code, output, serial_instances = run_preflight_action(tmp_path, config)

    assert exit_code == 1
    assert "pymc_usb preflight TX GET_VERSION: aa 70 00 00 94 14 (6 bytes)" in output
    assert "pymc_usb preflight TX PING: aa ff 00 00 ff 03 (6 bytes)" in output
    assert "Configured radio_type=pymc_usb opened the serial device" in output
    assert "no valid pymc-usb GET_VERSION or PING response was decoded" in output
    assert "ok" not in output.splitlines()
    assert len(serial_instances) == 1
    assert serial_instances[0].closed is True


def test_pymc_usb_preflight_off_mode_skips_wrapper_protocol_probe(tmp_path):
    device_path = tmp_path / "ttyACM0"
    config = pymc_usb_runtime_config(device_path, preflight="off")
    serial_open_attempts = []

    def fail_if_serial_opens():
        serial_open_attempts.append(True)
        raise AssertionError("off mode must not open serial for wrapper protocol preflight")

    exit_code, output, serial_instances = run_preflight_action(tmp_path, config, fail_if_serial_opens)

    assert exit_code == 0
    assert "preflight=off" in output
    assert "pymc_usb protocol preflight disabled by pymc_usb_preflight=off" in output
    assert "pymc_usb opening serial for protocol preflight" not in output
    assert "pymc_usb preflight TX GET_VERSION" not in output
    assert serial_open_attempts == []
    assert serial_instances == []
    assert "ok" in output.splitlines()


def test_existing_pymc_usb_config_defaults_to_warning_preflight(tmp_path):
    device_path = tmp_path / "ttyACM0"
    config = pymc_usb_runtime_config(device_path)

    exit_code, output, serial_instances = run_preflight_action(tmp_path, config)

    assert exit_code == 0
    assert "preflight=warn" in output
    assert "Continuing startup because pymc_usb_preflight=warn" in output
    assert len(serial_instances) == 1
    assert serial_instances[0].closed is True


def test_upstream_launch_path_remains_after_warning_preflight_failure(tmp_path):
    device_path = tmp_path / "ttyACM0"
    config = pymc_usb_runtime_config(device_path, preflight="warn")

    exit_code, output, _serial_instances = run_preflight_action(tmp_path, config)
    run_script = RUN_SCRIPT.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "pymc_usb preflight warning:" in output
    assert "ok" in output.splitlines()
    assert 'CONFIG_PATH="/config/pymc-repeater/config.yaml"' in run_script
    assert 'export PYMC_REPEATER_CONFIG="${CONFIG_PATH}"' in run_script
    assert '"${PYTHON_BIN}" -m repeater.main --config "${CONFIG_PATH}"' in run_script


def test_ci_safe_contract_config_does_not_use_sx1262_default():
    config_yaml = CI_SAFE_CONFIG.read_text(encoding="utf-8")
    assert "radio_type: sx1262" not in config_yaml
    assert "radio_type: none" in config_yaml
    assert "/dev/gpiochip0" not in config_yaml
