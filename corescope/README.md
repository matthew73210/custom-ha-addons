# CoreScope Home Assistant Add-on

Ingress doesn't work right now, you'll need to use external access

CoreScope is a self-hosted MeshCore packet analyzer with a web UI, API, MQTT ingestion, SQLite persistence, maps, packet views, and node analytics.

This add-on packages CoreScope for Home Assistant Supervisor. It is an independent wrapper and is not maintained or endorsed by CoreScope upstream.

CoreScope is developed by Kpa-clawbot and contributors: https://github.com/Kpa-clawbot/CoreScope

## Installation

1. Add this add-on repository in Home Assistant:

   ```text
   https://github.com/matthew73210/custom-ha-addons
   ```

2. Refresh the add-on store.
3. Install **CoreScope**.
4. Review the add-on options.
5. Start the add-on.

The web UI is available through Home Assistant Ingress and through the configured mapped `80/tcp` web UI port.

## Persistence

CoreScope stores persistent data under `/app/data`. This add-on links `/app/data` to the add-on config mount at `/config/corescope/data`, so the SQLite database, WAL, and shared-memory files survive add-on restarts and updates.

The generated CoreScope config is stored at `/config/corescope/config.json`. If you provide a full `config_json` option, the add-on writes that JSON object to the same file while keeping the database path inside `/app/data`.

## MQTT

By default, the add-on starts a local Mosquitto listener on port `1883` inside the container and configures CoreScope to read `meshcore/#` from it.

Mosquitto persistence is disabled because the broker is used only as a packet relay for CoreScope.

To ingest from external MQTT brokers, add entries to `external_mqtt_sources`. Credentials belong in add-on options or in a custom `config_json`; do not commit them to this repository.

The host port for `1883/tcp` is disabled by default. Expose it in the add-on Network settings only when another device or service needs to publish packets to this add-on.

## Map Region

Use `map_region` to set the initial map region. `default_region` remains as a backward-compatible alias, but `map_region` is canonical when both are present.

## License And Attribution

CoreScope is GPL-3.0 licensed upstream. This repository contains only the Home Assistant add-on wrapper files and builds CoreScope from upstream during the Docker build.

See the upstream project for CoreScope source, license, releases, and documentation: https://github.com/Kpa-clawbot/CoreScope
