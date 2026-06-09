# Weather Ticker — Specification

## Overview
Live weather, date and time ticker for any location worldwide. Powered by Open-Meteo — free, no API key required.

- **Port:** 3739
- **Container:** `wcp-widget-weather-ticker`
- **Image:** `docker.io/penrithbeacon/wcp-widget-weather-ticker`

## Version
- **Widget:** 1.6.0
- **WCP:** 2.1.0
- **Docker tag:** `1.6.0-wcp2.1.0`

## Controls (HTML Templates)

| Template | Route | Purpose | Default Size |
|----------|-------|---------|--------------|
| widget.html | `/widget/` | Compact weather ticker | 6×4 (widget) / masthead (ticker) |
| full.html | `/widget/full` | Full weather detail view | Window: 600×500 |

## Components

| ID | Name | Role | Size |
|----|------|------|------|
| weather-widget | Weather Ticker | widget | 6×4 |
| weather-ticker | Weather Masthead Ticker | widget | (masthead) |

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/wcp` | Container directory |
| GET | `/widget/wcp` | Widget manifest |
| GET | `/widget/index` | Widget index directory |
| GET | `/widget/` | Compact view |
| GET | `/widget/full` | Full detail view |
| GET | `/widget/health` | Health check |
| GET | `/widget/icon.svg` | Widget icon |
| GET | `/widget/manifest` | Lightweight manifest subset |
| GET | `/widget/api/guids` | Component UUIDs |
| GET | `/widget/export.wcp` | WCP export package |
| GET | `/widget/api/search` | Location autocomplete search |
| GET | `/widget/api/weather` | Fetch weather data |
| POST | `/widget/configure` | Accept location configuration |
| POST | `/widget/publish` | Publish SPA |
| DELETE | `/widget/publish` | Remove published SPA |
| GET | `/` | Serve published SPA |

## Features
- Live weather for any location worldwide
- Date and time display with timezone support
- Location search with autocomplete
- Dashboard configuration for location
- Masthead ticker mode (compact horizontal strip)
- Full-page detail view with forecast
- Publish to Web support

## Configuration
- Location (via `POST /widget/configure`)
- Persisted per orchestration/application context

## Data Persistence
- No named data volume
- Configuration stored in container memory (resets on restart unless volume-mounted)

## Dependencies
- Python: `flask`, `requests`
- External API: Open-Meteo (free, no key required)
