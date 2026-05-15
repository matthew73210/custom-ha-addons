# pyMC Repeater Home Assistant Add-on

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

## Ingress And Dashboard Access

Home Assistant ingress is enabled. Open the add-on from the Home Assistant sidebar or from the add-on page with **Open Web UI**.

The pyMC dashboard still listens on port `8000` inside the container. Home Assistant connects ingress directly to that internal port with `ingress_port: 8000`, and `8000/tcp` is not exposed on the host by default. If you need direct access for debugging, map the optional port in the add-on network settings.

The wrapper patches the upstream web UI during the Docker build so root-relative assets, API calls, document routes, event streams, and WebSocket URLs resolve through the Home Assistant ingress path.

## Configuration And Persistence

The upstream daemon expects its runtime config at:

```text
/etc/pymc_repeater/config.yaml
```

The persistent add-on config lives at:

```text
/config/pymc-repeater/config.yaml
```

At startup, the add-on links `/etc/pymc_repeater` to `/config/pymc-repeater`. On first start, if no persistent config exists, the add-on creates one from the add-on options. On later restarts, it reuses the existing persistent config and does not overwrite it.

Runtime data is stored through the upstream path `/var/lib/pymc_repeater`, which the add-on links to:

```text
/data/pymc-repeater
```

Changing add-on options after the first generated config exists will not rewrite `/config/pymc-repeater/config.yaml`. Edit the persistent config, delete it to regenerate from options, or use `config_yaml` when you intentionally want the add-on options to replace it.

`config_yaml` is a full upstream YAML override. When it is non-empty, the add-on writes it to the persistent config on every startup, then enforces wrapper-managed runtime fields:

- `storage.storage_dir: /var/lib/pymc_repeater`
- `http.host: 0.0.0.0`
- `http.port: 8000`
- `logging.level` from the add-on option
- `repeater.identity_file: /etc/pymc_repeater/identity.key` when no `identity_key` is provided

If `config_yaml` is empty and the persistent config exists, restarts reuse the persistent config instead of rewriting it. If `config_yaml` is empty and no persistent config exists, the add-on generates a first-start config from the visible add-on options.

## Add-on Options

- `node_name`: upstream `repeater.node_name`
- `public_name`: stored as upstream `repeater.owner_info`
- `latitude`, `longitude`: upstream node location fields
- `country`: stored as generated config metadata at `repeater.country` and `mqtt.country`; upstream currently uses explicit radio settings for regulation
- `map_region`: upstream `mqtt.iata_code`, default `PAR`
- `radio_type`: `sx1262`, `sx1262_ch341`, or `kiss`
- `frequency_preset`: convenience preset for common radio values
- `frequency_hz`, `tx_power`, `bandwidth`, `spreading_factor`, `coding_rate`: upstream `radio` fields
- `kiss_port`, `kiss_baud_rate`: upstream `kiss` serial settings
- `admin_password`: upstream `repeater.security.admin_password`
- `glass_enabled`, `glass_base_url`, `glass_inform_interval_seconds`: upstream pyMC Glass settings
- `log_level`: upstream logging level and service CLI level
- `config_yaml`: full raw upstream config replacement

## KISS Example

Prefer a stable serial-by-id path when Home Assistant exposes one:

```yaml
radio_type: kiss
kiss_port: /dev/serial/by-id/usb-Example_KISS_Modem_123456-if00-port0
kiss_baud_rate: 115200
```

## Hardware Notes

Supported upstream radio types exposed by this wrapper:

- `sx1262` for Linux spidev plus system GPIO
- `sx1262_ch341` for CH341 USB-SPI plus CH341 GPIO
- `kiss` for a KISS modem on a serial port

pyMC Repeater does not support UART HATs or SX1302/SX1303 concentrators.

USB, SPI, and GPIO access depends on the Home Assistant host and Supervisor restrictions. You may need to enable host SPI, attach the USB serial/SPI device, use a stable `/dev/serial/by-id/...` path, or adjust add-on protection/full-access settings before the daemon can initialize the radio.

## Current Mapping Limits

The upstream example does not expose a clear `node_id` field or a dedicated country-driven regulatory selector. This wrapper maps node identity to `node_name` and `owner_info`, stores `country` as metadata, and maps `map_region` to `mqtt.iata_code`. Frequency regulation remains the operator's responsibility through the radio preset or explicit radio fields.

## License And Attribution

pyMC Repeater is MIT licensed upstream. This repository contains only the Home Assistant add-on wrapper files and builds pyMC Repeater from upstream during the Docker build.

See the upstream project for source, license, examples, and current hardware details: https://github.com/pyMC-dev/pyMC_Repeater
