from __future__ import annotations

import re

from helpers import ADDON_ROOT


PYMC_USB_DOC = ADDON_ROOT / "docs/PYMC_USB.md"
README = ADDON_ROOT / "README.md"
CONFIG_YAML = ADDON_ROOT / "config.yaml"


def read(path):
    return path.read_text(encoding="utf-8")


def yaml_blocks(markdown: str) -> list[str]:
    return re.findall(r"```yaml\n(.*?)\n```", markdown, flags=re.DOTALL)


def test_pymc_usb_docs_describe_both_transport_modes():
    doc = read(PYMC_USB_DOC)
    assert "## pymc_usb transport modes" in doc
    assert "### A. Local USB serial mode" in doc
    assert "### B. TCP/IP mode" in doc
    assert "USB\" in `pymc_usb` is the protocol/device family name" in doc
    assert "pymc_tcp.host" in doc
    assert "pymc_tcp.port" in doc


def test_pymc_usb_local_serial_example_matches_upstream_schema():
    doc = read(PYMC_USB_DOC)
    blocks = yaml_blocks(doc)
    local = next(block for block in blocks if "radio_type: pymc_usb" in block)

    assert "pymc_usb:" in local
    assert "  port: /dev/serial/by-id/usb-example-pymc-radio" in local
    assert "  baudrate: 921600" in local
    assert "  lbt_enabled: true" in local
    assert "  lbt_max_attempts: 5" in local
    assert "pymc_tcp:" not in local


def test_pymc_usb_tcp_ip_example_uses_upstream_pymc_tcp_schema():
    doc = read(PYMC_USB_DOC)
    blocks = yaml_blocks(doc)
    tcp = next(block for block in blocks if "radio_type: pymc_tcp" in block)

    assert "pymc_tcp:" in tcp
    assert "  host: 192.168.1.49" in tcp
    assert "  port: 5055" in tcp
    assert "  token: \"\"" in tcp
    assert "  connect_timeout: 5.0" in tcp
    assert "  lbt_enabled: true" in tcp
    assert "  lbt_max_attempts: 5" in tcp
    assert "baudrate" not in tcp
    assert "pymc_usb:" not in tcp


def test_readme_points_users_to_config_file_for_pymc_usb_transport():
    readme = read(README)
    assert "## pymc_usb transport modes" in readme
    assert "radio_type: pymc_usb" in readme
    assert "radio_type: pymc_tcp" in readme
    assert "/config/pymc-repeater/config.yaml" in readme
    assert "Do not put `host`, `ip`, `tcp`, `socket`, `url`, or serial-over-TCP keys under `pymc_usb`" in readme


def test_home_assistant_config_does_not_add_pymc_usb_transport_options():
    config = read(CONFIG_YAML)
    assert "\noptions:" not in config
    assert "\nschema:" not in config

    forbidden = [
        "pymc_usb_port",
        "pymc_usb_baudrate",
        "pymc_usb_host",
        "pymc_usb_ip",
        "pymc_usb_tcp_port",
        "pymc_usb_lbt_enabled",
        "pymc_usb_lbt_max_attempts",
        "usb_path",
        "serial_path",
        "remote_ip",
    ]
    for key in forbidden:
        assert f"{key}:" not in config
