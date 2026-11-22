from dataclasses import dataclass, field

from .city import City


@dataclass
class User:
    email: str
    name: str
    password_hash: str
    cities: list[City] = field(default_factory=list)

    def has_city(self, city_key: str) -> bool:
        return any(c.key == city_key for c in self.cities)

    def add_city(self, city: City) -> bool:
        """Favorita a cidade. Retorna False se ela já estava na lista."""
        if self.has_city(city.key):
            return False
        self.cities.append(city)
        return True

    def remove_city(self, city_key: str) -> bool:
        """Remove a cidade. Retorna False se ela não estava na lista."""
        before = len(self.cities)
        self.cities = [c for c in self.cities if c.key != city_key]
        return len(self.cities) != before
