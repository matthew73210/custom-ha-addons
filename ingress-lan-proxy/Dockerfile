ARG BUILD_FROM=ghcr.io/home-assistant/base:latest

FROM ${BUILD_FROM}

ARG BUILD_VERSION
ARG BUILD_ARCH

SHELL ["/bin/ash", "-o", "pipefail", "-c"]

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/matthew73210/custom-ha-addons" \
  org.opencontainers.image.description="Home Assistant Ingress proxy for LAN web services"

RUN apk add --no-cache jq nginx \
  && rm -f /etc/nginx/http.d/default.conf

COPY rootfs /

RUN chmod +x /etc/cont-init.d/00-nginx-config \
  && chmod +x /etc/services.d/nginx/run \
  && mkdir -p /run/nginx /etc/nginx/http.d
