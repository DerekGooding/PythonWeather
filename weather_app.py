import requests
import os

def get_weather(city):
    """
    Fetches weather data for a given city from the OpenWeatherMap API.

    Args:
        city (str): The name of the city.

    Returns:
        dict: A dictionary containing weather data if the request is successful,
              otherwise None.
    """
    try:
        with open(os.path.join('.api', 'apiKeys.txt'), 'r') as f:
            API_KEY = f.read().strip()
    except FileNotFoundError:
        return {"error": "API key file not found."}
        
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