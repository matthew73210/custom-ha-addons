# pyMC Repeater Home Assistant Add-on

There is also https://github.com/pyMC-dev

This add-on packages the pyMC Repeater daemon for Home Assistant Supervisor. It is an independent wrapper and is not maintained or endorsed by pyMC upstream.

pyMC Repeater is a Python MeshCore repeater daemon built on `pymc_core`: https://github.com/pyMC-dev/pyMC_Repeater

## Installation

1. Add this add-on repository in Home Assistant:

   ```text
   https://github.com/matthew73210/custom-ha-addons
   ```

2. Refresh the add-on store.
3. Install **pyMC Repeater**.
4. Review the add-on options.
5. Start the add-on.

The dashboard is exposed on the configured `8000/tcp` web UI port. Ingress is intentionally disabled in this first package because upstream currently serves a standalone dashboard and API from `/`; direct port access is the most predictable path.

## Configuration And Persistence

At startup, the add-on writes `/etc/pymc_repeater/config.yaml` from the add-on options. That directory is linked to `/config/pymc-repeater`, so the generated config and generated identity key survive restarts and rebuilds.

Upstream persistent data is stored at `/var/lib/pymc_repeater`. The add-on links that path to `/data/pymc-repeater`, so SQLite/RRD/runtime data survives restarts and rebuilds.

Use `config_yaml` when you need the full upstream configuration schema. When `config_yaml` is set, the add-on uses it as the base config and still forces these wrapper-managed paths:

- `storage.storage_dir: /var/lib/pymc_repeater`
- `http.host: 0.0.0.0`
- `http.port: 8000`
- `repeater.identity_file: /etc/pymc_repeater/identity.key` when no identity is provided

## Radio Support

The initial options expose `radio_type`, `region`, `frequency_preset`, and KISS serial settings. The generated SX1262 GPIO/SPI defaults come from the upstream example config and may need to be overridden for your hardware using `config_yaml`.

Supported upstream radio types in this wrapper:

- `sx1262` for Linux spidev plus system GPIO
- `sx1262_ch341` for CH341 USB-SPI plus CH341 GPIO
- `kiss` for a KISS modem on a serial port

This add-on does not add support for UART HATs or SX1302/SX1303 concentrators.

## Frequency Presets

`frequency_preset` is a small wrapper convenience, not the full upstream radio-settings database:

- `EU_868`: EU/UK narrow, 869.618 MHz, SF8, BW62.5, CR8
- `EU_868_LONG_RANGE`: EU/UK long range, 869.525 MHz, SF11, BW250, CR5
- `US_915`: USA/Canada recommended, 910.525 MHz, SF7, BW62.5, CR5
- `AU_915`: Australia, 915.800 MHz, SF10, BW250, CR5
- `NZ_917`: New Zealand narrow, 917.375 MHz, SF7, BW62.5, CR5

Provide `config_yaml` for custom radio parameters.

## Hardware Notes

KISS devices normally appear as `/dev/ttyUSB0` or similar. SX1262 boards need SPI and GPIO access from the host. Home Assistant hardware availability varies by installation, so you may need to enable the host SPI interface, attach the USB serial/SPI device, or adjust add-on protection/device settings before the daemon can initialize the radio.

## License And Attribution

pyMC Repeater is MIT licensed upstream. This repository contains only the Home Assistant add-on wrapper files and builds pyMC Repeater from upstream during the Docker build.

See the upstream project for source, license, examples, and current hardware details: https://github.com/pyMC-dev/pyMC_Repeater
