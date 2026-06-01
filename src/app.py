"""
WCP Widget: Weather Ticker
Widget Context Protocol 1.1.0 — Weather + Date/Time masthead ticker
Powered by Open-Meteo (free, no API key required)
Port: 3739
"""

import json
import os
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

# ── WMO weather code → (emoji, description) ──────────────────────────────────

WMO = {
    0:  ("☀️",  "Clear sky"),
    1:  ("🌤️", "Mainly clear"),
    2:  ("⛅",  "Partly cloudy"),
    3:  ("☁️",  "Overcast"),
    45: ("🌫️", "Fog"),
    48: ("🌫️", "Icy fog"),
    51: ("🌦️", "Light drizzle"),
    53: ("🌦️", "Drizzle"),
    55: ("🌧️", "Heavy drizzle"),
    61: ("🌧️", "Light rain"),
    63: ("🌧️", "Rain"),
    65: ("🌧️", "Heavy rain"),
    71: ("🌨️", "Light snow"),
    73: ("🌨️", "Snow"),
    75: ("❄️",  "Heavy snow"),
    77: ("🌨️", "Snow grains"),
    80: ("🌧️", "Rain showers"),
    81: ("🌧️", "Showers"),
    82: ("⛈️",  "Heavy showers"),
    85: ("🌨️", "Snow showers"),
    86: ("❄️",  "Heavy snow showers"),
    95: ("⛈️",  "Thunderstorm"),
    96: ("⛈️",  "Thunderstorm + hail"),
    99: ("⛈️",  "Thunderstorm + hail"),
}

# ── Config helpers ────────────────────────────────────────────────────────────

def read_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def write_config(data):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ── WCP Manifest ─────────────────────────────────────────────────────────────

WCP_MANIFEST = {
    "wcp": "1.3.0",
    "name": "Weather Ticker",
    "version": "1.1.0",
    "description": (
        "Live weather, date and time ticker for any location worldwide. "
        "Powered by Open-Meteo — free, no API key required."
    ),
    "icon": "/widget/icon.svg",
    "health": "/widget/health",
    "configuration": {
        "submitEndpoint": "/widget/configure",
        "fields": [
            {
                "key": "location",
                "type": "location-search",
                "label": "Location",
                "placeholder": "Type a city name…",
                "searchEndpoint": "/widget/api/search?q={query}",
                "resultDisplay": "{name}, {admin1}, {country}",
                "resultValue": ["latitude", "longitude", "name", "country_code", "admin1"],
            },
            {
                "key": "units",
                "type": "select",
                "label": "Temperature Units",
                "options": [
                    {"value": "celsius",    "label": "°C — Celsius"},
                    {"value": "fahrenheit", "label": "°F — Fahrenheit"},
                ],
                "default": "celsius",
            },
            {
                "key": "refresh_interval",
                "type": "number",
                "label": "Refresh every (seconds)",
                "min": 300,
                "max": 7200,
                "default": 900,
            },
        ],
    },
    "pages": [
        {
            "id":          "full",
            "path":        "/widget/full",
            "title":       "Weather Detail",
            "description": "Full weather breakdown for the configured location.",
            "window":      {"width": 600, "height": 500},
        }
    ],
    "actions": [
        {
            "id":    "open-full-window",
            "type":  "wcp:open-window",
            "label": "Weather Detail",
            "page":  "full",
        },
        {
            "id":      "open-full-tab",
            "type":    "wcp:open-tab",
            "label":   "Open in New Tab",
            "page":    "full",
            "tab":     {"title": "Weather", "icon": "/widget/icon.svg"},
            "persist": False,
        },
    ],
    "components": [
        {
            "id": "weather-widget", "uuid": "3c138659-6100-4321-b1d7-7e556213031a", "name": "Weather Ticker", "role": "widget",
            "path": "/widget/", "icon": "/widget/icon.svg",
            "renderMode": "iframe", "defaultSize": {"w": 6, "h": 2},
        },
        {
            "id": "weather-ticker", "uuid": "c8fdf59c-70b6-416a-a3b6-1dc0788e7989", "name": "Weather Masthead Ticker", "role": "ticker",
            "path": "/widget/", "icon": "/widget/icon.svg",
            "mastheadCapable": True, "size": {"min": 40, "max": 60},
        },
    ],
}

