from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float
    timezone: str = "UTC"
    state: str = ""
    country: str = ""

    @property
    def key(self) -> str:
        """Identificador estável da cidade (duas cidades podem ter o mesmo nome)."""
        return f"{self.latitude:.4f},{self.longitude:.4f}"

    @property
    def display(self) -> str:
        text = self.name
        if self.state:
            text += f", {self.state}"
        if self.country:
            text += f" — {self.country}"
        return text

    def to_dict(self) -> dict:
        return {
            "name": self.name, "state": self.state, "country": self.country,
            "latitude": self.latitude, "longitude": self.longitude,
            "timezone": self.timezone, "key": self.key, "display": self.display,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "City":
        return cls(
            name=data["name"], latitude=float(data["latitude"]),
            longitude=float(data["longitude"]), timezone=data.get("timezone") or "UTC",
            state=data.get("state") or "", country=data.get("country") or "",
        )
