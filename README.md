# WCP Widget — Weather Ticker

A [Widget Context Protocol (WCP)](https://widgetcontextprotocol.com) widget that displays
live weather, date, and time for any location worldwide. Powered by
[Open-Meteo](https://open-meteo.com/) — free, no API key required.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com)  
**Part of the** [Penrith Beacon WCP](https://penrithbeacon.com) widget suite.

> **WCP 1.4.0 certified.** This widget implements the full
> [Widget Context Protocol 1.4.0](https://widgetcontextprotocol.com) specification,
> including server UUID, Container Directory (`GET /wcp`), and all four `Wcp-*` request headers.

**Port:** 3739  
**Powered by:** [Open-Meteo](https://open-meteo.com/) — free, no API key required.

## Quick Start

```bash
docker compose up --build -d
```

Configure at: Dashboard → Settings → Masthead Tickers → Add → Widget → `http://localhost:3739`

## WCP Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /widget/` | 60px scrolling ticker (masthead view) |
| `GET /widget/wcp` | WCP 1.1.0 manifest with configuration form |
| `GET /widget/health` | Health check |
| `GET /widget/full` | Full-page weather detail |
| `GET /widget/api/search?q=` | Location search |
| `GET /widget/api/weather` | Current weather for configured location |
| `POST /widget/configure` | Save configuration |

## Ticker Format

```
📍 Penrith, England, GB   📅 Sun 1 Jun 2026   🕐 14:32   ⛅ 18°C  Partly Cloudy   💨 12 km/h   💧 72%   UV 3
```
