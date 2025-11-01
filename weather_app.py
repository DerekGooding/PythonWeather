import requests
import os

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

def get_weather(city):
    """
    Fetches weather data for a given city from the OpenWeatherMap API.

    Args:
        city (str): The name of the city.

    Returns:
        dict: A dictionary containing weather data if the request is successful,
              otherwise an error dictionary.
    """
    API_KEY, error = get_api_key()
    if error:
        return {"error": error}

    BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
    
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'imperial'
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Unable to fetch weather data for {city}. Status code: {response.status_code}"}