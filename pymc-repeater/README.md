# pyMC Repeater Home Assistant Add-on

This add-on packages the upstream pyMC Repeater daemon for Home Assistant Supervisor. It is a wrapper around upstream pyMC_Repeater and is not maintained or endorsed by pyMC upstream.

pyMC Repeater is a Python MeshCore repeater daemon built on `pymc_core`: https://github.com/pyMC-dev/pyMC_Repeater

## Installation

1. Add this add-on repository in Home Assistant:

   ```text
   https://github.com/matthew73210/custom-ha-addons
   ```

2. Refresh the add-on store.
3. Install **pyMC Repeater**.
4. Review the add-on options in the Home Assistant add-on **Configuration** tab.
5. Start the add-on.
6. Open the dashboard with **Open Web UI**.

## Ingress And Dashboard Access

Ingress is enabled. Home Assistant opens the add-on through an internal Nginx proxy on port `8080`, and that proxy forwards requests to pyMC on `127.0.0.1:8000`.

The proxy preserves request methods, query strings, POST bodies, form data, cookies, response `Set-Cookie` headers, redirects, `Host` and `X-Forwarded-*` headers, and WebSocket or streaming upgrade headers. The add-on does not expose host ports by default.

pyMC's frontend expects to run at `/`, while Home Assistant ingress serves add-ons under a prefix such as `/api/hassio_ingress/<token>/`. The add-on handles that in wrapper-owned Nginx config and a small wrapper-owned `ha-ingress-proxy.js` helper. Upstream pyMC_Repeater Python, HTML, JavaScript, CSS, image, and static files are not modified, patched, overwritten, or vendored.

If you manually expose the proxy port, direct access may behave differently from Home Assistant ingress because direct access does not include the Home Assistant ingress path prefix.

## Configuration And Persistence

Normal users should change settings in the Home Assistant add-on **Configuration** tab. Supervisor stores those settings as add-on options, and the wrapper uses them to create or update the generated pyMC config.

The upstream daemon expects its runtime config at:

```text
/etc/pymc_repeater/config.yaml
```

The persistent generated config used by this add-on lives at:

```text
/config/pymc-repeater/config.yaml
```

At startup, the add-on links `/etc/pymc_repeater` to `/config/pymc-repeater`. On first start, if no persistent config exists, the add-on creates one from the add-on options. On later restarts, it reuses the existing persistent config and only updates wrapper-managed runtime fields such as the internal HTTP bind address and storage path when needed.

Advanced users can edit `/config/pymc-repeater/config.yaml` directly when they need upstream pyMC settings that are not exposed in the add-on UI.

Runtime data is stored through the upstream path `/var/lib/pymc_repeater`, which the add-on links to:

```text
/data/pymc-repeater
```

`config_yaml` is a full upstream YAML override. When it is non-empty, the add-on writes it to the persistent config on every startup, then enforces wrapper-managed runtime fields:

- `storage.storage_dir: /var/lib/pymc_repeater`
- `http.host: 127.0.0.1`
- `http.port: 8000`
- `logging.level` from the add-on option
- `repeater.identity_file: /etc/pymc_repeater/identity.key` when no `identity_key` is provided

If `config_yaml` is empty and the persistent config exists, restarts reuse the persistent config instead of regenerating it, apart from the wrapper-managed runtime fields above.

## Add-on Options

- `node_name`: upstream `repeater.node_name`
- `public_name`: stored as upstream `repeater.owner_info`
- `latitude`, `longitude`: upstream node location fields
- `country`: stored as generated config metadata at `repeater.country` and `mqtt.country`
- `map_region`: upstream `mqtt.iata_code`
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

## License And Attribution

pyMC Repeater is MIT licensed upstream. This repository contains only the Home Assistant add-on wrapper files and builds pyMC Repeater from upstream during the Docker build.

See the upstream project for source, license, examples, and current hardware details: https://github.com/pyMC-dev/pyMC_Repeater
