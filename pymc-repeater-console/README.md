# pyMC Repeater + Console Home Assistant App

This app packages the working pyMC Repeater daemon and layers the pyMC Console dashboard on top of it for Home Assistant Supervisor.

pyMC Console is a frontend/dashboard layer. It uses the same pyMC_Repeater REST API and WebSocket endpoints exposed by the backend daemon in this app. It is not a separate radio daemon.

- pyMC Repeater: https://github.com/pyMC-dev/pyMC_Repeater
- pyMC Console distribution: https://github.com/dmduran12/pymc_console-dist

Current upstream build refs:

- pyMC_Repeater repo/ref: `https://github.com/pyMC-dev/pyMC_Repeater.git` / `dev`
- pyMC_core repo/ref: `https://github.com/pyMC-dev/pyMC_core.git` / `3987d3e8863bdf078bc9a9a7e3d29320028f49ee`
- pyMC Console dist repo/ref: `https://github.com/dmduran12/pymc_console-dist.git` / `main`

The Docker build logs the resolved commit SHA for each upstream ref and fails if the installed runtime package does not contain `pymc_tcp` support. The refs remain configurable with `PYMC_REPEATER_REF`, `PYMC_CORE_REF`, and `PYMC_CONSOLE_REF` build arguments.

Compatibility note: this dev app version intentionally tracks upstream pyMC_Repeater `dev` because `pymc_usb` Wi-Fi/TCP modem support is merged there but is not yet present in a tagged/released pyMC_Repeater version. This is not release-stable pinning. The Wi-Fi modem path uses upstream `radio_type: pymc_tcp`. The `pymc_usb` firmware exposes its TCP modem protocol on port `5055` by default; it is not KISS, UDP, WebSocket, HTTP radio control, or serial-over-Wi-Fi. This wrapper only generates the upstream config and does not add a protocol bridge or compatibility shim.

## Installation

1. In Home Assistant, go to **Settings -> Apps -> App store**.
2. Use the repository option or store icon to add this app repository URL:

   ```text
   https://github.com/matthew73210/custom-ha-addons
   ```

3. Refresh the App store if needed.
4. Install **pyMC Repeater + Console**.
5. Review the app options in the Home Assistant **Configuration** tab.
6. Start the app.
7. Open the dashboard with **Open Web UI**.

## Prebuilt Images

Home Assistant pulls prebuilt images from GitHub Container Registry instead of building locally:

```text
ghcr.io/matthew73210/pymc-repeater-console-{arch}
```

The GitHub Actions workflow publishes `aarch64`, `amd64`, `armhf`, `armv7`, and `i386` images tagged with the app version plus `latest`. Home Assistant Supervisor uses the app `version` from `config.yaml` as the image tag.

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

Console packet-cache and graph routes are wrapper-normalized without modifying upstream assets or backend source. The wrapper serves `/api/bulk_packets`, `/api/recent_packets`, `/api/filtered_packets`, and `/api/analytics/*` from the persistent SQLite data when needed, while all other API and WebSocket paths are proxied to the upstream backend.

Both upstream frontends expect to run at `/`. The app handles Home Assistant ingress prefixes and the `/repeater/` original UI path in wrapper-owned Nginx config plus small wrapper-owned JavaScript helpers. Upstream pyMC_Repeater Python code is not patched.

### Browser Note

Chrome and Chromium-based browsers are recommended for Console graph pages through Home Assistant ingress. iPhone/iOS testing currently works. Safari may still have incomplete graph rendering through HA ingress due to browser handling of worker URL rewriting under the ingress path; direct non-ingress access may work even when Safari ingress graph rendering does not.

## Configuration And Persistence

Normal users should change settings in the Home Assistant **Configuration** tab. Supervisor stores those settings as app options, and the wrapper uses them to create or update the generated pyMC config.

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

The persistent generated config used by this app lives at:

```text
/config/pymc-repeater/config.yaml
```

At startup, the app links `/etc/pymc_repeater` and `/var/lib/pymc_repeater` to `/config/pymc-repeater` for upstream compatibility, but the generated pyMC config points directly at the persistent mapped paths:

