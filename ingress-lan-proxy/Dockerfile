ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.1.0
ARG BUILD_ARCH=amd64

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/matthew73210/custom-ha-addons" \
  org.opencontainers.image.description="Home Assistant Ingress proxy for LAN web services"

RUN apk add --no-cache jq nginx \
  && rm -f /etc/nginx/http.d/default.conf

COPY rootfs /

RUN chmod a+x \
    /etc/cont-init.d/00-nginx-config \
    /etc/services.d/nginx/run \
  && mkdir -p /run/nginx /etc/nginx/http.d
