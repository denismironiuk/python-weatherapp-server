from datetime import datetime
import requests
from helpers.weather_codes import WEATHER_CODES


def get_geolocation(city, country, base_url="https://geocoding-api.open-meteo.com/v1/search"):
    """
    Retrieves geographic coordinates for a given city and country using Open-Meteo's geocoding API.

    Args:
        city (str): Name of the city.
        country (str): Name of the country.
        base_url (str): Geolocation API base URL (default: Open-Meteo).

    Returns:
        tuple: A dict with 'lat' and 'lon' if found, and an error message if not.
    """
    params = {"name": city, "country": country, "count": 1}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        return None, f"Geolocation request failed: {error}"

    if not data.get("results"):
        return None, f"City '{city}, {country}' not found."

    coords = data["results"][0]
    return {"lat": coords["latitude"], "lon": coords["longitude"]}, None


def get_forecast_data(lat, lon, base_url="https://api.open-meteo.com/v1/forecast"):
    """
    Retrieves a 7-day forecast from Open-Meteo for the given coordinates.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        base_url (str): Weather forecast API base URL.

    Returns:
        list: A list of daily forecast dictionaries, or an empty list on failure.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_min,temperature_2m_max,weathercode,relative_humidity_2m_min,relative_humidity_2m_max",
        "timezone": "auto"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        print(f"[ERROR] Forecast request failed: {error}")
        return []

    if "daily" not in data:
        return []

    return _parse_forecast_data(data["daily"])


def _parse_forecast_data(daily):
    """
    Parses and formats the raw forecast data from the API into structured daily forecasts.

    Args:
        daily (dict): Dictionary containing raw daily weather data.

    Returns:
        list: List of formatted forecast entries.
    """
    forecast = []
    for date, tmin, tmax, code, hmin, hmax in zip(
        daily["time"],
        daily["temperature_2m_min"],
        daily["temperature_2m_max"],
        daily["weathercode"],
        daily["relative_humidity_2m_min"],
        daily["relative_humidity_2m_max"]
    ):
        description, icon = WEATHER_CODES.get(code, ("Unknown", "01d"))
        forecast.append({
            "date": datetime.fromisoformat(date).strftime('%A, %d %b'),
            "temp_min": round(tmin, 1),
            "temp_max": round(tmax, 1),
            "humidity_min": int(hmin),
            "humidity_max": int(hmax),
            "description": description,
            "icon": icon
        })

    return forecast
