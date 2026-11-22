"""Casos de uso de cidades: pesquisar (RF3), favoritar (RF4) e remover (RF6)."""
from ..entity.city import City
from ..entity.user import User
from ..external.geocoding_client import GeocodingClient
from ..external.user_repository import UserRepository
from ..support.errors import CityAlreadyFavorited, FavoriteNotFound, Unauthorized
from ..support.ttl_cache import TtlCache


class CityService:
    MIN_QUERY_LENGTH = 2

    def __init__(self, users: UserRepository, geocoding: GeocodingClient,
                 search_cache: TtlCache[list[City]]):
        self._users = users
        self._geocoding = geocoding
        self._cache = search_cache

    async def search(self, query: str) -> list[City]:
        query = query.strip()
        if len(query) < self.MIN_QUERY_LENGTH:
            return []
        key = query.lower()
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        cities = await self._geocoding.search(query)
        self._cache.set(key, cities)
        return cities

    async def list_favorites(self, email: str) -> list[City]:
        return (await self._load(email)).cities

    async def add_favorite(self, email: str, city: City) -> None:
        user = await self._load(email)
        if not user.add_city(city):
            raise CityAlreadyFavorited()
        await self._users.save_cities(user)

    async def remove_favorite(self, email: str, city_key: str) -> None:
        user = await self._load(email)
        if not user.remove_city(city_key):
            raise FavoriteNotFound()
        await self._users.save_cities(user)

    async def _load(self, email: str) -> User:
        user = await self._users.find_by_email(email)
        if user is None:
            raise Unauthorized()
        return user
