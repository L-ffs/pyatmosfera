"""Fronteira de cidades: RF3 (pesquisar), RF4 (favoritar) e RF6 (remover favorita)."""
from fastapi import APIRouter, Depends

from ..control.city_service import CityService
from ..entity.city import City
from .dependencies import get_city_service, get_current_email
from .schemas import CityRequest


class CityRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api", tags=["cidades"])
        self.router.add_api_route("/cities/search", self.search, methods=["GET"])
        self.router.add_api_route("/favorites", self.add_favorite, methods=["POST"], status_code=201)
        self.router.add_api_route("/favorites/{city_key}", self.remove_favorite, methods=["DELETE"])

    async def search(self, q: str = "", _email: str = Depends(get_current_email),
                     cities: CityService = Depends(get_city_service)):
        results = await cities.search(q)
        return {"results": [c.to_dict() for c in results]}

    async def add_favorite(self, body: CityRequest, email: str = Depends(get_current_email),
                           cities: CityService = Depends(get_city_service)):
        city = City(name=body.name.strip(), latitude=body.latitude, longitude=body.longitude,
                    timezone=body.timezone, state=body.state, country=body.country)
        await cities.add_favorite(email, city)
        return {"message": "Cidade favoritada.", "city": city.to_dict()}

    async def remove_favorite(self, city_key: str, email: str = Depends(get_current_email),
                              cities: CityService = Depends(get_city_service)):
        await cities.remove_favorite(email, city_key)
        return {"message": "Cidade removida dos favoritos."}
