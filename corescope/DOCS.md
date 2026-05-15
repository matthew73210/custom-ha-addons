# CoreScope Add-on Documentation

## What This Add-on Runs

This add-on builds CoreScope from the upstream source repository during the Docker build. It does not vendor or copy the CoreScope source tree into this add-on repository, and it does not pull or run the upstream Docker container from inside the add-on.

The final runtime image uses the Home Assistant add-on base image directly:

```Dockerfile
FROM ghcr.io/home-assistant/base:latest
```

This keeps the image compatible with Home Assistant Supervisor while still using CoreScope's upstream Go server, Go ingestor, static web UI, and optional Mosquitto packet relay.

## Configuration Options

### `mqtt_enabled`

Starts the internal Mosquitto listener when `true`, unless `disable_mosquitto` is also `true`.

### `mqtt_port`

Container port used by the internal Mosquitto listener. The default is `1883`.

### `external_mqtt_sources`

List of external MQTT brokers for CoreScope to ingest. Each source supports:

- `name`
- `broker`
- `username`
- `password`
- `topics`
- `iata_filter`
- `region`
- `reject_unauthorized`
- `connect_timeout_sec`

Passwords are written only into `/config/corescope/config.json` inside the add-on config mount. They are not logged by the add-on wrapper.

### `config_json`

Optional full CoreScope `config.json` object as a JSON string. When this is set, it takes precedence over generated config. Use this for advanced CoreScope settings such as channel keys, region maps, geo filters, custom retention, or external MQTT credentials.

### `default_region`

Default IATA-style region code used in generated config.

### `log_level`

Reserved add-on option for CoreScope logging level. The current upstream CoreScope server does not expose a CLI flag or environment variable for log level control, and the ingestor currently only parses `logLevel` without applying it. This add-on does not fake support by passing an ineffective setting through.

### `mosquitto_log_level`

Controls generated Mosquitto `log_type` entries. The default is `warning`, which logs warnings and errors only.

### `debug_startup`

When enabled, logs redacted startup diagnostics, including generated paths, MQTT topics, binary locations, and directory permissions. Passwords and API keys are not logged.

### `disable_caddy`

Defaults to `true`. Caddy is not started in the current s6 service layout; CoreScope serves HTTP directly on port `80`.

HTTPS/Caddy certificate management is not configured in this first add-on version because Home Assistant Ingress and the Home Assistant frontend normally handle TLS.

### `disable_mosquitto`

Disables the internal Mosquitto listener. Use this when all packet ingestion comes from external MQTT sources.

## Ingress

Ingress is enabled on port `80`. CoreScope uses hash-based frontend routes and API paths, so it should be usable through Home Assistant Ingress. WebSocket support is requested with `ingress_stream: true`.

If a future CoreScope release adds absolute URL assumptions that do not work behind Home Assistant's Ingress proxy, use the regular web UI port from the add-on Network settings and report the limitation here.

## Persistent Paths

- `/config/corescope/config.json`: generated or user-supplied CoreScope config.
- `/config/corescope/data`: persistent CoreScope data, linked to `/app/data`.
- `/config/corescope/data/meshcore.db`: SQLite database path.
- `/config/corescope/data/meshcore.db-wal`: SQLite WAL file.
- `/config/corescope/data/meshcore.db-shm`: SQLite shared-memory file.
- `/config/mosquitto`: generated Mosquitto config. Mosquitto persistence is disabled because the broker is only a packet relay for CoreScope.

## Building And Publishing

Home Assistant Supervisor can build local add-ons from this repository. For wider distribution, build and publish the add-on image for each supported architecture, then add an `image` field to `config.yaml` that points at the published GHCR image naming pattern.

The upstream prebuilt image `ghcr.io/kpa-clawbot/corescope:latest` is not used as the final add-on base because this add-on builds CoreScope directly into a Home Assistant add-on image.

## Upstream

CoreScope is developed by Kpa-clawbot and contributors: https://github.com/Kpa-clawbot/CoreScope

This add-on is an independent Home Assistant packaging wrapper and does not imply upstream endorsement.
