import python_weather
import asyncio
from unisonai import BaseTool, Field
from ui.UI import create_weather_widget
import os

class WeatherTool(BaseTool):
    name = "Weather Tool"
    description = "Get the current weather for a given city."
    params = [Field("city", "The city to check weather for")]

    async def _run(self, city: str):
        return await self.weather(city)

    async def weather(self, city: str):
        # Declare the client. The measuring unit used defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            
            # Fetch a weather forecast from a city.
            weather = await client.get(city)
            
            # Fetch the temperature for today.
            print(f"  Temperature: {weather.temperature}°F")
            print(f"  Feels like: {weather.feels_like}°F")
            print(f"  Humidity: {weather.humidity}%")
            print(f"  Wind Speed: {weather.wind_speed} m/s")
            print(f"  Description: {weather.description}")
            
            # Fetch weather forecast for upcoming days.
            for daily in weather:
                print(daily)
            
                # Each daily forecast has their own hourly forecasts.
                for hourly in daily:
                    print(f' --> {hourly!r}')

            if weather.description == "Clouds":
                main_condition = "Clouds"
            if weather.description == "Rain":
                main_condition = "Rain"
            if weather.description == "Clear" or weather.description == "Sunny":
                main_condition = "Clear"
            if weather.description == "Snow":
                main_condition = "Snow"
            if weather.description == "Thunderstorm":
                main_condition = "Thunderstorm"
            if weather.description == "Light Rain":
                main_condition = "Drizzle"
            if weather.description == "Mist":
                main_condition = "Mist"
            if weather.description == "Haze":
                main_condition = "Haze"
            if weather.description == "Smoke":
                main_condition = "Smoke"
            if weather.description == "Dust":
                main_condition = "Dust"
            if weather.description == "Fog":
                main_condition = "Fog"
            if weather.description == "Sand":
                main_condition = "Sand"
            if weather.description == "Ash":
                main_condition = "Ash"
            if weather.description == "Squall":
                main_condition = "Squall"
            if weather.description == "Tornado":
                main_condition = "Tornado"
            else:
                main_condition = "Unknown"

            weather_data = {
            "temperature": f"{weather.temperature}°F",
            "location": city,
            "description": weather.description,
            "main_condition": main_condition,  # This key is used by JS to pick the main icon
            "humidity": f"{weather.humidity}%",
            "wind": f"{weather.wind_speed} m/s",
            "feels_like": f"{weather.feels_like}°F",
            }
            try:
                create_weather_widget(weather_data)
            except:
                pass

            return weather_data
        
if __name__ == "__main__":
    tool = WeatherTool()
    print(asyncio.run(tool._run("")))