ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:bookworm

FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.3.2
ARG BUILD_ARCH=amd64
ARG BUILD_DATE=
ARG PYMC_REPEATER_REPO=https://github.com/pyMC-dev/pyMC_Repeater.git
ARG PYMC_REPEATER_REF=e17d1137ab2d2d5b86d03c99523272289b7688aa
ARG PYMC_CORE_REF=330e32d57b9321afd63c38e634fa076a5049afee
ARG PYMC_CONSOLE_REF=2d961cef1ae1a355eb06e34fba99788d9ffca44a
ARG PYMC_CORE_REPO=https://github.com/pyMC-dev/pyMC_core.git
ARG PYMC_CONSOLE_REPO=https://github.com/dmduran12/pymc_console-dist.git

ENV INSTALL_DIR=/opt/pymc_repeater \
    CONSOLE_WEB_DIR=/opt/pymc_console/web/html \
    ORIGINAL_WEB_DIR=/opt/pymc_repeater_original_web \
    PYMC_REPEATER_CONFIG=/config/pymc-repeater/config.yaml \
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
  org.opencontainers.image.pymc_upstream_metadata="/usr/share/pymc-repeater-console/upstream-build-info.json" \
  org.opencontainers.image.description="Home Assistant add-on wrapper for pyMC Repeater with pyMC Console"

RUN echo "Building pyMC Repeater + Console add-on wrapper version: ${BUILD_VERSION}" \
  && echo "Build architecture: ${BUILD_ARCH}" \
  && echo "pyMC_Repeater upstream: ${PYMC_REPEATER_REPO} ref=${PYMC_REPEATER_REF}" \
  && echo "pyMC_core upstream: ${PYMC_CORE_REPO} ref=${PYMC_CORE_REF}" \
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
  && echo "Requested pyMC_Repeater ref: ${PYMC_REPEATER_REF}" \
  && git init . \
  && git remote add origin "${PYMC_REPEATER_REPO}" \
  && if ! git fetch --depth 1 origin "${PYMC_REPEATER_REF}"; then \
       echo "ERROR: unable to resolve pyMC_Repeater ref ${PYMC_REPEATER_REF} from ${PYMC_REPEATER_REPO}"; \
       exit 1; \
     fi \
  && git checkout --detach FETCH_HEAD \
  && git rev-parse HEAD > /tmp/pymc_repeater_resolved_sha \
  && echo "Resolved pyMC_Repeater commit SHA: $(cat /tmp/pymc_repeater_resolved_sha)" \
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
  && echo "Verifying checked-out pyMC_Repeater source contains pymc_tcp and pymc_usb runtime support" \
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
  && if ! grep -q 'radio_type == "pymc_usb"' repeater/config.py; then \
       echo "ERROR: checked-out pyMC_Repeater does not support radio_type=pymc_usb"; \
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

RUN echo "Cloning pyMC_core repo: ${PYMC_CORE_REPO}" \
  && echo "Requested pyMC_core ref: ${PYMC_CORE_REF}" \
  && mkdir -p /tmp/pymc_core-src \
  && git -C /tmp/pymc_core-src init . \
  && git -C /tmp/pymc_core-src remote add origin "${PYMC_CORE_REPO}" \
  && if ! git -C /tmp/pymc_core-src fetch --depth 1 origin "${PYMC_CORE_REF}"; then \
       echo "ERROR: unable to resolve pyMC_core ref ${PYMC_CORE_REF} from ${PYMC_CORE_REPO}"; \
       exit 1; \
     fi \
  && git -C /tmp/pymc_core-src checkout --detach FETCH_HEAD \
  && git -C /tmp/pymc_core-src rev-parse HEAD > /tmp/pymc_core_resolved_sha \
  && echo "Resolved pyMC_core commit SHA: $(cat /tmp/pymc_core_resolved_sha)" \
  && git -C /tmp/pymc_core-src show --no-patch --oneline HEAD

RUN python3 -m venv --system-site-packages /opt/venv \
  && pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir . \
  && pip install --no-cache-dir --force-reinstall "/tmp/pymc_core-src[hardware]" \
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
if 'radio_type == "pymc_usb"' not in src:
    raise SystemExit("ERROR: installed repeater.config does not contain pymc_usb radio_type support")

