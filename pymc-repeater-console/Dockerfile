ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm

FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.2.11
ARG BUILD_ARCH=amd64
ARG PYMC_REPEATER_REF=main
ARG PYMC_CONSOLE_REF=main
ARG PYMC_REPEATER_REPO=https://github.com/pyMC-dev/pyMC_Repeater.git
ARG PYMC_CONSOLE_REPO=https://github.com/dmduran12/pymc_console-dist.git

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
  org.opencontainers.image.version="${BUILD_VERSION}" \
  org.opencontainers.image.source="https://github.com/matthew73210/custom-ha-addons" \
  org.opencontainers.image.vendor="matthew73210" \
  org.opencontainers.image.ref.name="${BUILD_VERSION}" \
  org.opencontainers.image.pymc_repeater.repo="${PYMC_REPEATER_REPO}" \
  org.opencontainers.image.pymc_repeater.ref="${PYMC_REPEATER_REF}" \
  org.opencontainers.image.pymc_console.repo="${PYMC_CONSOLE_REPO}" \
  org.opencontainers.image.pymc_console.ref="${PYMC_CONSOLE_REF}" \
  org.opencontainers.image.description="Home Assistant add-on wrapper for pyMC Repeater with pyMC Console"

RUN echo "Building pyMC Repeater + Console add-on wrapper version: ${BUILD_VERSION}" \
  && echo "Build architecture: ${BUILD_ARCH}" \
  && echo "pyMC_Repeater upstream: ${PYMC_REPEATER_REPO} ref=${PYMC_REPEATER_REF}" \
  && echo "pyMC Console dist upstream: ${PYMC_CONSOLE_REPO} ref=${PYMC_CONSOLE_REF}" \
  && echo "Wrapper policy: no manage.sh is run; upstream source/dist files are not patched." \
  && echo "Installing wrapper runtime/build packages for pyMC Repeater + Console" \
  && apt-get update \
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
  && python3 --version \
  && pip3 --version \
  && nginx -v \
  && rrdtool --version \
  && rm -rf /var/lib/apt/lists/*

WORKDIR ${INSTALL_DIR}

RUN echo "Cloning pyMC_Repeater repo: ${PYMC_REPEATER_REPO}" \
  && echo "Cloning pyMC_Repeater ref: ${PYMC_REPEATER_REF}" \
  && git clone --depth 1 --branch "${PYMC_REPEATER_REF}" "${PYMC_REPEATER_REPO}" . \
  && echo "pyMC_Repeater resolved commit: $(git rev-parse HEAD)" \
  && echo "Wrapper policy: not running upstream manage.sh or other install scripts; installing Python package directly."

RUN python3 -m venv --system-site-packages /opt/venv \
  && pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir . \
  && python3 -m pip show pymc-repeater || true \
  && mkdir -p /usr/share/licenses/pymc-repeater \
  && cp LICENSE /usr/share/licenses/pymc-repeater/LICENSE

RUN echo "Copying original pyMC_Repeater web assets without patching upstream files" \
  && mkdir -p "${ORIGINAL_WEB_DIR}" \
  && cp -a "${INSTALL_DIR}/repeater/web/html" "${ORIGINAL_WEB_DIR}/html" \
  && ln -sfn "${ORIGINAL_WEB_DIR}/html" "${ORIGINAL_WEB_DIR}/repeater" \
  && echo "Original web path: ${ORIGINAL_WEB_DIR}"

RUN echo "Cloning pyMC Console dist repo: ${PYMC_CONSOLE_REPO}" \
  && echo "Cloning pyMC Console dist ref: ${PYMC_CONSOLE_REF}" \
  && git clone --depth 1 --branch "${PYMC_CONSOLE_REF}" "${PYMC_CONSOLE_REPO}" /tmp/pymc_console-dist \
  && echo "pyMC Console dist resolved commit: $(git -C /tmp/pymc_console-dist rev-parse HEAD)" \
  && echo "Wrapper policy: copying Console dist as-is; no source or dist patching." \
  && mkdir -p "${CONSOLE_WEB_DIR}" /usr/share/licenses/pymc-console \
  && cp -a /tmp/pymc_console-dist/frontend/dist/. "${CONSOLE_WEB_DIR}/" \
  && cp /tmp/pymc_console-dist/LICENSE /usr/share/licenses/pymc-console/LICENSE \
  && echo "Console web path: ${CONSOLE_WEB_DIR}" \
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
