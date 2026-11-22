import asyncio

import pytest

from atmosfera.control.auth_service import AuthService
from atmosfera.control.city_service import CityService
from atmosfera.control.session_service import SessionService
from atmosfera.control.weather_service import WeatherService
from atmosfera.entity.city import City
from atmosfera.entity.weather import CurrentWeather, WeatherSnapshot
from atmosfera.support.errors import (
    CityAlreadyFavorited, EmailAlreadyExists, ExternalServiceError, FavoriteNotFound,
    InvalidCredentials, Unauthorized, WrongCurrentPassword)
from atmosfera.support.password_hasher import PasswordHasher
from atmosfera.support.ttl_cache import TtlCache

from fakes import FakeUserRepository

run = asyncio.run
JF = City("Juiz de Fora", -21.76, -43.35, "America/Sao_Paulo", "Minas Gerais", "Brasil")
RIO = City("Rio de Janeiro", -22.9, -43.2, "America/Sao_Paulo", "Rio de Janeiro", "Brasil")


def make_auth():
    users = FakeUserRepository()
    sessions = SessionService("k" * 32, 3600)
    return AuthService(users, PasswordHasher(1000), sessions), users, sessions


def test_signup_and_duplicate_email():
    auth, users, _ = make_auth()
    run(auth.signup("Ana", "ana@x.com", "senha-forte-1"))
    assert users.users["ana@x.com"].password_hash.startswith("pbkdf2_sha256$")
    with pytest.raises(EmailAlreadyExists):
        run(auth.signup("Ana 2", "ana@x.com", "outra-senha-1"))


def test_login_success_and_failures():
    auth, _, sessions = make_auth()
    run(auth.signup("Ana", "ana@x.com", "senha-forte-1"))
    user, token = run(auth.login("ana@x.com", "senha-forte-1"))
    assert user.name == "Ana" and sessions.validate(token) == "ana@x.com"
    with pytest.raises(InvalidCredentials):
        run(auth.login("ana@x.com", "errada-errada"))
    with pytest.raises(InvalidCredentials):  # e-mail inexistente: mesma resposta
        run(auth.login("nao@existe.com", "senha-forte-1"))


def test_change_password():
    auth, _, _ = make_auth()
    run(auth.signup("Ana", "ana@x.com", "senha-forte-1"))
    with pytest.raises(WrongCurrentPassword):
        run(auth.change_password("ana@x.com", "errada-errada", "nova-senha-9"))
    run(auth.change_password("ana@x.com", "senha-forte-1", "nova-senha-9"))
    run(auth.login("ana@x.com", "nova-senha-9"))
    with pytest.raises(InvalidCredentials):
        run(auth.login("ana@x.com", "senha-forte-1"))
    with pytest.raises(Unauthorized):
        run(auth.change_password("fantasma@x.com", "a", "nova-senha-9"))


class FakeGeocoding:
    def __init__(self, results):
        self.results, self.calls = results, 0

    async def search(self, query, count=5):
        self.calls += 1
        return self.results


def make_cities(results=(JF,)):
    auth, users, _ = make_auth()
    run(auth.signup("Ana", "ana@x.com", "senha-forte-1"))
    geo = FakeGeocoding(list(results))
    return CityService(users, geo, TtlCache(60)), geo


def test_search_rules_and_cache():
    cities, geo = make_cities()
    assert run(cities.search(" j ")) == [] and geo.calls == 0  # curto demais
    assert run(cities.search("Juiz")) == [JF]
    assert run(cities.search("juiz")) == [JF] and geo.calls == 1  # veio do cache


def test_favorites_add_duplicate_remove():
    cities, _ = make_cities()
    run(cities.add_favorite("ana@x.com", JF))
    with pytest.raises(CityAlreadyFavorited):
        run(cities.add_favorite("ana@x.com", JF))
    assert run(cities.list_favorites("ana@x.com")) == [JF]
    run(cities.remove_favorite("ana@x.com", JF.key))
    with pytest.raises(FavoriteNotFound):
        run(cities.remove_favorite("ana@x.com", JF.key))
    assert run(cities.list_favorites("ana@x.com")) == []
    with pytest.raises(Unauthorized):
        run(cities.list_favorites("fantasma@x.com"))


class FakeForecast:
    def __init__(self, failing=()):
        self.failing, self.calls = set(failing), 0

    async def fetch(self, city):
        self.calls += 1
        if city.name in self.failing:
            raise ExternalServiceError()
        return WeatherSnapshot(city, CurrentWeather(20.0, 5.0, 90, 0, True))


def test_weather_for_favorites_isolates_failures_and_caches():
    cities, _ = make_cities()
    run(cities.add_favorite("ana@x.com", JF))
    run(cities.add_favorite("ana@x.com", RIO))
    forecast = FakeForecast(failing={"Rio de Janeiro"})
    weather = WeatherService(cities, forecast, TtlCache(60))

    items = run(weather.favorites_weather("ana@x.com"))
    assert [i.city for i in items] == [JF, RIO]
    assert items[0].snapshot is not None and items[0].error is None
    assert items[1].snapshot is None and "indisponível" in items[1].error.lower()
    assert items[1].to_dict()["error"]

    run(weather.favorites_weather("ana@x.com"))
    assert forecast.calls == 3  # JF veio do cache na 2ª vez; Rio falhou de novo
