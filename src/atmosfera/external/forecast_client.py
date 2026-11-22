"""Fronteira com a Open-Meteo: previsão do tempo de uma cidade."""
from ..entity.city import City
from ..entity.weather import CurrentWeather, DailyForecast, HourlyForecast, WeatherSnapshot
from ..support.errors import ExternalServiceError
from ..support.http_client import HttpClient


class ForecastClient:
    URL = "https://api.open-meteo.com/v1/forecast"
    HOURS_SHOWN = 24

    def __init__(self, http: HttpClient):
        self._http = http

    async def fetch(self, city: City) -> WeatherSnapshot:
        result = await self._http.request("GET", self.URL, params={
            "latitude": city.latitude, "longitude": city.longitude,
            "timezone": city.timezone, "current_weather": "true",
            "hourly": "temperature_2m,precipitation_probability",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "forecast_days": 7,
        })
        if result.status != 200:
            raise ExternalServiceError()
        try:
            return self._parse(city, result.json())
        except (KeyError, TypeError, ValueError) as exc:
            raise ExternalServiceError("Resposta inválida da previsão.") from exc

    def _parse(self, city: City, data: dict) -> WeatherSnapshot:
        cw = data["current_weather"]
        current = CurrentWeather(
            temperature=cw["temperature"], windspeed=cw["windspeed"],
            winddirection=int(cw.get("winddirection", 0)),
            weathercode=int(cw["weathercode"]), is_day=cw.get("is_day", 1) == 1,
        )
        daily = []
        if "daily" in data:
            d = data["daily"]
            for i, date in enumerate(d["time"]):
                daily.append(DailyForecast(
                    date=date, temp_max=d["temperature_2m_max"][i],
                    temp_min=d["temperature_2m_min"][i], weathercode=int(d["weathercode"][i])))
        hourly = []
        if "hourly" in data:
            h = data["hourly"]
            start = next((i for i, t in enumerate(h["time"]) if t >= cw.get("time", "")), 0)
            for i in range(start, min(start + self.HOURS_SHOWN, len(h["time"]))):
                precipitation = h.get("precipitation_probability", [None] * len(h["time"]))[i]
                hourly.append(HourlyForecast(
                    time=h["time"][i], temperature=h["temperature_2m"][i],
                    precipitation=precipitation))
        return WeatherSnapshot(city=city, current=current, daily=daily, hourly=hourly)
