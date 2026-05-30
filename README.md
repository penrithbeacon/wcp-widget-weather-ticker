# wcp-widget-weather-ticker

WCP 1.1.0 widget: Live weather + date/time masthead ticker.

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
