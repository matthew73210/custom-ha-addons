#!/usr/bin/with-contenv bashio
set -euo pipefail

CONFIG_PATH="/config/config.json"
DATA_DIR="/config/data"
OPTIONS_PATH="/data/options.json"

mkdir -p "${DATA_DIR}" /config/mosquitto /config/caddy /config/run /app

if [ -e /app/data ] && [ ! -L /app/data ]; then
  rm -rf /app/data
fi
ln -sfn "${DATA_DIR}" /app/data

if [ -f "${OPTIONS_PATH}" ] && jq -e '.config_json? // "" | length > 0' "${OPTIONS_PATH}" >/dev/null; then
  jq -er '.config_json | fromjson | if type == "object" then . else error("config_json must be a JSON object") end' \
    "${OPTIONS_PATH}" > "${CONFIG_PATH}.tmp"
  mv "${CONFIG_PATH}.tmp" "${CONFIG_PATH}"
  bashio::log.info "Using custom CoreScope config JSON from add-on options."
else
  jq -n --slurpfile options "${OPTIONS_PATH}" '
    def prune:
      with_entries(select(.value != null and .value != "" and .value != []));
    def normalize_source:
      prune
      | if has("iata_filter") then .iataFilter = .iata_filter | del(.iata_filter) else . end
      | if has("reject_unauthorized") then .rejectUnauthorized = .reject_unauthorized | del(.reject_unauthorized) else . end
      | if has("connect_timeout_sec") then .connectTimeoutSec = .connect_timeout_sec | del(.connect_timeout_sec) else . end;

    ($options[0] // {}) as $opt
    | ($opt.default_region // "SJC") as $region
    | ($opt.mqtt_port // 1883) as $mqtt_port
    | (
        [
          if (($opt.mqtt_enabled // true) and (($opt.disable_mosquitto // false) | not)) then
            {
              name: "home-assistant-addon",
              broker: ("mqtt://localhost:" + ($mqtt_port | tostring)),
              topics: ["meshcore/#"],
              region: $region
            }
          else empty end
        ]
        + (($opt.external_mqtt_sources // []) | map(normalize_source))
      ) as $sources
    | {
        dbPath: "/app/data/meshcore.db",
        defaultRegion: $region,
        regions: {($region): $region},
        mqttSources: $sources,
        branding: {
          siteName: "CoreScope",
          tagline: "Real-time MeshCore packet analyzer"
        },
        retention: {
          nodeDays: 7,
          observerDays: 14,
          packetDays: 30,
          metricsDays: 30
        },
        packetStore: {
          maxMemoryMB: 512,
          retentionHours: 168
        },
        timestamps: {
          defaultMode: "ago",
          timezone: "local",
          formatPreset: "iso",
          customFormat: "",
          allowCustomFormat: false
        }
      }
  ' > "${CONFIG_PATH}.tmp"
  mv "${CONFIG_PATH}.tmp" "${CONFIG_PATH}"
  bashio::log.info "Generated CoreScope config at ${CONFIG_PATH}."
fi

ln -sfn "${CONFIG_PATH}" /app/config.json

MQTT_PORT="$(jq -r '.mqtt_port // 1883' "${OPTIONS_PATH}")"
cat > /config/mosquitto/mosquitto.conf <<EOF
listener ${MQTT_PORT} 0.0.0.0
allow_anonymous true
persistence true
persistence_location /config/mosquitto/
log_dest stdout
EOF

cat > /config/caddy/Caddyfile <<'EOF'
:80 {
  reverse_proxy 127.0.0.1:3000
}
EOF
