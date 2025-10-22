import requests
import os

API_KEY = os.getenv('OPENWEATHER_API_KEY')
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

def get_weather(city):
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'imperial'  # Use Fahrenheit
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        weather = data['weather'][0]
        main = data['main']
        wind = data['wind']
        sys = data['sys']
        
        print(f"Weather in {data['name']}, {sys['country']}:")
        print(f"Description: {weather['description'].capitalize()}")
        print(f"Temperature: {main['temp']}°F (Feels like: {main['feels_like']}°F)")
        print(f"Humidity: {main['humidity']}%")
        print(f"Pressure: {main['pressure']} hPa")
        print(f"Wind Speed: {wind['speed']} m/s")
        print(f"Visibility: {data.get('visibility', 'N/A')} meters")
        print(f"Sunrise: {sys['sunrise']}")
        print(f"Sunset: {sys['sunset']}")
    else:
        print(f"Error: Unable to fetch weather data for {city}. Status code: {response.status_code}")

if __name__ == "__main__":
    while True:
        city = input("Enter city name: ")
        get_weather(city)
        again = input("Do you want to look at another city? (y/n): ")
        if again.lower() != 'y':
            break