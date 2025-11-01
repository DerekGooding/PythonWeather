import tkinter as tk
from tkinter import messagebox, font
import weather_app
import os
import threading
import time
from datetime import datetime
import json

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather App")
        self.geometry("800x600")

        self.settings = self.load_settings()

        self.city_var = tk.StringVar()
        self.units_var = tk.StringVar(value=self.settings.get("units", "imperial"))

        self.create_widgets()
        self.load_subscriptions()
        self.start_auto_refresh()

    def create_widgets(self):
        # --- Fonts ---
        self.temp_font = font.Font(family="Helvetica", size=48, weight="bold")
        self.info_font = font.Font(family="Helvetica", size=12)

        # --- Frames ---
        top_frame = tk.Frame(self, pady=10)
        top_frame.pack(fill=tk.X)

        left_frame = tk.Frame(self, padx=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = tk.Frame(self, padx=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Top Frame Widgets ---
        tk.Label(top_frame, text="Enter City:").pack(side=tk.LEFT, padx=(10, 0))
        city_entry = tk.Entry(top_frame, textvariable=self.city_var, width=30)
        city_entry.pack(side=tk.LEFT, padx=5)
        city_entry.bind("<Return>", self.get_weather_for_entry)

        get_weather_button = tk.Button(top_frame, text="Get Weather", command=self.get_weather_for_entry)
        get_weather_button.pack(side=tk.LEFT, padx=5)

        subscribe_button = tk.Button(top_frame, text="Subscribe", command=self.subscribe_city)
        subscribe_button.pack(side=tk.LEFT, padx=5)
        
        # --- Units Toggle ---
        units_frame = tk.Frame(top_frame)
        units_frame.pack(side=tk.RIGHT, padx=10)
        tk.Radiobutton(units_frame, text="°F", variable=self.units_var, value="imperial", command=self.on_units_change).pack(side=tk.LEFT)
        tk.Radiobutton(units_frame, text="°C", variable=self.units_var, value="metric", command=self.on_units_change).pack(side=tk.LEFT)


        # --- Left Frame Widgets (Subscriptions) ---
        tk.Label(left_frame, text="Subscribed Cities").pack()
        self.subscriptions_listbox = tk.Listbox(left_frame, height=25)
        self.subscriptions_listbox.pack(fill=tk.Y)
        self.subscriptions_listbox.bind("<<ListboxSelect>>", self.get_weather_for_selection)

        refresh_button = tk.Button(left_frame, text="Refresh", command=self.refresh_subscriptions)
        refresh_button.pack(pady=5)

        # --- Right Frame Widgets (Weather Display) ---
        self.temp_label = tk.Label(right_frame, text="", font=self.temp_font)
        self.temp_label.pack(pady=20)
        
        self.weather_display = tk.Text(right_frame, height=15, width=60, state=tk.DISABLED, font=self.info_font)
        self.weather_display.pack(fill=tk.BOTH, expand=True)

    def on_units_change(self):
        self.settings["units"] = self.units_var.get()
        self.save_settings()
        self.refresh_subscriptions()

    def get_weather_for_entry(self, event=None):
        city = self.city_var.get()
        if city:
            self.display_weather(city)

    def get_weather_for_selection(self, event=None):
        selection = self.subscriptions_listbox.curselection()
        if selection:
            city = self.subscriptions_listbox.get(selection[0])
            self.display_weather(city)

    def display_weather(self, city):
        units = self.units_var.get()
        weather_data = weather_app.get_weather(city, units)
        
        self.weather_display.config(state=tk.NORMAL)
        self.weather_display.delete(1.0, tk.END)
        
        if weather_data and "error" not in weather_data:
            temp_unit = "°F" if units == "imperial" else "°C"
            self.temp_label.config(text=f"{weather_data['main']['temp']:.0f}{temp_unit}")
            self.weather_display.insert(tk.END, self.format_weather_data(weather_data, temp_unit))
        elif weather_data and "error" in weather_data:
            self.temp_label.config(text="")
            messagebox.showerror("Error", weather_data["error"])
        else:
            self.temp_label.config(text="")
            messagebox.showerror("Error", f"Could not retrieve weather for {city}")
            
        self.weather_display.config(state=tk.DISABLED)

    def format_weather_data(self, data, temp_unit):
        if not data or 'weather' not in data:
            return "No weather data available."
        
        weather = data['weather'][0]
        main = data['main']
        wind = data['wind']
        sys_data = data['sys']
        
        sunrise = datetime.fromtimestamp(sys_data['sunrise']).strftime('%H:%M:%S')
        sunset = datetime.fromtimestamp(sys_data['sunset']).strftime('%H:%M:%S')

        return (
            f"Weather in {data['name']}, {sys_data['country']}:\n"
            f"Description: {weather['description'].capitalize()}\n"
            f"Feels like: {main['feels_like']:.0f}{temp_unit}\n"
            f"Humidity: {main['humidity']}%%\n"
            f"Pressure: {main['pressure']} hPa\n"
            f"Wind Speed: {wind['speed']} m/s\n"
            f"Visibility: {data.get('visibility', 'N/A')} meters\n"
            f"Sunrise: {sunrise}\n"
            f"Sunset: {sunset}\n"
        )

    def subscribe_city(self):
        city = self.city_var.get()
        if city:
            if city not in self.settings["subscriptions"]:
                self.settings["subscriptions"].append(city)
                self.subscriptions_listbox.insert(tk.END, city)
                self.save_settings()
            else:
                messagebox.showinfo("Already Subscribed", f"You are already subscribed to {city}.")

    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f, indent=4)

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return self.get_default_settings()
        else:
            return self.get_default_settings()
            
    def get_default_settings(self):
        return {"units": "imperial", "subscriptions": []}

    def load_subscriptions(self):
        for city in self.settings.get("subscriptions", []):
            self.subscriptions_listbox.insert(tk.END, city)
        self.refresh_subscriptions()

    def refresh_subscriptions(self):
        cities = self.subscriptions_listbox.get(0, tk.END)
        if cities:
            current_selection = self.subscriptions_listbox.curselection()
            if current_selection:
                self.display_weather(self.subscriptions_listbox.get(current_selection[0]))
            else:
                self.display_weather(cities[0])

    def start_auto_refresh(self):
        self.auto_refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.auto_refresh_thread.start()

    def auto_refresh_loop(self):
        while True:
            time.sleep(3600) # 1 hour
            self.refresh_subscriptions()

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()