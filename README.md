# Python Weather App

A simple, modern weather application built with Python and Tkinter.

## Features

*   **Current Weather:** Get the current weather for any city.
*   **7-Day Forecast:** View the 7-day forecast for any city.
*   **Hourly Forecast:** View the hourly forecast for the next 12 hours.
*   **Subscriptions:** Subscribe to cities to quickly view their weather.
*   **Auto-Refresh:** Subscribed cities' weather data automatically refreshes every hour.
*   **Temperature Units:** Toggle between Fahrenheit and Celsius.
*   **Dark Theme:** A modern, dark-themed UI.
*   **Caching:** API responses are cached to avoid hitting rate limits.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/PythonWeather.git
    ```
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Add your OpenWeatherMap API key:
    *   Create a file named `apiKeys.txt` in the `.api` directory and paste your key in it.
    *   Or, set the `OPENWEATHER_API_KEY` environment variable.

## Usage

Run the application with the following command:

```bash
python weather_gui.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
