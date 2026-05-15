#!/usr/bin/with-contenv bashio
set -euo pipefail

CONFIG_ROOT="/config/corescope"
CONFIG_PATH="${CONFIG_ROOT}/config.json"
DATA_DIR="${CONFIG_ROOT}/data"
RUN_DIR="${CONFIG_ROOT}/run"
OPTIONS_PATH="/data/options.json"
MOSQUITTO_DIR="/config/mosquitto"

mkdir -p "${CONFIG_ROOT}" "${DATA_DIR}" "${RUN_DIR}" "${MOSQUITTO_DIR}" /app

if [ -d /config/data ] && [ ! -e "${DATA_DIR}/meshcore.db" ]; then
  bashio::log.info "Migrating existing CoreScope data from /config/data to ${DATA_DIR}."
  cp -an /config/data/. "${DATA_DIR}/" 2>/dev/null || true
fi

if [ -e /app/data ] && [ ! -L /app/data ]; then
  rm -rf /app/data
fi
ln -sfn "${DATA_DIR}" /app/data

chmod -R u+rwX,g+rwX "${CONFIG_ROOT}" "${DATA_DIR}" "${RUN_DIR}"

log_level="$(jq -r '.log_level // "info"' "${OPTIONS_PATH}")"
MAP_REGION="$(jq -r '(.map_region // .default_region // "PAR") | ascii_upcase' "${OPTIONS_PATH}")"
MQTT_REGION="$(jq -r '(.default_region // "SJC") | ascii_upcase' "${OPTIONS_PATH}")"
MAP_CENTER_JSON="null"
case "${MAP_REGION}" in
  PAR) MAP_CENTER_JSON='[48.8566,2.3522]' ;;
  CDG) MAP_CENTER_JSON='[49.0097,2.5479]' ;;
  SJC) MAP_CENTER_JSON='[37.3626,-121.929]' ;;
  SFO) MAP_CENTER_JSON='[37.6213,-122.379]' ;;
  OAK) MAP_CENTER_JSON='[37.7213,-122.2208]' ;;
esac
MAP_ZOOM="9"

