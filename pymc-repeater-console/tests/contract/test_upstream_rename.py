from __future__ import annotations

from helpers import ADDON_ROOT


DOCKERFILE = ADDON_ROOT / "Dockerfile"
CONFIG_YAML = ADDON_ROOT / "config.yaml"


def test_dockerfile_uses_openhop_repeater_pin_and_runtime_core_package():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert "ARG PYMC_REPEATER_REPO=https://github.com/openhop-dev/openhop_repeater.git" in dockerfile
    assert "ARG PYMC_REPEATER_REF=60357f580876ceab5b3808a7ed00f81ae235c003" in dockerfile
    assert "ARG PYMC_CORE_REPO=https://github.com/openhop-dev/openhop_core.git" in dockerfile
    assert "ARG OPENHOP_CORE_VERSION=1.1.1" in dockerfile
    assert '"openhop_core[hardware]==${OPENHOP_CORE_VERSION}"' in dockerfile
    assert "python3 -m pip show openhop-core" in dockerfile


def test_dockerfile_checks_renamed_openhop_core_imports():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert "openhop_core.hardware.tcp_radio" in dockerfile
    assert "openhop_core.hardware.usb_radio" in dockerfile
    assert "from openhop_core.hardware.tcp_radio import TCPLoRaRadio" in dockerfile
    assert "from openhop_core.hardware.usb_radio import USBLoRaRadio" in dockerfile


def test_addon_version_bumped_for_openhop_update():
    config_yaml = CONFIG_YAML.read_text(encoding="utf-8")

    assert "version: 0.3.4" in config_yaml
