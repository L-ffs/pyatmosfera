"""Fronteira de clima: RF5 (clima das cidades favoritas)."""
from fastapi import APIRouter, Depends

from ..control.weather_service import WeatherService
from .dependencies import get_current_email, get_weather_service


class WeatherRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api", tags=["clima"])
        self.router.add_api_route("/weather/favorites", self.favorites, methods=["GET"])

    async def favorites(self, email: str = Depends(get_current_email),
                        weather: WeatherService = Depends(get_weather_service)):
        items = await weather.favorites_weather(email)
        return {"cities": [item.to_dict() for item in items]}
