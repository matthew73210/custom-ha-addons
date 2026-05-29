# pyMC Repeater + Console Home Assistant App

This app packages the working pyMC Repeater daemon and layers the pyMC Console dashboard on top of it for Home Assistant Supervisor.

pyMC Console is a frontend/dashboard layer. It uses the same pyMC_Repeater REST API and WebSocket endpoints exposed by the backend daemon in this app. It is not a separate radio daemon.

- pyMC Repeater: https://github.com/pyMC-dev/pyMC_Repeater
- pyMC Console distribution: https://github.com/dmduran12/pymc_console-dist

Current upstream build refs:

- pyMC_Repeater repo/ref: `https://github.com/pyMC-dev/pyMC_Repeater.git` / `main`
- pyMC_core repo/ref: `https://github.com/pyMC-dev/pyMC_core.git` / `main`
- pyMC Console dist repo/ref: `https://github.com/dmduran12/pymc_console-dist.git` / `main`

The Docker build logs the requested ref and resolved commit SHA for each upstream ref, writes `/usr/share/pymc-repeater-console/upstream-build-info.json`, and fails clearly if a requested ref cannot be resolved. The refs remain configurable with `PYMC_REPEATER_REF`, `PYMC_CORE_REF`, and `PYMC_CONSOLE_REF` build arguments for dev/testing.

Compatibility note: default builds now track upstream `main` for pyMC Repeater, pyMC_core, and pyMC Console dist. The pymc-usb-compatible modem family can be reached locally over USB serial with upstream `radio_type: pymc_usb`, or remotely over TCP/IP with upstream `radio_type: pymc_tcp`. The wrapper creates a default upstream config only when no persisted config exists and does not add a protocol bridge or compatibility shim.

## Installation

1. In Home Assistant, go to **Settings -> Apps -> App store**.
2. Use the repository option or store icon to add this app repository URL:

   ```text
   https://github.com/matthew73210/custom-ha-addons
   ```

3. Refresh the App store if needed.
4. Install **pyMC Repeater + Console**.
5. Start the app.
6. Open the dashboard with **Open Web UI**.

## Prebuilt Images

Home Assistant pulls prebuilt images from GitHub Container Registry instead of building locally:

```text
ghcr.io/matthew73210/pymc-repeater-console-{arch}
```

The GitHub Actions workflow publishes `aarch64` and `amd64` images tagged with the app version plus `latest`. Home Assistant Supervisor uses the app `version` from `config.yaml` as the image tag.

## Dashboard Access

Console is the default UI:

```text
/
```

The original pyMC Repeater UI is still available:

```text
/repeater/
```

Both UIs talk to the same pyMC_Repeater backend API and WebSocket endpoints. A small wrapper-owned navigation control is injected into both pages so you can move between **pyMC Console** and **pyMC Repeater**.

## Companion Frame Server

pyMC_Repeater listens inside the app container on TCP port `5000` for companion frame clients. The app exposes container port `5000/tcp` as an optional, configurable Home Assistant app port. It does not bind host port `5000` by default, so the app can install and start even when something else already uses host port `5000`.

To allow remote companion clients, open the app **Network** settings and enable or set a host port for `5000/tcp`. Remote clients should connect to:

```text
<HA host IP>:<configured host port>
```

For example, if you map `5000/tcp` to host port `5000` and your Home Assistant host is `192.168.1.34`, connect clients to:

```text
192.168.1.34:5000
```

Use your Home Assistant host IP and the configured host port. Do not use Docker-internal `172.30.x.x` addresses for remote clients.

## Ingress

Ingress is enabled. Home Assistant opens the app through a wrapper-owned Nginx proxy on port `8080`. The same proxy also listens inside the container on `127.0.0.1:8000` for direct diagnostics. The upstream pyMC_Repeater backend runs behind the wrapper on `127.0.0.1:8001`.

The proxy preserves request methods, query strings, POST bodies, form data, cookies, response `Set-Cookie` headers, redirects, `Host` and `X-Forwarded-*` headers, WebSocket or streaming upgrade headers, and Console worker asset URLs. The worker URL shim rewrites `Worker` and `SharedWorker` constructor URLs to the Home Assistant ingress prefix while preserving module-worker options for Safari and Chromium browsers. Contacts map basemap/style requests are routed through a wrapper-owned same-origin proxy so MapLibre tile, sprite, and glyph URLs keep working under Home Assistant ingress without hardcoding an ingress URL. The proxy also normalizes duplicate `/api/api/...` requests emitted by some original Repeater UI panels so settings such as TX Delays can save without patching upstream assets. The app does not expose host ports by default.

