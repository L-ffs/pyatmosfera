from dataclasses import dataclass, field

from .city import City


class WeatherCondition:
    """Tradução dos códigos WMO (usados pela Open-Meteo) para texto em português."""

    _DESCRIPTIONS = {
        0: "Céu limpo", 1: "Predominantemente limpo", 2: "Parcialmente nublado",
        3: "Nublado", 45: "Névoa", 48: "Névoa com gelo",
        51: "Chuvisco leve", 53: "Chuvisco moderado", 55: "Chuvisco intenso",
        56: "Chuvisco congelante leve", 57: "Chuvisco congelante intenso",
        61: "Chuva leve", 63: "Chuva moderada", 65: "Chuva intensa",
        66: "Chuva congelante leve", 67: "Chuva congelante intensa",
        71: "Neve leve", 73: "Neve moderada", 75: "Neve intensa", 77: "Grãos de neve",
        80: "Pancadas de chuva leves", 81: "Pancadas de chuva moderadas",
        82: "Pancadas de chuva violentas", 85: "Pancadas de neve leves",
        86: "Pancadas de neve intensas", 95: "Tempestade",
        96: "Tempestade com granizo", 99: "Tempestade com granizo intenso",
    }

    @classmethod
    def describe(cls, code: int) -> str:
        return cls._DESCRIPTIONS.get(code, "Desconhecido")


@dataclass(frozen=True)
class CurrentWeather:
    temperature: float
    windspeed: float
    winddirection: int
    weathercode: int
    is_day: bool

    @property
    def condition(self) -> str:
        return WeatherCondition.describe(self.weathercode)


@dataclass(frozen=True)
class DailyForecast:
    date: str
    temp_max: float
    temp_min: float
    weathercode: int

    @property
    def condition(self) -> str:
        return WeatherCondition.describe(self.weathercode)


@dataclass(frozen=True)
class HourlyForecast:
    time: str
    temperature: float
    precipitation: int | None


@dataclass(frozen=True)
class WeatherSnapshot:
    city: City
    current: CurrentWeather
    daily: list[DailyForecast] = field(default_factory=list)
    hourly: list[HourlyForecast] = field(default_factory=list)

    def to_dict(self) -> dict:
        c = self.current
        return {
            "city": self.city.to_dict(),
            "current": {
                "temperature": c.temperature, "windspeed": c.windspeed,
                "winddirection": c.winddirection, "weathercode": c.weathercode,
                "condition": c.condition, "is_day": c.is_day,
            },
            "daily": [
                {"date": d.date, "temp_max": d.temp_max, "temp_min": d.temp_min,
                 "weathercode": d.weathercode, "condition": d.condition}
                for d in self.daily
            ],
            "hourly": [
                {"time": h.time, "temperature": h.temperature, "precipitation": h.precipitation}
                for h in self.hourly
            ],
        }
