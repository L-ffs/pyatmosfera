"""Fronteira com a Open-Meteo: busca de cidades pelo nome."""
from ..entity.city import City
from ..support.errors import ExternalServiceError
from ..support.http_client import HttpClient


class GeocodingClient:
    URL = "https://geocoding-api.open-meteo.com/v1/search"

    def __init__(self, http: HttpClient):
        self._http = http

    async def search(self, query: str, count: int = 5) -> list[City]:
        result = await self._http.request("GET", self.URL, params={
            "name": query, "count": count, "language": "pt", "format": "json"})
        if result.status != 200:
            raise ExternalServiceError()
        cities = []
        for item in result.json().get("results", []):
            if not item.get("name") or "latitude" not in item or "longitude" not in item:
                continue
            cities.append(City(
                name=item["name"], latitude=item["latitude"], longitude=item["longitude"],
                timezone=item.get("timezone", "UTC"), state=item.get("admin1", ""),
                country=item.get("country", ""),
            ))
        return cities
