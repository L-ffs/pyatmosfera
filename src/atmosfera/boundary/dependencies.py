"""Montagem das dependências de cada requisição (injeção do FastAPI)."""
from fastapi import Depends, Request

from ..control.auth_service import AuthService
from ..control.city_service import CityService
from ..control.session_service import SessionService
from ..control.weather_service import WeatherService
from ..entity.city import City
from ..entity.weather import WeatherSnapshot
from ..external.firestore_client import FirestoreClient
from ..external.forecast_client import ForecastClient
from ..external.geocoding_client import GeocodingClient
from ..external.user_repository import UserRepository
from ..support.errors import Unauthorized
from ..support.http_client import HttpClient
from ..support.password_hasher import PasswordHasher
from ..support.settings import Settings
from ..support.ttl_cache import TtlCache

SESSION_COOKIE = "atmosfera_session"


def get_settings(request: Request) -> Settings:
    state = request.app.state
    if getattr(state, "settings", None) is None:
        state.settings = Settings.load(request.scope.get("env"))
    return state.settings


def get_http_client() -> HttpClient:
    return HttpClient()


def get_session_service(settings: Settings = Depends(get_settings)) -> SessionService:
    return SessionService(settings.session_secret, settings.session_ttl_seconds)


def get_user_repository(settings: Settings = Depends(get_settings),
                        http: HttpClient = Depends(get_http_client)) -> UserRepository:
    return UserRepository(FirestoreClient(settings, http))


def get_auth_service(users: UserRepository = Depends(get_user_repository),
                     settings: Settings = Depends(get_settings),
                     sessions: SessionService = Depends(get_session_service)) -> AuthService:
    return AuthService(users, PasswordHasher(settings.pbkdf2_iterations), sessions)


def get_city_service(request: Request,
                     users: UserRepository = Depends(get_user_repository),
                     settings: Settings = Depends(get_settings),
                     http: HttpClient = Depends(get_http_client)) -> CityService:
    state = request.app.state
    if getattr(state, "search_cache", None) is None:
        state.search_cache = TtlCache[list[City]](settings.search_cache_seconds)
    return CityService(users, GeocodingClient(http), state.search_cache)


def get_weather_service(request: Request,
                        cities: CityService = Depends(get_city_service),
                        settings: Settings = Depends(get_settings),
                        http: HttpClient = Depends(get_http_client)) -> WeatherService:
    state = request.app.state
    if getattr(state, "weather_cache", None) is None:
        state.weather_cache = TtlCache[WeatherSnapshot](settings.weather_cache_seconds)
    return WeatherService(cities, ForecastClient(http), state.weather_cache)


def get_current_email(request: Request,
                      sessions: SessionService = Depends(get_session_service)) -> str:
    """E-mail do usuário logado (lido do cookie de sessão) ou 401."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise Unauthorized()
    return sessions.validate(token)
