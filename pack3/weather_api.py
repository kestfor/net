import aiohttp
from config_reader import config


class Weather:

    def __init__(self, weather, temp, feels_like):
        self._weather = weather
        self._temp = temp
        self._feels_like = feels_like

    @property
    def weather(self):
        return self._weather

    @property
    def temp(self):
        return self._temp

    @property
    def feels_like(self):
        return self._feels_like

    def __repr__(self):
        return f"{self._weather}, {self._temp}°С, feels like {self._feels_like}°С"


class WeatherAPI:

    def __init__(self, api_key):
        self._api_key = api_key

    async def get_weather(self, lat, lon, session: aiohttp.ClientSession) -> Weather:
        print()
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self._api_key}"
        res = await session.get(url, timeout=3)
        js = await res.json()
        return Weather(js['weather'][0]['description'], int(js['main']['temp'] - 273.15), int(js['main']['feels_like'] - 273.15))


weather = WeatherAPI(config.weather_token.get_secret_value())