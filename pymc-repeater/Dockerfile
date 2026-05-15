ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm

FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.2.1
ARG BUILD_ARCH=amd64
ARG PYMC_REPEATER_REF=main

ENV INSTALL_DIR=/opt/pymc_repeater \
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
  org.opencontainers.image.description="Home Assistant add-on wrapper for pyMC Repeater"

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    jq \
    libffi-dev \
    libusb-1.0-0 \
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

COPY rootfs /tmp/rootfs

RUN cp /tmp/rootfs/opt/pymc_repeater/ha-ingress.js repeater/web/html/ha-ingress.js \
  && sed -i \
    -e 's#href="/favicon.ico"#href="favicon.ico"#g' \
    -e 's#src="/assets/#src="assets/#g' \
    -e 's#href="/assets/#href="assets/#g' \
    -e 's#<script type="module"#<script src="ha-ingress.js"></script>\n    <script type="module"#' \
    repeater/web/html/index.html \
  && python3 /tmp/rootfs/opt/pymc_repeater/patch-web-ui.py

RUN python3 -m venv --system-site-packages /opt/venv \
  && pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir . \
  && mkdir -p /usr/share/licenses/pymc-repeater \
  && cp LICENSE /usr/share/licenses/pymc-repeater/LICENSE

COPY rootfs /

RUN chmod a+x \
    /etc/cont-init.d/pymc-repeater.sh \
    /etc/services.d/pymc-repeater/run \
    /etc/services.d/pymc-repeater/finish \
  && mkdir -p /config/pymc-repeater /data/pymc-repeater

EXPOSE 8000
