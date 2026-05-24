ARG BUILD_FROM

FROM ${BUILD_FROM}

ARG BUILD_VERSION
ARG BUILD_ARCH

SHELL ["/bin/ash", "-o", "pipefail", "-c"]

RUN apk add --no-cache jq nginx \
  && rm -f /etc/nginx/http.d/default.conf

COPY rootfs /

RUN chmod +x /etc/cont-init.d/00-nginx-config \
  && chmod +x /etc/services.d/nginx/run \
  && mkdir -p /run/nginx /etc/nginx/http.d
