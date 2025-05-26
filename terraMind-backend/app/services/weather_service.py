import requests
import os
from dotenv import load_dotenv

load_dotenv()


def get_weather(location):
    """
    Get current weather for a location using OpenWeatherMap API
    """
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "Weather API key not configured"
        }

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()

        return {
            "success": True,
            "location": data["name"],
            "country": data["sys"]["country"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "message": f"Current weather in {data['name']}: {data['weather'][0]['description']}, {data['main']['temp']}°C"
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
        return {
            "success": False,
            "error": str(e)
        }