print("OK: installed repeater.config supports radio_type=pymc_tcp and radio_type=pymc_usb")
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
  && echo "Requested pyMC Console dist ref: ${PYMC_CONSOLE_REF}" \
  && mkdir -p /tmp/pymc_console-dist \
  && git -C /tmp/pymc_console-dist init . \
  && git -C /tmp/pymc_console-dist remote add origin "${PYMC_CONSOLE_REPO}" \
  && if ! git -C /tmp/pymc_console-dist fetch --depth 1 origin "${PYMC_CONSOLE_REF}"; then \
       echo "ERROR: unable to resolve pyMC Console dist ref ${PYMC_CONSOLE_REF} from ${PYMC_CONSOLE_REPO}"; \
       exit 1; \
     fi \
  && git -C /tmp/pymc_console-dist checkout --detach FETCH_HEAD \
  && git -C /tmp/pymc_console-dist rev-parse HEAD > /tmp/pymc_console_resolved_sha \
  && if [ -f /tmp/pymc_console-dist/frontend/dist/VERSION ]; then cat /tmp/pymc_console-dist/frontend/dist/VERSION > /tmp/pymc_console_version; else printf '' > /tmp/pymc_console_version; fi \
  && echo "Resolved pyMC Console dist commit SHA: $(cat /tmp/pymc_console_resolved_sha)" \
  && if [ -s /tmp/pymc_console_version ]; then echo "pyMC Console dist version: $(cat /tmp/pymc_console_version)"; else echo "pyMC Console dist version: unavailable"; fi \
  && echo "Wrapper policy: copying Console dist as-is; no source or dist patching." \
  && mkdir -p "${CONSOLE_WEB_DIR}" /usr/share/licenses/pymc-console \
  && cp -a /tmp/pymc_console-dist/frontend/dist/. "${CONSOLE_WEB_DIR}/" \
  && cp /tmp/pymc_console-dist/LICENSE /usr/share/licenses/pymc-console/LICENSE \
  && echo "Console web path: ${CONSOLE_WEB_DIR}"

RUN mkdir -p /usr/share/pymc-repeater-console \
  && BUILD_VERSION="${BUILD_VERSION}" BUILD_ARCH="${BUILD_ARCH}" BUILD_DATE="${BUILD_DATE}" \
     PYMC_REPEATER_REPO="${PYMC_REPEATER_REPO}" PYMC_REPEATER_REF="${PYMC_REPEATER_REF}" \
     PYMC_CORE_REPO="${PYMC_CORE_REPO}" PYMC_CORE_REF="${PYMC_CORE_REF}" \
     PYMC_CONSOLE_REPO="${PYMC_CONSOLE_REPO}" PYMC_CONSOLE_REF="${PYMC_CONSOLE_REF}" \
     python3 - <<'PY'
import datetime
import json
import os
import pathlib

metadata_path = pathlib.Path("/usr/share/pymc-repeater-console/upstream-build-info.json")
build_date = os.environ.get("BUILD_DATE", "").strip()
if not build_date:
    build_date = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def read_text(path):
    return pathlib.Path(path).read_text(encoding="utf-8").strip()

metadata = {
    "schema_version": 1,
    "wrapper_app": "pymc-repeater-console",
    "wrapper_version": os.environ.get("BUILD_VERSION", ""),
    "build_arch": os.environ.get("BUILD_ARCH", ""),
    "build_date": build_date,
    "pymc_repeater": {
        "repository": os.environ["PYMC_REPEATER_REPO"],
        "requested_ref": os.environ["PYMC_REPEATER_REF"],
        "resolved_sha": read_text("/tmp/pymc_repeater_resolved_sha"),
    },
    "pymc_core": {
        "repository": os.environ["PYMC_CORE_REPO"],
        "requested_ref": os.environ["PYMC_CORE_REF"],
        "resolved_sha": read_text("/tmp/pymc_core_resolved_sha"),
    },
    "pymc_console_dist": {
        "repository": os.environ["PYMC_CONSOLE_REPO"],
        "requested_ref": os.environ["PYMC_CONSOLE_REF"],
        "resolved_sha": read_text("/tmp/pymc_console_resolved_sha"),
        "version": read_text("/tmp/pymc_console_version"),
    },
    "note": "Wrapper diagnostic build metadata only. This is not upstream API data and must not be used to alter pyMC runtime behavior.",
}

metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN python3 -m json.tool /usr/share/pymc-repeater-console/upstream-build-info.json \
  && rm -rf /tmp/pymc_console-dist /tmp/pymc_core-src

COPY rootfs /

RUN chmod a+x \
    /etc/cont-init.d/pymc-repeater.sh \
    /etc/s6-overlay/s6-rc.d/pymc-repeater-ingress/run \
    /etc/s6-overlay/s6-rc.d/pymc-repeater-ingress/finish \
    /etc/s6-overlay/s6-rc.d/pymc-repeater/run \
    /etc/s6-overlay/s6-rc.d/pymc-repeater/finish \
  && mkdir -p /config/pymc-repeater /data/pymc-repeater /run/nginx

EXPOSE 8080