Console packet-cache and graph routes are proxied to the upstream backend unchanged. The wrapper no longer serves `/api/bulk_packets`, `/api/recent_packets`, `/api/filtered_packets`, or `/api/analytics/*` from local SQLite data. If upstream does not provide an analytics route, the wrapper lets upstream fail natively instead of synthesizing analytics.

Both upstream frontends expect to run at `/`. The app handles Home Assistant ingress prefixes and the `/repeater/` original UI path in wrapper-owned Nginx config plus small wrapper-owned JavaScript helpers. Upstream pyMC_Repeater Python code is not patched.

### Browser Note

Chrome and Chromium-based browsers are recommended for Console graph pages through Home Assistant ingress. iPhone/iOS testing currently works. Safari may still have incomplete graph rendering through HA ingress due to browser handling of worker URL rewriting under the ingress path; direct non-ingress access may work even when Safari ingress graph rendering does not.

## Configuration And Persistence

pyMC Repeater runtime settings live only in the persisted upstream config file. The Home Assistant add-on options are not used to configure pyMC Repeater runtime behavior.

The app maps Home Assistant's app-specific config directory into the container at:

```text
/config
```

The wrapper keeps all pyMC-owned durable files under:

```text
/config/pymc-repeater
```

The upstream daemon expects its runtime config at:

```text
/etc/pymc_repeater/config.yaml
```

The persistent config used by this app lives at:

```text
/config/pymc-repeater/config.yaml
```

At startup, the app links `/etc/pymc_repeater` and `/var/lib/pymc_repeater` to `/config/pymc-repeater` for upstream compatibility. The backend is launched with, and `PYMC_REPEATER_CONFIG` points at, the real persisted file `/config/pymc-repeater/config.yaml`. If `/config/pymc-repeater/config.yaml` already exists, the wrapper uses it unchanged. If it does not exist, the wrapper creates a default config once. Later starts do not merge, regenerate, or overwrite the file.

The default pyMC config points directly at the persistent mapped paths:

```yaml
storage:
  storage_dir: /config/pymc-repeater
repeater:
  identity_file: /config/pymc-repeater/identity.key
```

The same persistent directory holds `identity.key`, `repeater.db`, `metrics.rrd`, SQLite WAL files, Glass certificates, and other pyMC history/cache files. If an older install has runtime files in `/data/pymc-repeater`, the wrapper migrates them into `/config/pymc-repeater` on startup without overwriting newer persistent files or an existing persistent `config.yaml`.

Edit `/config/pymc-repeater/config.yaml` to configure radio type, node name, location, logging, KISS serial settings, `pymc_usb`, `pymc_tcp`, Glass, storage, and other pyMC Repeater runtime settings. Use the Home Assistant **Network** settings only for add-on port mappings such as the companion frame server.

The app intentionally has no Home Assistant UI options for pyMC Repeater runtime settings. Values such as node name, coordinates, country, radio type, radio frequency, KISS serial settings, `pymc_usb` serial paths, remote TCP/IP hosts and ports, `pymc_tcp`, Glass, admin password, logging, and raw config YAML belong in `/config/pymc-repeater/config.yaml`.

If Home Assistant Supervisor logs warnings about old options such as `node_name`, `radio_type`, `frequency_hz`, `pymc_tcp_host`, or `config_yaml`, those warnings are stale saved add-on options from an older version. They are not options supported by the current wrapper. Reset or re-save the add-on configuration in Home Assistant, or reinstall the add-on if needed, and keep the runtime settings in `/config/pymc-repeater/config.yaml`.

Normal startup logging is intentionally concise: it prints the selected backend/direct/ingress ports, resolved storage paths, `repeater.db` and `metrics.rrd` presence, selected SQLite table counts, and startup completion. Full redacted config output, listener dumps, and endpoint parity probes are only emitted when `logging.level` in `/config/pymc-repeater/config.yaml` is set to `DEBUG` or when startup fails. The wrapper no longer performs WebSocket readiness probes during normal startup, which avoids noisy expected close errors from the backend.

