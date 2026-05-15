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

The add-on always keeps `dbPath` under `/app/data/meshcore.db`, which is linked to persistent storage.

### `map_region`

Canonical add-on option for the initial UI map region. The default is `PAR`. The generated CoreScope config uses this value for `defaultRegion`, the generated region list, and `mapDefaults` when the add-on knows coordinates for the region.

Known built-in map centers include `PAR`, `CDG`, `SJC`, `SFO`, and `OAK`. If the region has no built-in center, CoreScope falls back to its upstream map default while still learning observer regions from MQTT topics such as `meshcore/PAR/.../packets`.

### `default_region`

Backward-compatible option retained for the local MQTT source fallback region. MQTT behavior is otherwise unchanged. If `map_region` is omitted in a future config, `default_region` can still be used as the map fallback, but `map_region` is the canonical map option.

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

Ingress is enabled on port `80`. Direct access also works through the mapped `80/tcp` host port.

CoreScope upstream uses absolute frontend API paths such as `/api/...` and root WebSocket connections. The add-on injects `ha-ingress.js` before CoreScope's frontend scripts. That helper derives the current browser base path:

- Direct access: `/`
- Home Assistant Ingress: `/api/hassio_ingress/<redacted>/`

It rewrites CoreScope API fetches to `<browser-base>/api/...` and rewrites root WebSocket connections to the same browser base path with `ws:` or `wss:`. CoreScope's backend already upgrades WebSocket requests at any static path, so no ingress token or hardcoded external path is needed.

MQTT port mapping remains separate from Ingress. Only expose `1883/tcp` when an external MQTT publisher needs to reach the add-on broker directly.

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
