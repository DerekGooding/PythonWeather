import tkinter as tk
from tkinter import messagebox, font
import weather_app
import os
import threading
import time
from datetime import datetime
import json
from PIL import Image, ImageTk
import requests
import queue

IMAGE_CACHE_DIR = ".image_cache"

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather App")
        self.geometry("800x600")

        # --- Dark Theme Colors ---
        self.bg_color = "#2E2E2E"  # Dark Grey
        self.fg_color = "#FFFFFF"  # White
        self.accent_color = "#4CAF50" # Green
        self.text_bg_color = "#3C3C3C" # Slightly lighter dark grey
        self.list_bg_color = "#3C3C3C" # Slightly lighter dark grey
        self.list_fg_color = "#FFFFFF" # White
        self.button_bg_color = "#555555" # Medium dark grey
        self.button_fg_color = "#FFFFFF" # White
        self.status_bar_color = "#1E1E1E"

        self.configure(bg=self.bg_color)

        self.settings = self.load_settings()

        self.city_var = tk.StringVar()
        self.units_var = tk.StringVar(value=self.settings.get("units", "imperial"))
        self.current_city_display_var = tk.StringVar(value="Select a city or enter one above")
        self.status_var = tk.StringVar(value="Ready")
        
        self.data_queue = queue.Queue()
        
        if not os.path.exists(IMAGE_CACHE_DIR):
            os.makedirs(IMAGE_CACHE_DIR)

        self.create_widgets()
        self.load_subscriptions()
        self.start_auto_refresh()

    def create_widgets(self):
        # --- Fonts ---
        self.title_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.city_display_font = font.Font(family="Segoe UI", size=24, weight="bold")
        self.temp_font = font.Font(family="Segoe UI", size=48, weight="bold")
        self.info_font = font.Font(family="Segoe UI", size=12)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.list_font = font.Font(family="Segoe UI", size=10)
        self.forecast_day_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.forecast_temp_font = font.Font(family="Segoe UI", size=10)
        self.hourly_forecast_font = font.Font(family="Segoe UI", size=10)
        self.status_font = font.Font(family="Segoe UI", size=10)


        # --- Main Layout (Grid) ---
        self.grid_rowconfigure(0, weight=0) # Top frame
        self.grid_rowconfigure(1, weight=1) # Content frames
        self.grid_rowconfigure(2, weight=0) # Status bar
        self.grid_columnconfigure(0, weight=0) # Left frame
        self.grid_columnconfigure(1, weight=1) # Right frame

        # --- Top Frame (Search, Subscribe, Units) ---
        top_frame = tk.Frame(self, pady=10, bg=self.bg_color)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        tk.Label(top_frame, text="Enter City:", bg=self.bg_color, fg=self.fg_color, font=self.info_font).pack(side=tk.LEFT, padx=(10, 0))
        city_entry = tk.Entry(top_frame, textvariable=self.city_var, width=30, bg=self.text_bg_color, fg=self.fg_color, insertbackground=self.fg_color, font=self.info_font)
        city_entry.pack(side=tk.LEFT, padx=5)
        city_entry.bind("<Return>", self.get_weather_for_entry)

        get_weather_button = tk.Button(top_frame, text="Get Weather", command=self.get_weather_for_entry, bg=self.button_bg_color, fg=self.button_fg_color, font=self.button_font, activebackground=self.accent_color, activeforeground=self.fg_color)
        get_weather_button.pack(side=tk.LEFT, padx=5)

        subscribe_button = tk.Button(top_frame, text="Subscribe", command=self.subscribe_city, bg=self.button_bg_color, fg=self.button_fg_color, font=self.button_font, activebackground=self.accent_color, activeforeground=self.fg_color)
        subscribe_button.pack(side=tk.LEFT, padx=5)
        
        units_frame = tk.Frame(top_frame, bg=self.bg_color)
        units_frame.pack(side=tk.RIGHT, padx=10)
        tk.Radiobutton(units_frame, text="°F", variable=self.units_var, value="imperial", command=self.on_units_change, bg=self.bg_color, fg=self.fg_color, selectcolor=self.text_bg_color, activebackground=self.bg_color, activeforeground=self.accent_color, font=self.info_font).pack(side=tk.LEFT)
        tk.Radiobutton(units_frame, text="°C", variable=self.units_var, value="metric", command=self.on_units_change, bg=self.bg_color, fg=self.fg_color, selectcolor=self.text_bg_color, activebackground=self.bg_color, activeforeground=self.accent_color, font=self.info_font).pack(side=tk.LEFT)


        # --- Left Frame (Subscriptions) ---
        left_frame = tk.Frame(self, padx=10, bg=self.bg_color)
        left_frame.grid(row=1, column=0, sticky="ns")

        tk.Label(left_frame, text="Subscribed Cities", bg=self.bg_color, fg=self.fg_color, font=self.title_font).pack(pady=5)
        self.subscriptions_listbox = tk.Listbox(left_frame, height=25, bg=self.list_bg_color, fg=self.list_fg_color, selectbackground=self.accent_color, selectforeground=self.fg_color, borderwidth=0, highlightthickness=0, font=self.list_font)
        self.subscriptions_listbox.pack(fill=tk.Y, expand=True)
        self.subscriptions_listbox.bind("<<ListboxSelect>>", self.get_weather_for_selection)

        refresh_button = tk.Button(left_frame, text="Refresh", command=self.refresh_subscriptions, bg=self.button_bg_color, fg=self.button_fg_color, font=self.button_font, activebackground=self.accent_color, activeforeground=self.fg_color)
        refresh_button.pack(pady=5)

        # --- Right Frame (Weather Display) ---
        right_frame = tk.Frame(self, padx=10, bg=self.bg_color)
        right_frame.grid(row=1, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(4, weight=1)

        self.current_city_label = tk.Label(right_frame, textvariable=self.current_city_display_var, font=self.city_display_font, bg=self.bg_color, fg=self.fg_color)
        self.current_city_label.pack(pady=(10, 5))

        self.icon_label = tk.Label(right_frame, bg=self.bg_color)
        self.icon_label.pack()

        self.temp_label = tk.Label(right_frame, text="", font=self.temp_font, bg=self.bg_color, fg=self.fg_color)
        self.temp_label.pack(pady=10)
        
        self.weather_display = tk.Text(right_frame, height=8, width=60, state=tk.DISABLED, font=self.info_font, bg=self.text_bg_color, fg=self.fg_color, borderwidth=0, highlightthickness=0)
        self.weather_display.pack(fill=tk.X, expand=False)

        self.hourly_forecast_frame = tk.Frame(right_frame, bg=self.bg_color)
        self.hourly_forecast_frame.pack(fill=tk.X, expand=False, pady=10)

        self.forecast_frame = tk.Frame(right_frame, bg=self.bg_color)
        self.forecast_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # --- Status Bar ---
        status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg=self.status_bar_color, fg=self.fg_color, font=self.status_font)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")


    def set_status(self, text, duration=5000):
        self.status_var.set(text)
        if duration:
            self.after(duration, lambda: self.status_var.set("Ready"))


    def on_units_change(self):
        self.settings["units"] = self.units_var.get()
        self.save_settings()
        self.refresh_subscriptions()
        self.set_status(f"Units changed to {self.units_var.get()}")

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
        self.set_status(f"Fetching weather for {city}...")
        self.current_city_display_var.set(f"Loading {city}...")
        self.temp_label.config(text="")
        self.icon_label.config(image="")
        self.clear_forecast()
        self.clear_hourly_forecast()
        
        thread = threading.Thread(target=self.fetch_weather_data_threaded, args=(city, self.units_var.get()), daemon=True)
        thread.start()
        self.after(100, self.check_data_queue)

    def fetch_weather_data_threaded(self, city, units):
        weather_data = weather_app.get_weather(city, units)
        if weather_data and "error" not in weather_data:
            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']
            forecast_data = weather_app.get_forecast(lat, lon, units)
            self.data_queue.put((weather_data, forecast_data))
        else:
            self.data_queue.put((weather_data, None))

    def check_data_queue(self):
        try:
            weather_data, forecast_data = self.data_queue.get_nowait()
            self.process_weather_data(weather_data, forecast_data)
        except queue.Empty:
            self.after(100, self.check_data_queue)

    def get_icon(self, icon_code, icon_url, size=None):
        icon_path = os.path.join(IMAGE_CACHE_DIR, f"{icon_code}.png")
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
        else:
            try:
                image_data = requests.get(icon_url, stream=True).raw
                img = Image.open(image_data)
                img.save(icon_path)
            except Exception as e:
                self.set_status(f"Error loading icon: {e}")
                return None
        
        if size:
            img = img.resize(size)
        
        return ImageTk.PhotoImage(img)

    def process_weather_data(self, weather_data, forecast_data):
        units = self.units_var.get()
        self.weather_display.config(state=tk.NORMAL)
        self.weather_display.delete(1.0, tk.END)
        
        if weather_data and "error" not in weather_data:
            temp_unit = "°F" if units == "imperial" else "°C"
            self.current_city_display_var.set(f"{weather_data['name']}, {weather_data['sys']['country']}")
            self.temp_label.config(text=f"{weather_data['main']['temp']:.0f}{temp_unit}")
            
            icon_code = weather_data['weather'][0]['icon']
            icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
            
            photo = self.get_icon(icon_code, icon_url)
            if photo:
                self.icon_label.config(image=photo)
                self.icon_label.image = photo # Keep a reference

            self.weather_display.insert(tk.END, self.format_weather_data(weather_data, temp_unit))
            
            self.fade_in(self.current_city_label, self.fg_color)
            self.fade_in(self.temp_label, self.fg_color)
            self.fade_in(self.weather_display, self.fg_color)
            
            self.display_forecast(forecast_data)
            self.display_hourly_forecast(forecast_data)
            self.set_status("Weather updated")

        elif weather_data and "error" in weather_data:
            self.current_city_display_var.set("Error")
            self.temp_label.config(text="")
            self.icon_label.config(image="")
            self.clear_forecast()
            self.clear_hourly_forecast()
            self.set_status(weather_data["error"])
            if "API key" in weather_data["error"]:
                 messagebox.showerror("API Key Error", weather_data["error"])

        else:
            self.current_city_display_var.set("City Not Found")
            self.temp_label.config(text="")
            self.icon_label.config(image="")
            self.clear_forecast()
            self.clear_hourly_forecast()
            self.set_status(f"Could not retrieve weather for {weather_data['name'] if weather_data else 'city'}")
            
        self.weather_display.config(state=tk.DISABLED)

    def display_forecast(self, forecast_data):
        self.clear_forecast()

        if forecast_data and "daily" in forecast_data:
            for i, day in enumerate(forecast_data["daily"][:7]):
                day_frame = tk.Frame(self.forecast_frame, bg=self.text_bg_color)
                day_frame.pack(fill=tk.X, pady=2)
                
                day_name_label = tk.Label(day_frame, text=datetime.fromtimestamp(day['dt']).strftime('%a'), font=self.forecast_day_font, bg=self.text_bg_color, fg=self.bg_color)
                day_name_label.pack(side=tk.LEFT, padx=5)
                self.fade_in(day_name_label, self.fg_color)

                icon_code = day['weather'][0]['icon']
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}.png"
                photo = self.get_icon(icon_code, icon_url, (40, 40))
                if photo:
                    icon_label = tk.Label(day_frame, image=photo, bg=self.text_bg_color)
                    icon_label.image = photo
                    icon_label.pack(side=tk.LEFT, padx=5)

                temp_label = tk.Label(day_frame, text=f"{day['temp']['max']:.0f}° / {day['temp']['min']:.0f}°", font=self.forecast_temp_font, bg=self.text_bg_color, fg=self.bg_color)
                temp_label.pack(side=tk.RIGHT, padx=5)
                self.fade_in(temp_label, self.fg_color)


    def clear_forecast(self):
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()

    def display_hourly_forecast(self, forecast_data):
        self.clear_hourly_forecast()

        if forecast_data and "hourly" in forecast_data:
            for i, hour in enumerate(forecast_data["hourly"][:12]): # Display next 12 hours
                hour_frame = tk.Frame(self.hourly_forecast_frame, bg=self.text_bg_color)
                hour_frame.pack(side=tk.LEFT, padx=2)
                
                hour_name_label = tk.Label(hour_frame, text=datetime.fromtimestamp(hour['dt']).strftime('%H:%M'), font=self.hourly_forecast_font, bg=self.text_bg_color, fg=self.bg_color)
                hour_name_label.pack()
                self.fade_in(hour_name_label, self.fg_color)

                icon_code = hour['weather'][0]['icon']
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}.png"
                photo = self.get_icon(icon_code, icon_url, (30, 30))
                if photo:
                    icon_label = tk.Label(hour_frame, image=photo, bg=self.text_bg_color)
                    icon_label.image = photo
                    icon_label.pack()

                temp_label = tk.Label(hour_frame, text=f"{hour['temp']:.0f}°", font=self.hourly_forecast_font, bg=self.text_bg_color, fg=self.bg_color)
                temp_label.pack()
                self.fade_in(temp_label, self.fg_color)

    def clear_hourly_forecast(self):
        for widget in self.hourly_forecast_frame.winfo_children():
            widget.destroy()

    def format_weather_data(self, data, temp_unit):
        if not data or 'weather' not in data:
            return "No weather data available."
        
        weather = data['weather'][0]
        main = data['main']
        wind = data['wind']
        sys_data = data['sys']
        
        sunrise = datetime.fromtimestamp(sys_data['sunrise']).strftime('%H:%M:%S')
        sunset = datetime.fromtimestamp(sys_data['sunset']).strftime('%H:%M:%S')

        return "Description: " + weather['description'].capitalize() + "\n" + \
               "Feels like: " + str(round(main['feels_like'])) + temp_unit + "\n" + \
               "Humidity: " + str(main['humidity']) + "%\n" + \
               "Pressure: " + str(main['pressure']) + " hPa\n" + \
               "Wind Speed: " + str(wind['speed']) + " m/s\n" + \
               "Visibility: " + str(data.get('visibility', 'N/A')) + " meters\n" + \
               "Sunrise: " + sunrise + "\n" + \
               "Sunset: " + sunset + "\n"

    def fade_in(self, widget, end_color, steps=10, interval=20):
        start_color = self.bg_color
        
        start_rgb = self.winfo_rgb(start_color)
        end_rgb = self.winfo_rgb(end_color)

        dr = (end_rgb[0] - start_rgb[0]) / steps
        dg = (end_rgb[1] - start_rgb[1]) / steps
        db = (end_rgb[2] - start_rgb[2]) / steps

        def update_color(step):
            if step > steps:
                if isinstance(widget, tk.Text):
                    widget.config(fg=end_color)
                else:
                    widget.config(fg=end_color)
                return

            r = start_rgb[0] + int(dr * step)
            g = start_rgb[1] + int(dg * step)
            b = start_rgb[2] + int(db * step)
            
            # Ensure values are within the valid range for colors
            r = max(0, min(r, 65535))
            g = max(0, min(g, 65535))
            b = max(0, min(b, 65535))

            color = f"#{r:04x}{g:04x}{b:04x}"
            
            try:
                if isinstance(widget, tk.Text):
                    widget.config(fg=color)
                else:
                    widget.config(fg=color)
            except tk.TclError as e:
                # This can happen if the widget is destroyed during the animation
                print(f"TclError during fade_in: {e}")
                return


            self.after(interval, update_color, step + 1)
        
        update_color(0)


    def subscribe_city(self):
        city = self.city_var.get()
        if city:
            if city not in self.settings["subscriptions"]:
                self.settings["subscriptions"].append(city)
                self.subscriptions_listbox.insert(tk.END, city)
                self.save_settings()
                self.set_status(f"Subscribed to {city}")
            else:
                self.set_status(f"Already subscribed to {city}")

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
