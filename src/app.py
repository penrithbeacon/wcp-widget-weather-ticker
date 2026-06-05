"""
WCP Widget: Weather Ticker
Widget Context Protocol 1.4.0 compliant — Weather + Date/Time masthead ticker
Powered by Open-Meteo (free, no API key required)
Port: 3739  |  Specification: https://widgetcontextprotocol.com
"""

import io
import json
import os
import zipfile
import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

PUBLISHED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'published', 'index.html')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

# In-memory cache: display string → full location object (lat/lon etc.)
_search_cache = {}

# ── CORS ──────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = (
        'Content-Type, Wcp-Instance-Id, Wcp-Dashboard-Id, Wcp-Version, Wcp-Widget-Id, '
        'Wcp-Orchestration-Id, Wcp-Application-Id'
    )
    return response

@app.route('/widget/<path:p>', methods=['OPTIONS'])
@app.route('/widget/', methods=['OPTIONS'])
@app.route('/wcp', methods=['OPTIONS'])
def cors_preflight(p=''):
    return Response('', status=204)

# ── Instance ID helper ────────────────────────────────────────────────────────

def get_instance_id():
    iid = request.headers.get("Wcp-Instance-Id", "").strip()
    if not iid:
        iid = (request.args.get("wcpInstanceId", "") or "").strip()
    return iid

def get_orchestration_id():
    oid = request.headers.get("Wcp-Orchestration-Id", "").strip()
    if not oid:
        oid = (request.args.get("wcpOrchestrationId", "") or "").strip()
    return oid

def get_application_id():
    aid = request.headers.get("Wcp-Application-Id", "").strip()
    if not aid:
        aid = (request.args.get("wcpApplicationId", "") or "").strip()
    return aid

def get_state_key():
    """WCP 1.5.0 compound state key. See widgetcontextprotocol.com — WCP Request Headers."""
    orch_id = get_orchestration_id()
    app_id  = get_application_id()
    if orch_id and app_id: return f"{orch_id}:{app_id}"
    if orch_id:            return orch_id
    return "global"

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

# ── Config helpers (per-instance storage keyed by Wcp-Instance-Id) ───────────

def _load_store():
    """Load the full config store. Returns {'instances': {'<id>': {...}, ...}}"""
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        # Backward compat: migrate old flat format
        if 'instances' not in data:
            return {'instances': {'global': data}}
        return data
    except Exception:
        return {'instances': {}}

def read_config(instance_id=None):
    store = _load_store()
    instances = store.get('instances', {})
    if instance_id and instance_id in instances:
        return instances[instance_id]
    return instances.get('global', {})

def write_config(data, instance_id=None):
    store = _load_store()
    key = instance_id or 'global'
    store['instances'][key] = data
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(store, f, indent=2)

# ── WCP Manifest ─────────────────────────────────────────────────────────────

