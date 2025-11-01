import tkinter as tk
from tkinter import messagebox
import weather_app
import os
import threading
import time
from datetime import datetime

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather App")
        self.geometry("800x600")

        self.city_var = tk.StringVar()
        self.create_widgets()
        self.load_subscriptions()
        self.start_auto_refresh()

    def create_widgets(self):
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

        # --- Left Frame Widgets (Subscriptions) ---
        tk.Label(left_frame, text="Subscribed Cities").pack()
        self.subscriptions_listbox = tk.Listbox(left_frame, height=25)
        self.subscriptions_listbox.pack(fill=tk.Y)
        self.subscriptions_listbox.bind("<<ListboxSelect>>", self.get_weather_for_selection)

        refresh_button = tk.Button(left_frame, text="Refresh", command=self.refresh_subscriptions)
        refresh_button.pack(pady=5)

        # --- Right Frame Widgets (Weather Display) ---
        self.weather_display = tk.Text(right_frame, height=25, width=60, state=tk.DISABLED)
        self.weather_display.pack(fill=tk.BOTH, expand=True)

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
        weather_data = weather_app.get_weather(city)
        self.weather_display.config(state=tk.NORMAL)
        self.weather_display.delete(1.0, tk.END)
        if weather_data and "error" not in weather_data:
            self.weather_display.insert(tk.END, self.format_weather_data(weather_data))
        elif weather_data and "error" in weather_data:
            messagebox.showerror("Error", weather_data["error"])
        else:
            messagebox.showerror("Error", f"Could not retrieve weather for {city}")
        self.weather_display.config(state=tk.DISABLED)

    def format_weather_data(self, data):
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
            f"Temperature: {main['temp']}°F (Feels like: {main['feels_like']}°F)\n"
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
            if city not in self.subscriptions_listbox.get(0, tk.END):
                self.subscriptions_listbox.insert(tk.END, city)
                self.save_subscriptions()
            else:
                messagebox.showinfo("Already Subscribed", f"You are already subscribed to {city}.")

    def save_subscriptions(self):
        with open("subscriptions.txt", "w") as f:
            for city in self.subscriptions_listbox.get(0, tk.END):
                f.write(city + "\n")

    def load_subscriptions(self):
        if os.path.exists("subscriptions.txt"):
            with open("subscriptions.txt", "r") as f:
                for city in f:
                    self.subscriptions_listbox.insert(tk.END, city.strip())
            self.refresh_subscriptions()

    def refresh_subscriptions(self):
        cities = self.subscriptions_listbox.get(0, tk.END)
        if cities:
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