```yaml
storage:
  storage_dir: /config/pymc-repeater
repeater:
  identity_file: /config/pymc-repeater/identity.key
```

The same persistent directory holds `identity.key`, `repeater.db`, `metrics.rrd`, SQLite WAL files, Glass certificates, and other pyMC history/cache files. If an older install has runtime files in `/data/pymc-repeater`, the wrapper migrates them into `/config/pymc-repeater` on startup without overwriting newer persistent files.

Normal startup logging is intentionally concise: it prints the selected backend/direct/ingress ports, resolved storage paths, `repeater.db` and `metrics.rrd` presence, selected SQLite table counts, and startup completion. Full redacted config output, listener dumps, and endpoint parity probes are only emitted when `log_level` is set to `debug` or when startup fails. The wrapper no longer performs WebSocket readiness probes during normal startup, which avoids noisy expected close errors from the backend.

Nginx logs worker asset requests plus failed graph/API/WebSocket/map-proxy requests with status, upstream target, auth-header presence, token-query presence, upgrade header, host, and ingress prefix presence without logging token values.

The wrapper sets:

```yaml
web:
  web_path: /opt/pymc_console/web/html
```

That makes pyMC_Repeater serve Console at `/`. The Docker build preserves the original pyMC_Repeater web files under `/opt/pymc_repeater_original_web`, and Nginx serves those files at `/repeater/`.

All existing generated config options from the working `pymc-repeater` app are kept, including KISS serial settings, device permissions, storage, logging, Glass options, and ingress behavior.

## AppArmor And Permissions

The app uses Home Assistant Supervisor's default AppArmor handling with `apparmor: true`. The declared `addon_config` map grants the container read/write access to `/config`, which is where pyMC now stores its database, RRD, identity, generated config, logs/cache, and related runtime files. Serial, USB, and GPIO access remain declared in `config.yaml` for KISS and radio devices.

## KISS Example

Prefer a stable serial-by-id path when Home Assistant exposes one:

```yaml
radio_type: kiss
kiss_port: /dev/serial/by-id/usb-Example_KISS_Modem_123456-if00-port0
kiss_baud_rate: 115200
```

## pymc_usb Wi-Fi/TCP Example

Provision the modem on Wi-Fi first, then set the app options to use upstream `pymc_tcp`:

```yaml
radio_type: pymc_tcp
pymc_tcp_host: 192.168.1.50
pymc_tcp_port: 5055
pymc_tcp_token: ""
pymc_tcp_connect_timeout: 5.0
pymc_tcp_lbt_enabled: true
pymc_tcp_lbt_max_attempts: 5
tx_power: 22
sync_word: 0
preamble_length: 0
```

`sync_word` and `preamble_length` use `0` as an automatic wrapper value. For `radio_type: pymc_tcp`, the wrapper writes upstream radio defaults matching the pymc_usb TCP modem defaults: `sync_word: 18` (`0x12`) and `preamble_length: 16`. Set explicit values only when your modem and mesh use different radio settings. The configured `tx_power`, `frequency_hz`, `bandwidth`, `spreading_factor`, and `coding_rate` are also sent to the TCP modem during startup, so they must match the working modem and the rest of the mesh.

At startup the wrapper generates the upstream-compatible block:

```yaml
radio_type: pymc_tcp
radio:
  frequency: 869618000
  tx_power: 22
  bandwidth: 62500
  spreading_factor: 8
  coding_rate: 8
  preamble_length: 16
  sync_word: 18
pymc_tcp:
  host: 192.168.1.50
  port: 5055
  token: ""
  connect_timeout: 5.0
  lbt_enabled: true
  lbt_max_attempts: 5
```

## License And Attribution

pyMC Repeater and pyMC Console are MIT licensed upstream. This repository contains only the Home Assistant app wrapper files and builds the upstream projects during the Docker build.

See the upstream projects for source, licenses, examples, and current hardware details:

- https://github.com/pyMC-dev/pyMC_Repeater
- https://github.com/dmduran12/pymc_console-dist
