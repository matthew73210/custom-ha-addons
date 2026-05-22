# pyMC USB Runtime Configuration

`pymc-repeater-console` must not expose pyMC USB settings as Home Assistant add-on UI options. The USB radio selection and serial device path belong in the persisted pyMC Repeater config file:

```text
/config/pymc-repeater/config.yaml
```

## Upstream Support

The pinned pyMC Repeater upstream supports USB pyMC radios with:

- `radio_type: pymc_usb`
- config section: `pymc_usb`
- required device key: `pymc_usb.port`
- optional baudrate key: `pymc_usb.baudrate`, default `921600`
- optional LBT keys: `pymc_usb.lbt_enabled` and `pymc_usb.lbt_max_attempts`

The upstream setup logic recognizes serial paths matching:

- `/dev/ttyACM*`
- `/dev/ttyUSB*`
- `/dev/ttyS*`
- `/dev/serial/by-id/*`

Use `/dev/serial/by-id/*` when available because it is more stable across reconnects. Upstream examples mention `/dev/ttyACM0`.

## Example Config

```yaml
radio_type: pymc_usb

pymc_usb:
  port: /dev/serial/by-id/usb-example-pymc-radio
  baudrate: 921600
  lbt_enabled: true
  lbt_max_attempts: 5

radio:
  frequency: 869618000
  bandwidth: 62500
  spreading_factor: 8
  coding_rate: 8
  sync_word: 18
  preamble_length: 16
  tx_power: 14
```

## Home Assistant Add-On Boundary

The add-on metadata currently declares:

- `usb: true`
- `uart: true`

Those are wrapper-level device access declarations. They are not pyMC runtime options and they do not select the radio or serial device path.

If Home Assistant Supervisor requires narrower or additional device mapping for a specific install, that mapping should remain wrapper packaging metadata. The pyMC radio type, USB serial path, baudrate, and LBT behavior must stay in `/config/pymc-repeater/config.yaml`.

## Startup Behavior

The wrapper creates `/config/pymc-repeater/config.yaml` once if it is missing and then preserves it unchanged on later starts. Startup passes the runtime config file to upstream pyMC Repeater unchanged through:

```text
python -m repeater.main --config /etc/pymc_repeater/config.yaml
```

`/etc/pymc_repeater` is a wrapper symlink to the persisted `/config/pymc-repeater` directory.
