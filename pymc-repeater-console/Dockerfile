ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm

FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.2.16-dev
ARG BUILD_ARCH=amd64
# Tracks upstream dev for this dev app version because pymc_usb Wi-Fi/TCP
# (`radio_type: pymc_tcp`) is merged there but is not in a tagged release yet.
ARG PYMC_REPEATER_REPO=https://github.com/pyMC-dev/pyMC_Repeater.git
ARG PYMC_REPEATER_REF=dev
ARG PYMC_CORE_REF=3987d3e8863bdf078bc9a9a7e3d29320028f49ee
ARG PYMC_CONSOLE_REF=main
ARG PYMC_CORE_REPO=https://github.com/pyMC-dev/pyMC_core.git
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
  org.opencontainers.image.pymc_core.repo="${PYMC_CORE_REPO}" \
  org.opencontainers.image.pymc_core.ref="${PYMC_CORE_REF}" \
  org.opencontainers.image.pymc_console.repo="${PYMC_CONSOLE_REPO}" \
  org.opencontainers.image.pymc_console.ref="${PYMC_CONSOLE_REF}" \
  org.opencontainers.image.description="Home Assistant add-on wrapper for pyMC Repeater with pyMC Console"

RUN echo "Building pyMC Repeater + Console add-on wrapper version: ${BUILD_VERSION}" \
  && echo "Build architecture: ${BUILD_ARCH}" \
  && echo "pyMC_Repeater upstream: ${PYMC_REPEATER_REPO} ref=${PYMC_REPEATER_REF}" \
  && echo "pyMC_core upstream override: ${PYMC_CORE_REPO} ref=${PYMC_CORE_REF}" \
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
  && git init . \
  && git remote add origin "${PYMC_REPEATER_REPO}" \
  && git fetch --depth 1 origin "${PYMC_REPEATER_REF}" \
  && git checkout --detach FETCH_HEAD \
  && echo "pyMC_Repeater resolved commit: $(git rev-parse HEAD)" \
  && echo "pyMC_Repeater checkout diagnostics:" \
  && git remote -v \
  && git branch -a \
  && git show --no-patch --oneline HEAD \
  && git log -1 --decorate --oneline \
  && git status \
  && echo "Relevant source diagnostics:" \
  && (grep -n "radio_type" repeater/config.py || true) \
  && (grep -n "pymc_tcp" repeater/config.py || true) \
  && (grep -n "pymc_usb" repeater/config.py || true) \
  && (tail -40 repeater/config.py || true) \
  && (cat pyproject.toml | grep -n "pymc_core" || true) \
  && echo "Verifying checked-out pyMC_Repeater source contains pymc_tcp runtime support" \
  && if ! grep -q 'radio_type == "pymc_tcp"' repeater/config.py; then \
       echo "ERROR: checked-out pyMC_Repeater does not support radio_type=pymc_tcp"; \
       echo "Remote:"; \
       git remote -v; \
       echo "HEAD:"; \
       git show --no-patch --oneline HEAD; \
       echo "Available remote refs:"; \
       git ls-remote --heads origin || true; \
       echo "Relevant config.py matches:"; \
       grep -n "radio_type" repeater/config.py || true; \
       grep -n "pymc" repeater/config.py || true; \
       tail -80 repeater/config.py || true; \
       exit 1; \
     fi \
  && echo "Wrapper policy: not running upstream manage.sh or other install scripts; installing Python package directly."

RUN python3 -m venv --system-site-packages /opt/venv \
  && pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir . \
  && pip install --no-cache-dir --force-reinstall "pymc_core[hardware] @ git+${PYMC_CORE_REPO}@${PYMC_CORE_REF}" \
  && python3 -m pip show pymc-repeater \
  && python3 -m pip show pymc-core \
  && mkdir -p /usr/share/licenses/pymc-repeater \
  && cp "${INSTALL_DIR}/LICENSE" /usr/share/licenses/pymc-repeater/LICENSE

RUN cd / \
  && python3 - <<'PY'
import inspect
import repeater.config as config

src = inspect.getsource(config)
if 'radio_type == "pymc_tcp"' not in src:
    raise SystemExit("ERROR: installed repeater.config does not contain pymc_tcp radio_type support")

print("OK: installed repeater.config supports radio_type=pymc_tcp")
print("repeater.config path:", config.__file__)
PY

RUN cd / \
  && python3 - <<'PY'
try:
    from pymc_core.hardware.tcp_radio import TCPLoRaRadio
except Exception as exc:
    raise SystemExit(f"ERROR: installed pyMC_core lacks TCPLoRaRadio: {exc}") from exc

print("OK: installed pyMC_core has TCPLoRaRadio")
print("TCPLoRaRadio:", TCPLoRaRadio)
PY

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
