# WCP Widget: Weather Ticker

A [Widget Context Protocol (WCP)](https://github.com/penrithbeacon/wcp-widget-weather-ticker)
compliant widget that displays live weather, date, and time for any location worldwide.
Powered by [Open-Meteo](https://open-meteo.com/) — free, no API key required.
Designed to run alongside the **Penrith Beacon WCP Dashboard** or any WCP-compatible host.

## Quick Start

```bash
docker run -d \
  --name wcp-widget-weather-ticker \
  -p 3739:3739 \
  -v weather_config:/app/data \
  --restart unless-stopped \
  penrithbeacon/wcp-widget-weather-ticker:latest
```

Then add it to your WCP dashboard at `http://localhost:3739` and configure your location.

## Docker Compose

```yaml
services:
  weather-ticker:
    image: penrithbeacon/wcp-widget-weather-ticker:latest
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

Configure the widget through your WCP dashboard's widget settings panel, or directly:

```bash
curl -X POST http://localhost:3739/widget/configure \
  -H "Content-Type: application/json" \
  -d '{
    "location": "London, UK",
    "latitude": 51.5074,
    "longitude": -0.1278,
    "units": "celsius",
    "refresh": 15
  }'
```

| Field | Type | Description |
|-------|------|-------------|
| `location` | string | Display name for the location |
| `latitude` | float | Latitude (set automatically via location search) |
| `longitude` | float | Longitude (set automatically via location search) |
| `units` | string | `celsius` or `fahrenheit` |
| `refresh` | integer | Refresh interval in minutes (default: 15) |

## WCP Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /widget/` | Compact ticker widget (iframe) |
| `GET /widget/wcp` | WCP 1.1.0 manifest |
| `GET /widget/health` | Health check |
| `GET /widget/icon.svg` | Widget icon |
| `POST /widget/configure` | Save widget configuration |
| `GET /widget/api/search?q=<city>` | Location autocomplete search |

## WCP Compatibility

| Property | Value |
|----------|-------|
| WCP Version | 1.1.0 |
| Widget Version | 1.0.0 |
| Render mode | iframe |
| Auth | none |
| Default card size | 6×2 |
| Config fields | location-search, select, number |

## Technical Details

- **Base image:** `python:3.12-slim`
- **Port:** `3739`
- **Dependencies:** Flask, requests
- **Weather data:** [Open-Meteo API](https://open-meteo.com/) — free, no API key needed
- **Persistent storage:** Named Docker volume `weather_config` stores location/units preferences
- **Timezone handling:** Uses `utc_offset_seconds` from Open-Meteo for correct local time inside Docker

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release |
| `1.1.0-wcp1.3.0` | Widget v1.1.0, WCP 1.3.0 — adds components array, ticker role |
| `1.0.0-wcp1.1.0` | Widget v1.0.0, WCP protocol v1.1.0 |

## Source

- Docker Hub: [penrithbeacon/wcp-widget-weather-ticker](https://hub.docker.com/r/penrithbeacon/wcp-widget-weather-ticker)
- GitHub: [penrithbeacon/wcp-widget-weather-ticker](https://github.com/penrithbeacon/wcp-widget-weather-ticker)
- WCP Specification: [widgetcontextprotocol.com](https://widgetcontextprotocol.com)
