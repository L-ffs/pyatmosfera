"""Fronteira com o banco: guarda e recupera usuários (um documento por e-mail)."""
from ..entity.city import City
from ..entity.user import User
from .firestore_client import FirestoreClient


class UserRepository:
    def __init__(self, client: FirestoreClient):
        self._client = client

    async def find_by_email(self, email: str) -> User | None:
        data = await self._client.get_document(email)
        if data is None:
            return None
        return User(
            email=data.get("email", email),
            name=data.get("name", ""),
            password_hash=data.get("password_hash", ""),
            cities=[City.from_dict(c) for c in data.get("cities", [])],
        )

    async def add(self, user: User) -> bool:
        """Grava um usuário novo. Retorna False se o e-mail já existe."""
        return await self._client.create_document(user.email, {
            "email": user.email,
            "name": user.name,
            "password_hash": user.password_hash,
            "cities": [self._city_fields(c) for c in user.cities],
        })

    async def save_cities(self, user: User) -> None:
        await self._client.update_document(
            user.email, {"cities": [self._city_fields(c) for c in user.cities]})

    async def save_password_hash(self, user: User) -> None:
        await self._client.update_document(user.email, {"password_hash": user.password_hash})

    @staticmethod
    def _city_fields(city: City) -> dict:
        return {"name": city.name, "state": city.state, "country": city.country,
                "latitude": city.latitude, "longitude": city.longitude,
                "timezone": city.timezone}