# ── WCP Endpoints ─────────────────────────────────────────────────────────────

@app.route("/widget/")
@app.route("/widget/index.html")
def widget_ticker():
    cfg = read_config()
    return render_template("widget.html", manifest=WCP_MANIFEST, config=cfg)

@app.route("/widget/wcp")
def widget_wcp():
    return jsonify(WCP_MANIFEST)

@app.route("/widget/manifest")
def widget_manifest():
    m = WCP_MANIFEST
    return jsonify({
        "wcp": m["wcp"], "name": m["name"], "version": m["version"],
        "description": m["description"], "icon": m["icon"],
        "health": m["health"], "components": m["components"],
    })

@app.route("/widget/health")
def widget_health():
    return jsonify({"status": "ok", "name": WCP_MANIFEST["name"]})

@app.route("/widget/full")
def widget_full():
    cfg = read_config()
    return render_template("full.html", manifest=WCP_MANIFEST, config=cfg)

@app.route("/widget/icon.svg")
def widget_icon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <path fill="#f0883e" d="M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0zm0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13zm8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5zM3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8zm10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0zm-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0zm9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707zM4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .708z"/>
</svg>"""
    return Response(svg, mimetype="image/svg+xml")

# ── Configuration ─────────────────────────────────────────────────────────────

@app.route("/widget/configure", methods=["POST"])
def widget_configure():
    try:
        data = request.get_json(force=True) or {}
        write_config(data)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Location search (proxies Open-Meteo geocoding) ────────────────────────────

@app.route("/widget/api/search")
def location_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": q, "count": 10, "language": "en", "format": "json"},
            timeout=8,
        )
        data = r.json()
        results = []
        for item in data.get("results", []):
            results.append({
                "name":         item.get("name", ""),
                "admin1":       item.get("admin1", ""),
                "country":      item.get("country", ""),
                "country_code": item.get("country_code", ""),
                "latitude":     item.get("latitude"),
                "longitude":    item.get("longitude"),
            })
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

# ── Weather data ──────────────────────────────────────────────────────────────

@app.route("/widget/api/weather")
def get_weather():
    cfg = read_config()
    loc = cfg.get("location")
    if not loc or not loc.get("latitude"):
        return jsonify({"error": "no_location", "message": "Location not configured"})

    units = cfg.get("units", "celsius")
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":         loc["latitude"],
                "longitude":        loc["longitude"],
                "current":          "temperature_2m,relative_humidity_2m,weathercode,windspeed_10m,uv_index",
                "wind_speed_unit":  "kmh",
                "temperature_unit": units,
                "timezone":         "auto",
            },
            timeout=8,
        )
        data = r.json()
        cur  = data.get("current", {})
        code = cur.get("weathercode", 0)
        icon, desc = WMO.get(code, ("🌡️", "Unknown"))
        unit_sym = "°C" if units == "celsius" else "°F"

        # Use the location's UTC offset from Open-Meteo so time is local, not UTC
        utc_offset = data.get("utc_offset_seconds", 0)
        local_tz   = timezone(timedelta(seconds=utc_offset))
        now        = datetime.now(local_tz)

        return jsonify({
            "location":    f"{loc.get('name', '')}, {loc.get('admin1', '')}, {loc.get('country_code', '')}",
            "date":        now.strftime("%a %-d %b %Y"),
            "time":        now.strftime("%H:%M"),
            "icon":        icon,
            "description": desc,
            "temperature": f"{round(cur.get('temperature_2m', 0))}{unit_sym}",
            "humidity":    f"{round(cur.get('relative_humidity_2m', 0))}%",
            "wind":        f"{round(cur.get('windspeed_10m', 0))} km/h",
            "uv":          str(round(cur.get("uv_index", 0))),
            "refresh_interval": cfg.get("refresh_interval", 900),
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3739, debug=False)
