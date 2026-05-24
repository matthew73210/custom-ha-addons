# Ingress LAN Proxy

Ingress LAN Proxy exposes one local LAN HTTP or HTTPS web UI through Home Assistant Ingress. Home Assistant handles authentication and the secure connection in front of the add-on; the add-on runs Nginx internally and proxies requests to the target you configure.

This add-on does not expose a normal external port by default. Ingress points to the internal Nginx listener on port `8099`.

## Configuration

Default options:

```yaml
target_scheme: http
target_host: 192.168.1.50
target_port: 80
verify_ssl: false
```

Options:

- `target_scheme`: Protocol used to reach the LAN service. Set to `http` or `https`.
- `target_host`: IP address or DNS name of the LAN service.
- `target_port`: Port of the LAN service.
- `verify_ssl`: Whether Nginx should verify the upstream certificate when `target_scheme` is `https`.

## Usage

1. Add this repository to the Home Assistant app store.
2. Install the `Ingress LAN Proxy` add-on.
3. Set the target service options, for example:

   ```yaml
   target_scheme: http
   target_host: 192.168.1.x
   target_port: 80
   verify_ssl: false
   ```

4. Start the add-on.
5. Open the web UI from Home Assistant using the add-on's `LAN Proxy` ingress panel.

## Notes

This add-on is intended for LAN web UIs that tolerate reverse proxying. Some applications use hardcoded absolute paths, redirects, cookies, or browser security settings that may need additional rewrites or app-specific proxy configuration.

When `target_scheme` is `https` and `verify_ssl` is `false`, the generated Nginx configuration sets `proxy_ssl_verify off`.

## Prebuilt Images

Home Assistant pulls prebuilt images from GitHub Container Registry:

```text
ghcr.io/matthew73210/ingress-lan-proxy-{arch}
```

The GitHub Actions workflow publishes `amd64` and `aarch64` images tagged with the add-on version plus `latest`.
