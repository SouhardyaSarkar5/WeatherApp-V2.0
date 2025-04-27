from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

API_KEY = "942ede6e8b41006a9e425153a47f42b5"  # Your OpenWeatherMap API key

def get_icon(condition):
    condition = condition.lower()
    if "clear" in condition or "sun" in condition:
        return "☀️"
    elif "cloud" in condition or "overcast" in condition:
        return "☁️"
    elif "rain" in condition or "drizzle" in condition:
        return "🌧️"
    elif "storm" in condition or "thunder" in condition:
        return "⛈️"
    elif "snow" in condition or "sleet" in condition:
        return "❄️"
    elif "fog" in condition or "mist" in condition or "haze" in condition:
        return "🌫️"
    elif "wind" in condition:
        return "💨"
    else:
        return "❓"

def fetch_weather(city_name):
    try:
        # First attempt
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
        geo_res = requests.get(geo_url)
        geo_data = geo_res.json()

        if geo_res.status_code != 200 or not geo_data:
            # Retry with broader search (limit=5)
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=5&appid={API_KEY}"
            geo_res = requests.get(geo_url)
            geo_data = geo_res.json()

            if geo_res.status_code != 200 or not geo_data:
                return None

            # Pick first valid result
            geo_info = next((item for item in geo_data if "lat" in item and "lon" in item and item.get("name")), None)
            if not geo_info:
                return None
        else:
            geo_info = geo_data[0]

        lat = geo_info["lat"]
        lon = geo_info["lon"]

        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        weather_res = requests.get(weather_url)
        if weather_res.status_code != 200:
            return None
        data = weather_res.json()

        condition = data["weather"][0]["description"].title()
        temp_c = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_kph = data["wind"]["speed"] * 3.6
        icon_code = data["weather"][0]["icon"]
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

        sunrise_unix = data["sys"]["sunrise"]
        sunset_unix = data["sys"]["sunset"]
        timezone_offset = data["timezone"]

        sunrise_local = datetime.utcfromtimestamp(sunrise_unix + timezone_offset).strftime("%H:%M")
        sunset_local = datetime.utcfromtimestamp(sunset_unix + timezone_offset).strftime("%H:%M")

        return {
            "location": f"{data['name']}, {data['sys']['country']}",
            "condition": condition,
            "temp": f"{temp_c}°C",
            "humidity": f"{humidity}%",
            "wind": f"{wind_kph:.1f} km/h",
            "sunrise": sunrise_local,
            "sunset": sunset_local,
            "icon": get_icon(condition),
            "icon_url": icon_url
        }
    except Exception as e:
        print("Error fetching weather:", e)
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    error = None
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    if request.method == "POST":
        city = request.form.get("city")
        weather = fetch_weather(city)
        if not weather:
            error = "Couldn't fetch weather for that city."

    return render_template("index.html", weather=weather, error=error, today_date=today_date)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
