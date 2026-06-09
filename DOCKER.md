# WCP Widget: Weather Ticker

A [Widget Context Protocol (WCP)](https://widgetcontextprotocol.com) compliant widget that displays
live weather, date, and time for any location worldwide. Powered by
[Open-Meteo](https://open-meteo.com/) — free, no API key required. Designed to run alongside
any WCP-compatible host dashboard.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com)

## Quick Start

```bash
docker run -d \
  --name wcp-widget-weather-ticker \
  -p 3739:3739 \
  -v weather_config:/app/data \
  --restart unless-stopped \
  docker.io/penrithbeacon/wcp-widget-weather-ticker:latest
```

Then add it to your WCP dashboard at the container's network address and configure your location.

## Docker Compose

```yaml
services:
  weather-ticker:
    image: docker.io/penrithbeacon/wcp-widget-weather-ticker:latest
    container_name: wcp-widget-weather-ticker
    ports:
      - "3739:3739"
    restart: unless-stopped
    volumes:
      - weather_config:/app/data

volumes:
  weather_config:
```

## Configuration

Configure the widget through your WCP dashboard's widget settings panel. The dashboard reads
the `config` array from the manifest (`GET /widget/wcp`), builds a settings form, and POSTs
the completed values to `/widget/configure` with the `Wcp-Instance-Id` header.

| Field | Type | Description |
|-------|------|-------------|
| `location` | autocomplete | Live search — returns matching cities from Open-Meteo geocoding |
| `units` | select | `celsius` or `fahrenheit` |
| `refresh_interval` | number | Refresh interval in seconds (300–7200, default 900) |

## WCP Request Headers

This widget supports the WCP 2.0.0 request headers:

| Header | Required | Description |
|--------|----------|-------------|
| `Wcp-Instance-Id` | Required | UUID identifying this widget instance — enables multi-instance configuration |
| `Wcp-Dashboard-Id` | Optional | UUID identifying the requesting dashboard |
| `Wcp-Version` | Optional | Protocol version the dashboard speaks |
| `Wcp-Widget-Id` | Optional | Widget ID from Container Directory selection |
| `Wcp-Orchestration-Id` | Optional | UUID of the active orchestration — shared state key for multi-component coordination |
| `Wcp-Application-Id` | Optional | UUID of the active application window (kiosk only) — combined with orchestration ID for full isolation |

## WCP Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /wcp` | WCP 2.0.0 Container Directory |
| `GET /widget/` | Compact ticker widget (iframe) |
| `GET /widget/wcp` | WCP 2.0.0 manifest |
| `GET /widget/health` | Health check |
| `GET /widget/icon.svg` | Widget icon (SVG) |
| `GET /widget/full` | Full weather detail page |
| `POST /widget/configure` | Save widget configuration (per instance) |
| `GET /widget/api/search?q=<query>` | Location autocomplete — returns JSON string array |
| `GET /widget/api/weather` | Current weather data — accepts inline `lat`, `lon`, `units` params |

## WCP Compatibility

| Property | Value |
|----------|-------|
| WCP Version | 2.1.0 |
| Widget Version | 1.6.0 |
| Render mode | iframe |
| Auth | none |
| Default card size | 6×2 |
| Config fields | autocomplete, select, number |
| Multi-instance | Yes — configuration keyed by `Wcp-Instance-Id` |

## Technical Details

- **Base image:** `python:3.12-slim`
- **Platforms:** `linux/amd64`, `linux/arm64`
- **Port:** `3739`
- **Dependencies:** Flask, requests
- **Weather data:** [Open-Meteo API](https://open-meteo.com/) — free, no API key needed
- **Persistent storage:** Named Docker volume `weather_config` stores per-instance configurations
- **Timezone handling:** Uses `utc_offset_seconds` from Open-Meteo for correct local time inside Docker

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release — multi-arch (`linux/amd64`, `linux/arm64`) |
| `1.5.0-wcp2.1.0` | Widget v1.5.0, WCP 2.1.0 — `/widget/health` returns `container` name |
| `1.4.0-wcp2.1.0` | Widget v1.4.0, WCP 2.1.0 — WCP 2.1.0 upgrade, orchestration ID context |
| `1.3.0-wcp2.0.0` | Widget v1.3.0, WCP 2.0.0 — container block, manifest image source |
| `1.2.1-wcp1.4.0` | Widget v1.2.1, WCP 2.0.0 — server UUID, Container Directory, Wcp-Widget-Id |
| `1.2.0-wcp1.3.1` | Widget v1.2.0, WCP 1.3.1 — multi-instance headers, autocomplete config type |
| `1.1.0-wcp1.3.0` | Widget v1.1.0, WCP 1.3.0 — components array, ticker role |

> **Platform history:** `latest` was rebuilt as a multi-arch image on 2026-06-05, adding `linux/amd64` support (Synology NAS, Intel/AMD servers). All version-specific tags (`1.1.0-wcp1.3.0` through `1.3.0-wcp2.0.0`) were originally built on Apple Silicon and are `linux/arm64` only.

## Source

- Docker Hub: [penrithbeacon/wcp-widget-weather-ticker](https://hub.docker.com/r/penrithbeacon/wcp-widget-weather-ticker)
- GitHub: [penrithbeacon/wcp-widget-weather-ticker](https://github.com/penrithbeacon/wcp-widget-weather-ticker)
- WCP Specification: [widgetcontextprotocol.com](https://widgetcontextprotocol.com)
