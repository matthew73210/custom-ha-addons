ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm

FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.2.8
ARG BUILD_ARCH=amd64
ARG PYMC_REPEATER_REF=main
ARG PYMC_CONSOLE_REF=main

ENV INSTALL_DIR=/opt/pymc_repeater \
    CONSOLE_WEB_DIR=/opt/pymc_console/web/html \
    ORIGINAL_WEB_DIR=/opt/pymc_repeater_original_web \
    PYMC_REPEATER_CONFIG=/etc/pymc_repeater/config.yaml \
    PYTHONUNBUFFERED=1 \
    SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYMC_REPEATER=1.0.5 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/matthew73210/custom-ha-addons" \
  org.opencontainers.image.description="Home Assistant add-on wrapper for pyMC Repeater with pyMC Console"

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    iproute2 \
    jq \
    libffi-dev \
    libusb-1.0-0 \
    nginx \
    python3 \
    python3-dev \
    python3-pip \
    python3-rrdtool \
    python3-venv \
    rrdtool \
    swig \
  && rm -rf /var/lib/apt/lists/*

WORKDIR ${INSTALL_DIR}

RUN git clone --depth 1 --branch "${PYMC_REPEATER_REF}" https://github.com/pyMC-dev/pyMC_Repeater.git .

RUN python3 -m venv --system-site-packages /opt/venv \
  && pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir . \
  && mkdir -p /usr/share/licenses/pymc-repeater \
  && cp LICENSE /usr/share/licenses/pymc-repeater/LICENSE

RUN mkdir -p "${ORIGINAL_WEB_DIR}" \
  && cp -a "${INSTALL_DIR}/repeater/web/html" "${ORIGINAL_WEB_DIR}/html" \
  && ln -sfn "${ORIGINAL_WEB_DIR}/html" "${ORIGINAL_WEB_DIR}/repeater"

RUN git clone --depth 1 --branch "${PYMC_CONSOLE_REF}" https://github.com/dmduran12/pymc_console-dist.git /tmp/pymc_console-dist \
  && mkdir -p "${CONSOLE_WEB_DIR}" /usr/share/licenses/pymc-console \
  && cp -a /tmp/pymc_console-dist/frontend/dist/. "${CONSOLE_WEB_DIR}/" \
  && cp /tmp/pymc_console-dist/LICENSE /usr/share/licenses/pymc-console/LICENSE \
  && rm -rf /tmp/pymc_console-dist

COPY rootfs /

RUN chmod a+x \
    /etc/cont-init.d/pymc-repeater.sh \
    /etc/s6-overlay/s6-rc.d/pymc-repeater-ingress/run \
    /etc/s6-overlay/s6-rc.d/pymc-repeater-ingress/finish \
    /etc/s6-overlay/s6-rc.d/pymc-console-compat-api/run \
    /etc/s6-overlay/s6-rc.d/pymc-console-compat-api/finish \
    /etc/s6-overlay/s6-rc.d/pymc-repeater/run \
    /etc/s6-overlay/s6-rc.d/pymc-repeater/finish \
  && mkdir -p /config/pymc-repeater /data/pymc-repeater /run/nginx

EXPOSE 8080
