import requests
import os
import json
import time

CACHE_DIR = ".cache"
CACHE_EXPIRATION = 600  # 10 minutes

def get_api_key():
    """
    Gets the API key from a local file or environment variable.

    Returns:
        tuple: A tuple containing the API key and an error message.
               If the key is found, the error message is None.
               If the key is not found, the key is None and the error message is set.
    """
    # Try to get API key from local file
    try:
        with open(os.path.join('.api', 'apiKeys.txt'), 'r') as f:
            api_key = f.read().strip()
        if api_key:
            return api_key, None
    except FileNotFoundError:
        pass  # File not found, will try environment variable

    # If local file fails, try environment variable
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if api_key:
        return api_key, None

    # If both fail, return an error
    error_message = (
        "API key not found. Please add your OpenWeatherMap API key.\n\n"
        "You can either:\n"
        "1. Create a file named 'apiKeys.txt' in the '.api' directory and paste your key in it.\n"
        "2. Set the 'OPENWEATHER_API_KEY' environment variable.\n\n"
        "If you don't have an API key, you can get one for free from https://openweathermap.org/appid"
    )
    return None, error_message

def get_cached_data(cache_key):
    """
    Gets data from the cache if it exists and is not expired.

    Args:
        cache_key (str): The key for the cached data.

    Returns:
        dict: The cached data if found and valid, otherwise None.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    cache_file = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            try:
                data = json.load(f)
                if time.time() - data.get("timestamp", 0) < CACHE_EXPIRATION:
                    return data.get("payload")
            except json.JSONDecodeError:
                return None
    return None

def save_cached_data(cache_key, data):
    """
    Saves data to the cache.

    Args:
        cache_key (str): The key for the cached data.
        data (dict): The data to be cached.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    cache_file = os.path.join(CACHE_DIR, cache_key)
    with open(cache_file, 'w') as f:
        json.dump({"timestamp": time.time(), "payload": data}, f)


def get_weather(city, units='imperial'):
    """
    Fetches weather data for a given city from the OpenWeatherMap API.

    Args:
        city (str): The name of the city.
        units (str): The units for the temperature ('imperial' for F, 'metric' for C).

    Returns:
        dict: A dictionary containing weather data if the request is successful,
              otherwise an error dictionary.
    """
    cache_key = f"weather_{city.lower()}_{units}.json"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data

    API_KEY, error = get_api_key()
    if error:
        return {"error": error}

    BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
    
    params = {
        'q': city,
        'appid': API_KEY,
        'units': units
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        save_cached_data(cache_key, data)
        return data
    else:
        return {"error": f"Unable to fetch weather data for {city}. Status code: {response.status_code}"}

def get_forecast(lat, lon, units='imperial'):
    """
    Fetches 7-day forecast data for a given latitude and longitude.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        units (str): The units for the temperature ('imperial' for F, 'metric' for C).

    Returns:
        dict: A dictionary containing forecast data if the request is successful,
              otherwise an error dictionary.
    """
    cache_key = f"forecast_{lat}_{lon}_{units}.json"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data

    API_KEY, error = get_api_key()
    if error:
        return {"error": error}

    BASE_URL = 'https://api.openweathermap.org/data/3.0/onecall'
    
    params = {
        'lat': lat,
        'lon': lon,
        'exclude': 'current,minutely,alerts',
        'appid': API_KEY,
        'units': units
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        save_cached_data(cache_key, data)
        return data
    else:
        return {"error": f"Unable to fetch forecast data. Status code: {response.status_code}"}