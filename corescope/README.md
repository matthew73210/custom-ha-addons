# CoreScope Home Assistant App

Ingress doesn't work right now, you'll need to use external access

CoreScope is a self-hosted MeshCore packet analyzer with a web UI, API, MQTT ingestion, SQLite persistence, maps, packet views, and node analytics.

This app packages CoreScope for Home Assistant Supervisor. It is an independent wrapper and is not maintained or endorsed by CoreScope upstream.

CoreScope is developed by Kpa-clawbot and contributors: https://github.com/Kpa-clawbot/CoreScope

## Installation

1. In Home Assistant, go to **Settings -> Apps -> App store**.
2. Use the repository option or store icon to add this app repository URL:

   ```text
   https://github.com/matthew73210/custom-ha-addons
   ```

3. Refresh the App store if needed.
4. Install **CoreScope**.
5. Review the app options.
6. Start the app.

The web UI is available through Home Assistant Ingress and through the configured mapped `80/tcp` web UI port.

## Persistence

CoreScope stores persistent data under `/app/data`. This app links `/app/data` to the Home Assistant app config mount at `/config/corescope/data`, so the SQLite database, WAL, and shared-memory files survive app restarts and updates.

The generated CoreScope config is stored at `/config/corescope/config.json`. If you provide a full `config_json` option, the app writes that JSON object to the same file while keeping the database path inside `/app/data`.

## MQTT

By default, the app starts a local Mosquitto listener on port `1883` inside the container and configures CoreScope to read `meshcore/#` from it.

Mosquitto persistence is disabled because the broker is used only as a packet relay for CoreScope.

To ingest from external MQTT brokers, add entries to `external_mqtt_sources`. Credentials belong in app options or in a custom `config_json`; do not commit them to this repository.

The host port for `1883/tcp` is disabled by default. Expose it in the app Network settings only when another device or service needs to publish packets to this app.

## Map Region

Use `map_region` to set the initial map region. `default_region` remains as a backward-compatible alias, but `map_region` is canonical when both are present.

## License And Attribution

CoreScope is GPL-3.0 licensed upstream. This repository contains only the Home Assistant app wrapper files and builds CoreScope from upstream during the Docker build.

See the upstream project for CoreScope source, license, releases, and documentation: https://github.com/Kpa-clawbot/CoreScope
