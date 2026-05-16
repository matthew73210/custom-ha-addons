# pyMC Repeater + Console Home Assistant Add-on

This add-on packages the working pyMC Repeater daemon and layers the pyMC Console dashboard on top of it for Home Assistant Supervisor.

pyMC Console is a frontend/dashboard layer. It uses the same pyMC_Repeater REST API and WebSocket endpoints exposed by the backend daemon in this add-on. It is not a separate radio daemon.

- pyMC Repeater: https://github.com/pyMC-dev/pyMC_Repeater
- pyMC Console distribution: https://github.com/dmduran12/pymc_console-dist

## Installation

1. Add this add-on repository in Home Assistant:

   ```text
   https://github.com/matthew73210/custom-ha-addons
   ```

2. Refresh the add-on store.
3. Install **pyMC Repeater + Console**.
4. Review the add-on options in the Home Assistant add-on **Configuration** tab.
5. Start the add-on.
6. Open the dashboard with **Open Web UI**.

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

## Ingress

Ingress is enabled. Home Assistant opens the add-on through an internal Nginx proxy on port `8080`, and that proxy forwards API and WebSocket traffic to pyMC on `127.0.0.1:8000`.

The proxy preserves request methods, query strings, POST bodies, form data, cookies, response `Set-Cookie` headers, redirects, `Host` and `X-Forwarded-*` headers, and WebSocket or streaming upgrade headers. The add-on does not expose host ports by default.

Both upstream frontends expect to run at `/`. The add-on handles Home Assistant ingress prefixes and the `/repeater/` original UI path in wrapper-owned Nginx config plus small wrapper-owned JavaScript helpers. Upstream pyMC_Repeater Python code is not patched.

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

The wrapper sets:

```yaml
web:
  web_path: /opt/pymc_console/web/html
```

That makes pyMC_Repeater serve Console at `/`. The Docker build preserves the original pyMC_Repeater web files under `/opt/pymc_repeater_original_web`, and Nginx serves those files at `/repeater/`.

All existing generated config options from the working `pymc-repeater` add-on are kept, including KISS serial settings, device permissions, storage, logging, Glass options, and ingress behavior.

## KISS Example

Prefer a stable serial-by-id path when Home Assistant exposes one:

```yaml
radio_type: kiss
kiss_port: /dev/serial/by-id/usb-Example_KISS_Modem_123456-if00-port0
kiss_baud_rate: 115200
```

## License And Attribution

pyMC Repeater and pyMC Console are MIT licensed upstream. This repository contains only the Home Assistant add-on wrapper files and builds the upstream projects during the Docker build.

See the upstream projects for source, licenses, examples, and current hardware details:

- https://github.com/pyMC-dev/pyMC_Repeater
- https://github.com/dmduran12/pymc_console-dist