WCP_MANIFEST = {
    "wcp": "2.1.0",
    "uuid": "65063c5d-5f2e-47c2-935b-fe3a3cdc4d0f",
    "name": "Weather Ticker",
    "version": "1.4.0",
    "description": (
        "Live weather, date and time ticker for any location worldwide. "
        "Powered by Open-Meteo — free, no API key required."
    ),
    "icon": "/widget/icon.svg",
    "health": "/widget/health",
    "container": {
        "image":            "docker.io/penrithbeacon/wcp-widget-weather-ticker",
        "source":           {"type": "registry"},
        "tag":              "1.4.0-wcp2.1.0",
        "port":             3739,
        "volumes":          [{"name": "weather_config", "mountPath": "/app/data"}],
        "defaultLifecycle": "always",
    },
    "configuration": {
        "submitEndpoint": "/widget/configure",
        "fields": [
            {
                "id": "location",
                "type": "autocomplete",
                "label": "Location",
                "placeholder": "Type a city name…",
                "searchUrl": "",
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

# ── JSON-LD structured data ───────────────────────────────────────────────────

WIDGET_JSONLD = json.dumps({
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": WCP_MANIFEST["name"],
    "softwareVersion": WCP_MANIFEST["version"],
    "description": WCP_MANIFEST["description"],
    "identifier": WCP_MANIFEST["uuid"],
    "applicationCategory": "WCP Widget",
    "operatingSystem": "Web",
    "isBasedOn": {
        "@type": "WebSite",
        "name": "Widget Context Protocol",
        "url": "https://widgetcontextprotocol.com",
    },
    "additionalProperty": [
        {"@type": "PropertyValue", "name": "wcpVersion",      "value": WCP_MANIFEST["wcp"]},
        {"@type": "PropertyValue", "name": "containerImage",  "value": WCP_MANIFEST["container"]["image"]},
        {"@type": "PropertyValue", "name": "containerTag",    "value": WCP_MANIFEST["container"]["tag"]},
        {"@type": "PropertyValue", "name": "containerPort",   "value": str(WCP_MANIFEST["container"]["port"])},
    ],
}, indent=2)

# ── WCP Endpoints ─────────────────────────────────────────────────────────────

@app.route("/wcp")
def container_directory():
    return jsonify({
        "type":    "directory",
        "wcp":     "2.1.0",
        "widgets": [{
            "id":          "weather-ticker",
            "uuid":        WCP_MANIFEST["uuid"],
            "name":        WCP_MANIFEST["name"],
            "description": WCP_MANIFEST["description"],
            "icon":        WCP_MANIFEST["icon"],
            "manifest":    "/widget/wcp",
        }]
    })

@app.route('/')
def published_spa():
    if os.path.exists(PUBLISHED_PATH):
        with open(PUBLISHED_PATH, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/html')
    return Response('Not Found', status=404, mimetype='text/plain')

@app.route('/widget/publish', methods=['POST'])
def publish():
    html = request.get_data(as_text=True)
    if not html:
        return jsonify({'success': False, 'error': 'Empty body'}), 400
    try:
        os.makedirs(os.path.dirname(PUBLISHED_PATH), exist_ok=True)
        with open(PUBLISHED_PATH, 'w', encoding='utf-8') as f:
            f.write(html)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/widget/publish', methods=['DELETE'])
def unpublish():
    try:
        if os.path.exists(PUBLISHED_PATH):
            os.remove(PUBLISHED_PATH)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/widget/")
@app.route("/widget/index.html")
def widget_ticker():
    iid = get_instance_id()
    cfg = read_config(iid)
    return render_template("widget.html", manifest=WCP_MANIFEST, config=cfg, jsonld=WIDGET_JSONLD,
                           wcp_instance_id=iid,
                           wcp_orchestration_id=get_orchestration_id(),
                           wcp_application_id=get_application_id())

@app.route("/widget/wcp")
def widget_wcp():
    manifest = dict(WCP_MANIFEST)
    manifest['web'] = {'published': os.path.exists(PUBLISHED_PATH)}
    return jsonify(manifest)

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
    iid = get_instance_id()
    cfg = read_config(iid)
    return render_template("full.html", manifest=WCP_MANIFEST, config=cfg, jsonld=WIDGET_JSONLD,
                           wcp_instance_id=iid,
                           wcp_orchestration_id=get_orchestration_id(),
                           wcp_application_id=get_application_id())

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <path fill="#f0883e" d="M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0zm0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13zm8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5zM3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8zm10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0zm-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0zm9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707zM4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .708z"/>
</svg>"""

@app.route("/widget/icon.svg")
def widget_icon():
    return Response(ICON_SVG, mimetype="image/svg+xml")

@app.route("/widget/api/guids")
def api_guids():
    return jsonify({
        "uuid": WCP_MANIFEST["uuid"],
        "components": [
            {"id": c["id"], "uuid": c["uuid"], "name": c["name"]}
            for c in WCP_MANIFEST.get("components", [])
        ]
    })

@app.route("/widget/export.wcp")
def export_wcp():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(WCP_MANIFEST, indent=2))
        z.writestr("icon.svg", ICON_SVG)
        z.writestr("DOCKER.md", f"""# {WCP_MANIFEST['name']} — WCP Container

## Pull
```
docker pull penrithbeacon/wcp-widget-weather-ticker
```

## Run
```
docker compose up -d
```

Port: 3739 | Spec: https://widgetcontextprotocol.com
""")
    buf.seek(0)
    name = WCP_MANIFEST["name"].lower().replace(" ", "-")
    resp = Response(buf.read(), mimetype="application/zip")
    resp.headers["Content-Disposition"] = f'attachment; filename="{name}.wcp"'
    return resp

# ── Configuration ─────────────────────────────────────────────────────────────

@app.route("/widget/configure", methods=["POST"])
def widget_configure():
    try:
        instance_id = request.headers.get('Wcp-Instance-Id')
        data = request.get_json(force=True) or {}
        # If location is a string (display name), resolve from cache
        if isinstance(data.get('location'), str):
            data['location'] = _search_cache.get(data['location'], data['location'])
        write_config(data, instance_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Location search (proxies Open-Meteo geocoding) ────────────────────────────

@app.route("/widget/api/search")
def location_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": q, "count": 10, "language": "en", "format": "json"},
            timeout=8,
        )
        data = r.json()
        suggestions = []
        for item in data.get("results", []):
            parts = [item.get("name", "")]
            if item.get("admin1"): parts.append(item["admin1"])
            if item.get("country"): parts.append(item["country"])
            display = ", ".join(parts)
            # Cache the full object keyed by display string for use at configure time
            _search_cache[display] = {
                "name":         item.get("name", ""),
                "admin1":       item.get("admin1", ""),
                "country":      item.get("country", ""),
                "country_code": item.get("country_code", ""),
                "latitude":     item.get("latitude"),
                "longitude":    item.get("longitude"),
            }
            suggestions.append(display)
        return jsonify(suggestions)
    except Exception as e:
        return jsonify([])

# ── Weather data ──────────────────────────────────────────────────────────────

@app.route("/widget/api/weather")
def get_weather():
    # Widget JS passes lat/lon/units inline after configure; fall back to stored config
    lat  = request.args.get("lat")
    lon  = request.args.get("lon")
    units = request.args.get("units")
    if not (lat and lon):
        instance_id = request.headers.get('Wcp-Instance-Id')
        cfg = read_config(instance_id)
        loc = cfg.get("location")
        if not loc or not loc.get("latitude"):
            return jsonify({"error": "no_location", "message": "Location not configured"})
        lat   = loc["latitude"]
        lon   = loc["longitude"]
        units = units or cfg.get("units", "celsius")
        loc_name = f"{loc.get('name', '')}, {loc.get('admin1', '')}, {loc.get('country_code', '')}"
    else:
        lat, lon = float(lat), float(lon)
        units = units or "celsius"
        loc_name = request.args.get("loc", "")
    if not units:
        units = "celsius"
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":         lat,
                "longitude":        lon,
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
            "location":    loc_name,
            "date":        now.strftime("%a %-d %b %Y"),
            "time":        now.strftime("%H:%M"),
            "icon":        icon,
            "description": desc,
            "temperature": f"{round(cur.get('temperature_2m', 0))}{unit_sym}",
            "humidity":    f"{round(cur.get('relative_humidity_2m', 0))}%",
            "wind":        f"{round(cur.get('windspeed_10m', 0))} km/h",
            "uv":          str(round(cur.get("uv_index", 0))),
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3739, debug=False)