Nginx logs worker asset requests plus failed graph/API/WebSocket/map-proxy requests with status, upstream target, auth-header presence, token-query presence, upgrade header, host, and ingress prefix presence without logging token values.

The wrapper sets:

```yaml
web:
  web_path: /opt/pymc_console/web/html
```

That makes pyMC_Repeater serve Console at `/`. The Docker build preserves the original pyMC_Repeater web files under `/opt/pymc_repeater_original_web`, and Nginx serves those files at `/repeater/`.

The wrapper does not translate Home Assistant options into pyMC Repeater config keys. Keep runtime configuration in `/config/pymc-repeater/config.yaml` so upstream behavior remains visible and editable as upstream config.

Before starting the backend, the wrapper validates the selected `radio_type`. Unsupported radio types, missing or invalid `pymc_tcp` host/port values, unreachable TCP modem endpoints, missing KISS or `pymc_usb` serial devices, non-character serial paths, and serial permission failures stop startup with a clear log message. This prevents upstream TCP deferred-connect mode from making an unusable radio backend look healthy.

## AppArmor And Permissions

The app uses Home Assistant Supervisor's default AppArmor handling with `apparmor: true`. The declared `addon_config` map grants the container read/write access to `/config`, which is where pyMC stores its database, RRD, identity, config, logs/cache, and related runtime files. Serial, USB, and GPIO access remain declared in `config.yaml` for KISS and radio devices.

## KISS Example

Prefer a stable serial-by-id path when Home Assistant exposes one:

```yaml
radio_type: kiss
kiss:
  port: /dev/serial/by-id/usb-Example_KISS_Modem_123456-if00-port0
  baud_rate: 115200
```

## pymc_usb transport modes

`pymc_usb` names the pymc-usb-compatible modem family and protocol. It does not always mean the modem is physically attached over USB. Upstream pyMC Repeater currently exposes two transport configurations for that modem family.

| Mode | Use when | Config value | Example field |
| --- | --- | --- | --- |
| Local USB serial | The modem is plugged into the Home Assistant host | `/dev/serial/by-id/...` or `/dev/ttyACM*` | `pymc_usb.port` |
| TCP/IP | The pymc-usb-compatible device is reachable over the network | Remote IP address or hostname and TCP port | `pymc_tcp.host`, `pymc_tcp.port` |

### Local USB Serial Example

Use this when the pymc-usb modem is plugged directly into the Home Assistant host:

```yaml
radio_type: pymc_usb

pymc_usb:
  port: /dev/serial/by-id/usb-example-pymc-radio
  baudrate: 921600
  lbt_enabled: true
  lbt_max_attempts: 5
```

Prefer `/dev/serial/by-id/...` because it is stable across reboots. `/dev/ttyACM*`, `/dev/ttyUSB*`, and `/dev/ttyS*` may work but can change. The wrapper already declares `usb: true` and `uart: true`; the serial path is configured only in `/config/pymc-repeater/config.yaml`.

### TCP/IP Example

Use this when the pymc-usb-compatible device is exposed over the network. Upstream uses `radio_type: pymc_tcp` for this mode, with `pymc_tcp.host` for the remote IP address or hostname and `pymc_tcp.port` for the remote TCP port:

```yaml
radio_type: pymc_tcp
radio:
  frequency: 869618000
  tx_power: 14
  bandwidth: 62500
  spreading_factor: 8
  coding_rate: 8
  preamble_length: 16
  sync_word: 18
pymc_tcp:
  host: "192.168.1.49"
  port: 5055
  token: ""
  connect_timeout: 5.0
  lbt_enabled: true
  lbt_max_attempts: 5
```

`baudrate` is not used by upstream in TCP/IP mode because there is no local serial link. Do not put `host`, `ip`, `tcp`, `socket`, `url`, or serial-over-TCP keys under `pymc_usb`; the accepted network schema is the upstream `pymc_tcp` section shown above.

These values are upstream pyMC Repeater config keys. The wrapper does not translate Home Assistant option names or fill automatic radio defaults on later starts, so the radio settings in the config file must match the working modem and the rest of the mesh.

## License And Attribution

pyMC Repeater and pyMC Console are MIT licensed upstream. This repository contains only the Home Assistant app wrapper files and builds the upstream projects during the Docker build.

See the upstream projects for source, licenses, examples, and current hardware details:

- https://github.com/pyMC-dev/pyMC_Repeater
- https://github.com/dmduran12/pymc_console-dist