if [ -f "${OPTIONS_PATH}" ] && jq -e '.config_json? // "" | length > 0' "${OPTIONS_PATH}" >/dev/null; then
  jq -er \
    --arg db_path "/app/data/meshcore.db" \
    --arg map_region "${MAP_REGION}" \
    --arg mqtt_region "${MQTT_REGION}" \
    --argjson map_center "${MAP_CENTER_JSON}" \
    --argjson map_zoom "${MAP_ZOOM}" '
    .config_json
    | fromjson
    | if type == "object" then . else error("config_json must be a JSON object") end
    | .dbPath = $db_path
    | .regions = ((.regions // {}) + {($map_region): $map_region, ($mqtt_region): $mqtt_region})
    | if $map_center == null then .
      else .mapDefaults = ((.mapDefaults // {}) + {center: $map_center, zoom: ((.mapDefaults.zoom // $map_zoom))})
      end
  ' "${OPTIONS_PATH}" > "${CONFIG_PATH}.tmp"
  mv "${CONFIG_PATH}.tmp" "${CONFIG_PATH}"
  bashio::log.info "Using custom CoreScope config JSON from add-on options."
else
  jq -n \
    --slurpfile options "${OPTIONS_PATH}" \
    --arg map_region "${MAP_REGION}" \
    --arg mqtt_region "${MQTT_REGION}" \
    --argjson map_center "${MAP_CENTER_JSON}" \
    --argjson map_zoom "${MAP_ZOOM}" '
    def prune:
      with_entries(select(.value != null and .value != "" and .value != []));
    def normalize_source:
      prune
      | if has("iata_filter") then .iataFilter = .iata_filter | del(.iata_filter) else . end
      | if has("reject_unauthorized") then .rejectUnauthorized = .reject_unauthorized | del(.reject_unauthorized) else . end
      | if has("connect_timeout_sec") then .connectTimeoutSec = .connect_timeout_sec | del(.connect_timeout_sec) else . end;

    ($options[0] // {}) as $opt
    | $map_region as $region
    | ($opt.mqtt_port // 1883) as $mqtt_port
    | (
        [
          if (($opt.mqtt_enabled // true) and (($opt.disable_mosquitto // false) | not)) then
            {
              name: "home-assistant-addon",
              broker: ("mqtt://localhost:" + ($mqtt_port | tostring)),
              topics: ["meshcore/#"],
              region: $mqtt_region
            }
          else empty end
        ]
        + (($opt.external_mqtt_sources // []) | map(normalize_source))
      ) as $sources
    | {
        dbPath: "/app/data/meshcore.db",
        defaultRegion: $region,
        regions: {($region): $region, ($mqtt_region): $mqtt_region},
        mqttSources: $sources,
        mapDefaults: (if $map_center == null then {} else {center: $map_center, zoom: $map_zoom} end),
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
MOSQUITTO_LOG_LEVEL="$(jq -r '.mosquitto_log_level // "warning"' "${OPTIONS_PATH}")"

cat > "${MOSQUITTO_DIR}/mosquitto.conf" <<EOF
listener ${MQTT_PORT} 0.0.0.0
allow_anonymous true
persistence false
log_dest stdout
EOF

case "${MOSQUITTO_LOG_LEVEL}" in
  debug)
    echo "log_type all" >> "${MOSQUITTO_DIR}/mosquitto.conf"
    ;;
  information)
    {
      echo "log_type information"
      echo "log_type notice"
      echo "log_type warning"
      echo "log_type error"
    } >> "${MOSQUITTO_DIR}/mosquitto.conf"
    ;;
  notice)
    {
      echo "log_type notice"
      echo "log_type warning"
      echo "log_type error"
    } >> "${MOSQUITTO_DIR}/mosquitto.conf"
    ;;
  error)
    echo "log_type error" >> "${MOSQUITTO_DIR}/mosquitto.conf"
    ;;
  warning|*)
    {
      echo "log_type warning"
      echo "log_type error"
    } >> "${MOSQUITTO_DIR}/mosquitto.conf"
    ;;
esac

if id mosquitto >/dev/null 2>&1; then
  chown -R mosquitto:mosquitto "${MOSQUITTO_DIR}"
  chmod -R u+rwX,g+rwX "${MOSQUITTO_DIR}"
fi

bashio::log.info "Ingress support is enabled in add-on metadata; frontend API and WebSocket URLs are derived from the browser base path."
bashio::log.info "Frontend public base path is browser-derived (direct /, ingress /api/hassio_ingress/<redacted>/)."
bashio::log.info "Frontend API path template: <browser-base>/api/..."
bashio::log.info "Frontend WebSocket endpoint: <browser-base> with HTTP Upgrade."
bashio::log.info "Map region: ${MAP_REGION}; map center: ${MAP_CENTER_JSON}; MQTT fallback region: ${MQTT_REGION}."

if [ "$(jq -r '.debug_startup // false' "${OPTIONS_PATH}")" = "true" ]; then
  bashio::log.info "[startup] Generated config path: ${CONFIG_PATH}"
  bashio::log.info "[startup] CoreScope data path: ${DATA_DIR}"
  bashio::log.info "[startup] CoreScope database path: ${DATA_DIR}/meshcore.db"
  if [ -L /app/data ]; then
    bashio::log.info "[startup] /app/data symlink target: $(readlink /app/data)"
  else
    bashio::log.warning "[startup] /app/data is not a symlink"
  fi
  bashio::log.info "[startup] MQTT listener address: 0.0.0.0:${MQTT_PORT}"
  bashio::log.info "[startup] Ingress mode configured: true"
  bashio::log.info "[startup] Frontend browser base path: derived at runtime"
  bashio::log.info "[startup] Frontend API base path: window.CoreScopeIngress.apiBasePath"
  bashio::log.info "[startup] Frontend WebSocket path: window.CoreScopeIngress.websocketPath"
  bashio::log.info "[startup] Map region: ${MAP_REGION}"
  bashio::log.info "[startup] MQTT fallback/default_region: ${MQTT_REGION}"
  bashio::log.info "[startup] Local Mosquitto enabled: $(jq -r '((.mqtt_enabled // true) and ((.disable_mosquitto // false) | not))' "${OPTIONS_PATH}")"
  bashio::log.info "[startup] External MQTT source count: $(jq -r '(.external_mqtt_sources // []) | length' "${OPTIONS_PATH}")"
  bashio::log.info "[startup] MQTT subscribed topics: $(jq -r '[.mqttSources[]?.topics[]?] | unique | join(", ")' "${CONFIG_PATH}")"
  bashio::log.info "[startup] CoreScope log_level option: ${log_level} (not passed through; upstream does not currently expose a working server or ingestor log-level CLI/env control)"
  bashio::log.info "[startup] Mosquitto log level: ${MOSQUITTO_LOG_LEVEL}"
  bashio::log.info "[startup] corescope-server binary: $(command -v /app/corescope-server || true)"
  bashio::log.info "[startup] corescope-ingestor binary: $(command -v /app/corescope-ingestor || true)"
  bashio::log.info "[startup] mosquitto binary: $(command -v mosquitto || true)"
  bashio::log.info "[startup] Directory permissions:"
  ls -ld /config "${CONFIG_ROOT}" "${DATA_DIR}" "${MOSQUITTO_DIR}" | while read -r line; do
    bashio::log.info "[startup] ${line}"
  done
  bashio::log.info "[startup] MQTT sources redacted: $(jq -c '[.mqttSources[]? | {name, broker:((.broker // "") | sub("//[^/@]+@"; "//[redacted]@")), topics, region, username:(if has("username") then "[set]" else null end), password:(if has("password") then "[redacted]" else null end)}]' "${CONFIG_PATH}")"
fi
