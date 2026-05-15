ARG BUILDPLATFORM=linux/amd64

FROM --platform=${BUILDPLATFORM} golang:1.22-alpine AS builder

ARG APP_VERSION=0.1.0
ARG BUILD_TIME=unknown
ARG CORESCOPE_REF=master
ARG GIT_COMMIT=unknown
ARG TARGETARCH
ARG TARGETOS

RUN apk add --no-cache ca-certificates git

WORKDIR /src
RUN git clone --depth 1 https://github.com/Kpa-clawbot/CoreScope.git . \
  && git checkout "${CORESCOPE_REF}"

WORKDIR /build/server
RUN cp /src/cmd/server/go.mod /src/cmd/server/go.sum ./ \
  && mkdir -p ../../internal \
  && cp -R /src/internal/geofilter /src/internal/sigvalidate /src/internal/packetpath /src/internal/dbconfig /src/internal/perfio ../../internal/ \
  && go mod download
RUN cp -R /src/cmd/server/. ./ \
  && CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} \
    go build -ldflags "-X main.Version=${APP_VERSION} -X main.Commit=${GIT_COMMIT} -X main.BuildTime=${BUILD_TIME}" -o /corescope-server .

WORKDIR /build/ingestor
RUN cp /src/cmd/ingestor/go.mod /src/cmd/ingestor/go.sum ./ \
  && mkdir -p ../../internal \
  && cp -R /src/internal/geofilter /src/internal/sigvalidate /src/internal/packetpath /src/internal/dbconfig /src/internal/perfio ../../internal/ \
  && go mod download
RUN cp -R /src/cmd/ingestor/. ./ \
  && CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} \
    go build -o /corescope-ingestor .

WORKDIR /build/decrypt
RUN cp /src/cmd/decrypt/go.mod /src/cmd/decrypt/go.sum ./ \
  && mkdir -p ../../internal \
  && cp -R /src/internal/channel ../../internal/ \
  && go mod download
RUN cp -R /src/cmd/decrypt/. ./ \
  && CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} \
    go build -ldflags="-s -w" -o /corescope-decrypt .

FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION=0.1.0
ARG BUILD_ARCH=amd64

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/matthew73210/custom-ha-addons" \
  org.opencontainers.image.description="Home Assistant add-on wrapper for CoreScope"

RUN apk add --no-cache ca-certificates caddy jq mosquitto mosquitto-clients

WORKDIR /app

COPY --from=builder /corescope-server /corescope-ingestor /corescope-decrypt /app/
COPY --from=builder /src/public /app/public
COPY --from=builder /src/config.example.json /app/config.example.json
COPY --from=builder /src/channel-rainbow.json /app/channel-rainbow.json
COPY --from=builder /src/LICENSE /usr/share/licenses/corescope/LICENSE
COPY rootfs /

RUN chmod a+x /etc/services.d/corescope/run \
    /etc/services.d/corescope-caddy/run \
    /etc/services.d/corescope-ingestor/run \
    /etc/services.d/corescope-mosquitto/run \
    /etc/cont-init.d/corescope.sh \
  && mkdir -p /app/data /config/data /config/mosquitto /config/caddy /config/run

EXPOSE 80 1883
