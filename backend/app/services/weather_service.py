"""Live weather using Open-Meteo API (free, no key needed)."""
import json
import time
import urllib.parse
import urllib.request
from typing import Optional

# Cache weather responses for 30 minutes to avoid rate limiting (429)
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


async def get_weather(location: str, days: int = 3) -> dict:
    """Get real weather forecast from Open-Meteo (free, no API key). Cached for 30 min."""
    coords = _get_coords(location)
    if not coords:
        return {"error": f"Location '{location}' not found. Try a city or state name."}

    # Check cache first
    cache_key = f"{location.lower()}:{days}"
    if cache_key in _weather_cache:
        cached_data, cached_time = _weather_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_data

    lat, lon = coords
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weathercode",
        "current_weather": "true",
        "timezone": "auto",
        "forecast_days": min(days, 7),
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"

    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 KisanVaani/2.1"})
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        # Try urllib as fallback
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            # Return cached data even if expired, rather than error
            if cache_key in _weather_cache:
                return _weather_cache[cache_key][0]
            return {"error": f"Weather service temporarily unavailable. Try again in a few minutes."}

    # Parse current weather
    current = data.get("current_weather", {})
    daily = data.get("daily", {})

    weather_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 80: "Rain showers", 81: "Heavy rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail",
    }

    forecast = []
    dates = daily.get("time", [])
    for i in range(len(dates)):
        forecast.append({
            "date": dates[i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "rain_mm": daily["precipitation_sum"][i],
            "rain_chance": daily["precipitation_probability_max"][i],
            "condition": weather_codes.get(daily["weathercode"][i], "Unknown"),
        })

    result = {
        "location": location,
        "current": {
            "temperature": current.get("temperature"),
            "condition": weather_codes.get(current.get("weathercode", 0), "Unknown"),
            "windspeed": current.get("windspeed"),
        },
        "forecast": forecast,
    }

    # Cache the result
    _weather_cache[cache_key] = (result, time.time())
    return result


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
