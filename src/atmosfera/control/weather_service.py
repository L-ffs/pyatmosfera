"""Caso de uso RF5: clima atual das cidades favoritas do usuário."""
import asyncio
from dataclasses import dataclass

from ..entity.city import City
from ..entity.weather import WeatherSnapshot
from ..external.forecast_client import ForecastClient
from ..support.errors import AppError
from ..support.ttl_cache import TtlCache
from .city_service import CityService


@dataclass
class FavoriteWeather:
    city: City
    snapshot: WeatherSnapshot | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        if self.snapshot is not None:
            return self.snapshot.to_dict()
        return {"city": self.city.to_dict(), "error": self.error or "Clima indisponível."}


class WeatherService:
    def __init__(self, cities: CityService, forecast: ForecastClient,
                 cache: TtlCache[WeatherSnapshot]):
        self._cities = cities
        self._forecast = forecast
        self._cache = cache

    async def for_city(self, city: City) -> WeatherSnapshot:
        cached = self._cache.get(city.key)
        if cached is not None:
            return cached
        snapshot = await self._forecast.fetch(city)
        self._cache.set(city.key, snapshot)
        return snapshot

    async def favorites_weather(self, email: str) -> list[FavoriteWeather]:
        cities = await self._cities.list_favorites(email)
        results = await asyncio.gather(
            *(self.for_city(c) for c in cities), return_exceptions=True)
        weather = []
        for city, result in zip(cities, results):
            if isinstance(result, WeatherSnapshot):
                weather.append(FavoriteWeather(city, snapshot=result))
            else:
                message = result.message if isinstance(result, AppError) else None
                weather.append(FavoriteWeather(city, error=message or "Clima indisponível."))
        return weather
