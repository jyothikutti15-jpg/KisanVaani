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
    # India
    "sehore": (23.20, 77.08), "vidarbha": (20.93, 77.78), "warangal": (17.98, 79.60),
    "pune": (18.52, 73.86), "indore": (22.72, 75.86), "nagpur": (21.15, 79.09),
    "jaipur": (26.91, 75.79), "lucknow": (26.85, 80.95), "patna": (25.61, 85.14),
    "bhopal": (23.26, 77.41), "hyderabad": (17.39, 78.49), "chennai": (13.08, 80.27),
    "bangalore": (12.97, 77.59), "kolkata": (22.57, 88.36), "ahmedabad": (23.02, 72.57),
    "madhya pradesh": (23.26, 77.41), "telangana": (17.39, 78.49), "karnataka": (12.97, 77.59),
    "maharashtra": (19.08, 72.88), "tamil nadu": (13.08, 80.27),
    # Kenya
    "kakamega": (0.28, 34.75), "nairobi": (-1.29, 36.82), "mombasa": (-4.04, 39.67),
    "western kenya": (0.28, 34.75), "kisumu": (-0.09, 34.77),
    # Nigeria
    "kano": (12.00, 8.52), "lagos": (6.52, 3.38), "abuja": (9.06, 7.49),
    "dawanau": (12.00, 8.52), "kaduna": (10.52, 7.43),
    # Ethiopia
    "addis ababa": (9.02, 38.75), "bahir dar": (11.60, 37.39), "amhara": (11.60, 37.39),
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
    """Get weather forecast with fallback chain: Open-Meteo -> wttr.in -> cache."""
    coords = _get_coords(location)
    if not coords:
        return {"error": f"Location '{location}' not found. Try: Pune, Nagpur, Kakamega, Kano, Nairobi"}

    # Check cache first
    cache_key = f"{location.lower()}:{days}"
    if cache_key in _weather_cache:
        cached_data, cached_time = _weather_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_data

    lat, lon = coords

    # Try 1: Open-Meteo (free, no key needed)
    data = await _fetch_open_meteo(lat, lon, days)
    if data and "daily" in data:
        result = _parse_open_meteo_response(data, location)
        _weather_cache[cache_key] = (result, time.time())
        return result

    # Try 2: wttr.in (free, works from server IPs)
    wttr_data = await _fetch_wttr(location)
    if wttr_data and "current_condition" in wttr_data:
        result = _parse_wttr_response(wttr_data, location)
        _weather_cache[cache_key] = (result, time.time())
        return result

    # Try 3: Return cached data even if expired
    if cache_key in _weather_cache:
        return _weather_cache[cache_key][0]

    return {"error": "Weather service temporarily unavailable. Try again in a few minutes."}


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
