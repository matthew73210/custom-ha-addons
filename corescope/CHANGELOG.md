# Changelog

## 0.1.0

- Initial CoreScope Home Assistant Supervisor add-on package.
- Build CoreScope from upstream source during Docker build.
- Add Home Assistant Ingress support on port 80.
- Persist CoreScope data under the add-on config mount.
- Generate CoreScope `config.json` from add-on options, with advanced custom JSON override support.
- Add optional local Mosquitto listener and external MQTT source configuration.
