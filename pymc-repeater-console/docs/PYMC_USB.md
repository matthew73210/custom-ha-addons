# pyMC USB Runtime Configuration

`pymc-repeater-console` must not expose pyMC USB settings as Home Assistant add-on UI options. The radio selection, serial device path, network host, network port, baudrate, and LBT settings belong in the persisted pyMC Repeater config file:

```text
/config/pymc-repeater/config.yaml
```

## Upstream Support

The pinned pyMC Repeater upstream supports the pymc-usb-compatible modem family in two ways:

- Local USB serial mode uses `radio_type: pymc_usb` and the `pymc_usb` config section.
- TCP/IP mode to a remote pymc-usb-compatible firmware endpoint uses `radio_type: pymc_tcp` and the `pymc_tcp` config section.

In other words, "USB" in `pymc_usb` is the protocol/device family name, not always the physical transport. A pymc-usb-compatible radio can be reached locally by USB serial, or remotely over TCP/IP when the firmware exposes its TCP modem endpoint.

## pymc_usb transport modes

| Mode | Use when | Config value | Example field |
| --- | --- | --- | --- |
| Local USB serial | The modem is plugged into the Home Assistant host | `/dev/serial/by-id/...` or `/dev/ttyACM*` | `pymc_usb.port` |
| TCP/IP | The pymc-usb-compatible device is reachable over the network | Remote IP address or hostname and TCP port | `pymc_tcp.host`, `pymc_tcp.port` |

### A. Local USB serial mode

Use this when the pymc-usb modem is plugged directly into the Home Assistant host.

```yaml
radio_type: pymc_usb

pymc_usb:
  port: /dev/serial/by-id/usb-example-pymc-radio
  baudrate: 921600
  lbt_enabled: true
  lbt_max_attempts: 5
```

The upstream setup logic recognizes serial paths matching:

- `/dev/ttyACM*`
- `/dev/ttyUSB*`
- `/dev/ttyS*`
- `/dev/serial/by-id/*`

- `/dev/serial/by-id/...` is preferred because it is stable across reboots and reconnects.
- `/dev/ttyACM*`, `/dev/ttyUSB*`, and `/dev/ttyS*` may work but can change.
- The wrapper already declares `usb: true` and `uart: true`.
- The serial path is configured only in `/config/pymc-repeater/config.yaml`.
- `pymc_usb.baudrate` is used in this local serial mode and defaults to `921600` if omitted.

### B. TCP/IP mode

Use this when the pymc-usb-compatible device is exposed over the network.

Upstream pyMC Repeater does not accept `host`, `ip`, `tcp`, `socket`, `url`, or `serial-over-tcp` keys under the `pymc_usb` section. The accepted TCP/IP schema is the upstream `pymc_tcp` transport:

```yaml
radio_type: pymc_tcp

pymc_tcp:
  host: 192.168.1.49
  port: 5055
  token: ""
  connect_timeout: 5.0
  lbt_enabled: true
  lbt_max_attempts: 5
```

Use `pymc_tcp.host` for the remote device IP address or hostname. Use `pymc_tcp.port` for the remote TCP port; pymc-usb firmware commonly uses `5055`. `baudrate` is not used by upstream in TCP/IP mode because there is no local serial link.

Investigation note: upstream pyMC Repeater `dev` at `85f282357ca6cd6516d961eb8650ecc2a6286f74` and pinned `main` at `e17d1137ab2d2d5b86d03c99523272289b7688aa` both route TCP/IP pymc-usb-compatible firmware through `radio_type: pymc_tcp`, not through extra network keys under `pymc_usb`.

## Home Assistant Add-On Boundary

The add-on metadata currently declares:

- `usb: true`
- `uart: true`

Those are wrapper-level device access declarations. They are not pyMC runtime options and they do not select the radio or serial device path.

If Home Assistant Supervisor requires narrower or additional device mapping for a specific install, that mapping should remain wrapper packaging metadata. The pyMC radio type, USB serial path, remote TCP/IP host, remote TCP port, baudrate, and LBT behavior must stay in `/config/pymc-repeater/config.yaml`.

## Startup Behavior

The wrapper creates `/config/pymc-repeater/config.yaml` once if it is missing and then preserves it unchanged on later starts. Startup passes the runtime config file to upstream pyMC Repeater unchanged through:

```text
python -m repeater.main --config /etc/pymc_repeater/config.yaml
```

`/etc/pymc_repeater` is a wrapper symlink to the persisted `/config/pymc-repeater` directory.
