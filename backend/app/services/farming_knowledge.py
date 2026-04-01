import json
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> dict:
    try:
        with open(DATA_DIR / filename) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_countries() -> dict:
    return _load_json("countries.json")


def get_current_season(country: str = "IN") -> str:
    """Get current season based on country and month."""
    month = date.today().month
    countries = get_countries()
    country_data = countries.get(country, countries.get("IN", {}))
    seasons = country_data.get("seasons", {})

    # Parse season months and match current month
    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    current_month = month_names[month]

    for season_name, season_info in seasons.items():
        months_str = season_info.get("months", "")
        if current_month.lower() in months_str.lower():
            return season_name

    # Fallback
    return list(seasons.keys())[0] if seasons else "Unknown"


def get_context(language: str = "en", country: str = "IN", farmer_profile: dict | None = None) -> str:
    """Build rich farming context for the LLM."""
    today = date.today().isoformat()
    season = get_current_season(country)
    countries = get_countries()
    country_data = countries.get(country, {})

    parts = [
        f"Current date: {today}",
        f"Country: {country_data.get('name', country)}",
        f"Currency: {country_data.get('currency', 'USD')}",
        f"Current season: {season}",
    ]

    # Season crops
    season_info = country_data.get("seasons", {}).get(season, {})
    if season_info.get("crops"):
        parts.append(f"Active crops: {', '.join(season_info['crops'])}")

    # Market prices
    prices = country_data.get("market_prices", {})
    if prices:
        price_lines = [f"  {crop}: {price}" for crop, price in list(prices.items())[:8]]
        parts.append("Current market prices:\n" + "\n".join(price_lines))

    # Government schemes
    schemes = country_data.get("schemes", [])
    if schemes:
        scheme_lines = [f"  - {s['name']}: {s['summary']}" for s in schemes[:5]]
        parts.append("Government schemes:\n" + "\n".join(scheme_lines))

    # Extension service
    if country_data.get("extension_service"):
        parts.append(f"Nearest extension service: {country_data['extension_service']}")
    if country_data.get("emergency_helpline"):
        parts.append(f"Agriculture helpline: {country_data['emergency_helpline']}")

    # Farmer memory context
    if farmer_profile:
        parts.append("\n--- FARMER PROFILE (remember this farmer) ---")
        if farmer_profile.get("name"):
            parts.append(f"Farmer name: {farmer_profile['name']}")
        if farmer_profile.get("region"):
            parts.append(f"Location: {', '.join(filter(None, [farmer_profile.get('village'), farmer_profile.get('district'), farmer_profile.get('region')]))}")
        if farmer_profile.get("crops"):
            parts.append(f"Crops grown: {farmer_profile['crops']}")
        if farmer_profile.get("land_size_acres"):
            parts.append(f"Land size: {farmer_profile['land_size_acres']} acres")
        if farmer_profile.get("soil_type"):
            parts.append(f"Soil type: {farmer_profile['soil_type']}")
        if farmer_profile.get("irrigation_type"):
            parts.append(f"Irrigation: {farmer_profile['irrigation_type']}")
        if farmer_profile.get("past_problems"):
            parts.append(f"Past problems: {farmer_profile['past_problems']}")
        if farmer_profile.get("active_issues"):
            parts.append(f"Current ongoing issues: {farmer_profile['active_issues']}")
        if farmer_profile.get("last_advice"):
            parts.append(f"Last advice given: {farmer_profile['last_advice'][:200]}")

    return "\n".join(parts)
