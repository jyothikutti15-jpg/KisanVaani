"""Live weather using multiple free APIs with fallback chain."""
import json
import time
import urllib.parse
import urllib.request
from typing import Optional

# Cache weather responses for 30 minutes
_weather_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL = 1800  # 30 minutes

# City coordinates for common farming regions
CITY_COORDS = {
    # India — Major cities
    "mumbai": (19.08, 72.88), "delhi": (28.61, 77.21), "new delhi": (28.61, 77.21),
    "pune": (18.52, 73.86), "nagpur": (21.15, 79.09), "nashik": (19.99, 73.79),
    "hyderabad": (17.39, 78.49), "chennai": (13.08, 80.27), "bangalore": (12.97, 77.59),
    "bengaluru": (12.97, 77.59), "kolkata": (22.57, 88.36), "ahmedabad": (23.02, 72.57),
    "jaipur": (26.91, 75.79), "lucknow": (26.85, 80.95), "patna": (25.61, 85.14),
    "bhopal": (23.26, 77.41), "indore": (22.72, 75.86), "surat": (21.17, 72.83),
    "chandigarh": (30.73, 76.78), "coimbatore": (11.01, 76.96), "visakhapatnam": (17.69, 83.22),
    "thiruvananthapuram": (8.52, 76.94), "mysore": (12.30, 76.66), "mangalore": (12.87, 74.88),
    "rajkot": (22.30, 70.80), "vadodara": (22.31, 73.19), "aurangabad": (19.88, 75.34),
    "solapur": (17.66, 75.91), "amravati": (20.93, 77.78), "sangli": (16.85, 74.56),
    # India — Farming regions & states
    "sehore": (23.20, 77.08), "vidarbha": (20.93, 77.78), "warangal": (17.98, 79.60),
    "shirur": (18.83, 74.38), "baramati": (18.15, 74.58), "satara": (17.68, 74.00),
    "latur": (18.40, 76.57), "nanded": (19.15, 77.30), "kolhapur": (16.70, 74.24),
    "madhya pradesh": (23.26, 77.41), "telangana": (17.39, 78.49), "karnataka": (12.97, 77.59),
    "maharashtra": (19.08, 72.88), "tamil nadu": (13.08, 80.27), "rajasthan": (26.91, 75.79),
    "gujarat": (23.02, 72.57), "uttar pradesh": (26.85, 80.95), "bihar": (25.61, 85.14),
    "punjab": (30.73, 76.78), "haryana": (29.06, 76.09), "andhra pradesh": (15.91, 79.74),
    "west bengal": (22.57, 88.36), "odisha": (20.27, 85.84), "kerala": (8.52, 76.94),
    "assam": (26.14, 91.77), "chhattisgarh": (21.25, 81.63), "jharkhand": (23.34, 85.31),
    # Kenya
    "kakamega": (0.28, 34.75), "nairobi": (-1.29, 36.82), "mombasa": (-4.04, 39.67),
    "western kenya": (0.28, 34.75), "kisumu": (-0.09, 34.77), "nakuru": (-0.30, 36.07),
    "eldoret": (0.51, 35.27), "thika": (-1.03, 37.07), "nyeri": (-0.42, 36.95),
    "machakos": (-1.52, 37.26), "bungoma": (0.57, 34.56), "kitale": (1.02, 34.99),
    # Nigeria
    "kano": (12.00, 8.52), "lagos": (6.52, 3.38), "abuja": (9.06, 7.49),
    "dawanau": (12.00, 8.52), "kaduna": (10.52, 7.43), "ibadan": (7.38, 3.94),
    "jos": (9.93, 8.89), "maiduguri": (11.85, 13.16), "enugu": (6.44, 7.50),
    "katsina": (13.00, 7.60), "sokoto": (13.06, 5.24), "abeokuta": (7.16, 3.35),
    # Ethiopia
    "addis ababa": (9.02, 38.75), "bahir dar": (11.60, 37.39), "amhara": (11.60, 37.39),
    "hawassa": (7.06, 38.48), "dire dawa": (9.60, 41.85), "jimma": (7.67, 36.83),
    "mekelle": (13.50, 39.47), "gondar": (12.60, 37.47), "adama": (8.54, 39.27),
}


def _get_coords(location: str) -> Optional[tuple[float, float]]:
    location_lower = location.lower().strip()
    for key, coords in CITY_COORDS.items():
        if key in location_lower or location_lower in key:
            return coords
    return None


WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 80: "Rain showers", 81: "Heavy rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail",
}


async def _fetch_open_meteo(lat: float, lon: float, days: int) -> Optional[dict]:
    """Try Open-Meteo API with httpx async client."""
    try:
        import httpx
        params = {
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weathercode",
            "current_weather": "true", "timezone": "auto",
            "forecast_days": min(days, 7),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (compatible; KisanVaani/2.1)"},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


async def _fetch_wttr(location: str) -> Optional[dict]:
    """Fallback: use wttr.in weather API (works from server IPs)."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                f"https://wttr.in/{location}?format=j1",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


def _parse_wttr_response(data: dict, location: str) -> dict:
    """Parse wttr.in JSON format into our standard format."""
    current = data.get("current_condition", [{}])[0]
    forecasts = data.get("weather", [])

    forecast_list = []
    for day in forecasts[:7]:
        forecast_list.append({
            "date": day.get("date", ""),
            "temp_max": float(day.get("maxtempC", 0)),
            "temp_min": float(day.get("mintempC", 0)),
            "rain_mm": float(day.get("totalSnow_cm", 0)) * 10,  # approximate
            "rain_chance": int(day.get("hourly", [{}])[4].get("chanceofrain", 0)) if day.get("hourly") else 0,
            "condition": day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "Unknown") if day.get("hourly") else "Unknown",
        })

    return {
        "location": location,
        "current": {
            "temperature": float(current.get("temp_C", 0)),
            "condition": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
            "windspeed": float(current.get("windspeedKmph", 0)),
        },
        "forecast": forecast_list,
    }


def _parse_open_meteo_response(data: dict, location: str) -> dict:
    """Parse Open-Meteo response into our standard format."""
    current = data.get("current_weather", {})
    daily = data.get("daily", {})

    forecast = []
    dates = daily.get("time", [])
    for i in range(len(dates)):
        forecast.append({
            "date": dates[i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "rain_mm": daily["precipitation_sum"][i],
            "rain_chance": daily["precipitation_probability_max"][i],
            "condition": WEATHER_CODES.get(daily["weathercode"][i], "Unknown"),
        })

    return {
        "location": location,
        "current": {
            "temperature": current.get("temperature"),
            "condition": WEATHER_CODES.get(current.get("weathercode", 0), "Unknown"),
            "windspeed": current.get("windspeed"),
        },
        "forecast": forecast,
    }


async def get_weather(location: str, days: int = 3) -> dict:
    """Get weather for ANY location. Uses wttr.in (accepts any city name worldwide)
    with Open-Meteo as secondary source for known coordinates."""

    # Check cache first
    cache_key = f"{location.lower().strip()}:{days}"
    if cache_key in _weather_cache:
        cached_data, cached_time = _weather_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_data

    # Try 1: wttr.in — accepts ANY city/village name worldwide (best for unknown locations)
    wttr_data = await _fetch_wttr(location)
    if wttr_data and "current_condition" in wttr_data:
        result = _parse_wttr_response(wttr_data, location)
        _weather_cache[cache_key] = (result, time.time())
        return result

    # Try 2: Open-Meteo with known coordinates (fallback)
    coords = _get_coords(location)
    if coords:
        lat, lon = coords
        data = await _fetch_open_meteo(lat, lon, days)
        if data and "daily" in data:
            result = _parse_open_meteo_response(data, location)
            _weather_cache[cache_key] = (result, time.time())
            return result

    # Try 3: Return cached data even if expired
    if cache_key in _weather_cache:
        return _weather_cache[cache_key][0]

    return {"error": f"Could not fetch weather for '{location}'. Try a different spelling or a nearby city name."}


def format_weather_for_context(weather: dict) -> str:
    """Format weather data for inclusion in LLM context."""
    if "error" in weather:
        return f"Weather: {weather['error']}"

    lines = [f"Weather for {weather['location']}:"]
    curr = weather.get("current", {})
    if curr:
        lines.append(f"  Now: {curr.get('temperature')}°C, {curr.get('condition')}, Wind: {curr.get('windspeed')} km/h")

    for day in weather.get("forecast", [])[:3]:
        lines.append(f"  {day['date']}: {day['temp_min']}-{day['temp_max']}°C, Rain: {day['rain_chance']}% ({day['rain_mm']}mm), {day['condition']}")

    return "\n".join(lines)
