import asyncio
import json

import pytest

from atmosfera.entity.city import City
from atmosfera.entity.user import User
from atmosfera.external.firestore_client import FirestoreClient
from atmosfera.external.forecast_client import ForecastClient
from atmosfera.external.geocoding_client import GeocodingClient
from atmosfera.external.user_repository import UserRepository
from atmosfera.support.errors import ExternalServiceError
from atmosfera.support.settings import Settings

from fakes import FakeHttp

SETTINGS = Settings(session_secret="x" * 32, firestore_project_id="proj")
JF = City("Juiz de Fora", -21.76, -43.35, "America/Sao_Paulo", "Minas Gerais", "Brasil")
run = asyncio.run


def test_firestore_codec_roundtrip_with_nested_values():
    plain = {"s": "texto", "i": 3, "f": 1.5, "b": True, "n": None,
             "lista": [{"name": "A", "latitude": -1.5}, {"name": "B", "latitude": 2.0}]}
    encoded = FirestoreClient._encode_fields(plain)
    assert encoded["fields"]["i"] == {"integerValue": "3"}
    assert encoded["fields"]["b"] == {"booleanValue": True}  # bool não vira inteiro
    assert FirestoreClient._decode_fields(encoded) == plain


def test_firestore_get_create_update():
    http = FakeHttp()
    client = FirestoreClient(SETTINGS, http)
    http.on("GET", "/users/ana%40x.com", 404)
    assert run(client.get_document("ana@x.com")) is None

    http.rules.clear()
    http.on("GET", "/users/", 200, json.dumps({"fields": {"name": {"stringValue": "Ana"}}}))
    assert run(client.get_document("ana@x.com")) == {"name": "Ana"}

    http.rules.clear()
    http.on("POST", "/documents/users", 409)
    assert run(client.create_document("ana@x.com", {"name": "Ana"})) is False
    http.rules.clear()
    http.on("POST", "/documents/users", 200)
    assert run(client.create_document("ana@x.com", {"name": "Ana"})) is True
    assert http.calls[-1]["params"]["documentId"] == "ana@x.com"

    http.rules.clear()
    http.on("PATCH", "/users/", 200)
    run(client.update_document("ana@x.com", {"cities": [], "name": "Ana"}))
    assert ("updateMask.fieldPaths", "cities") in http.calls[-1]["params"]

    http.rules.clear()
    http.on("GET", "/users/", 500)
    with pytest.raises(ExternalServiceError):
        run(client.get_document("ana@x.com"))


def test_firestore_adds_api_key_when_configured():
    http = FakeHttp()
    settings = Settings(session_secret="x" * 32, firestore_project_id="p", firestore_api_key="K")
    http.on("GET", "/users/", 404)
    run(FirestoreClient(settings, http).get_document("a@b.co"))
    assert http.calls[0]["params"] == {"key": "K"}


def test_user_repository_maps_documents():
    http = FakeHttp()
    repo = UserRepository(FirestoreClient(SETTINGS, http))
    user = User("ana@x.com", "Ana", "hash", [JF])
    http.on("POST", "/documents/users", 200)
    assert run(repo.add(user)) is True
    stored = http.calls[-1]["json"]["fields"]
    assert stored["password_hash"] == {"stringValue": "hash"}
    assert len(stored["cities"]["arrayValue"]["values"]) == 1

    http.rules.clear()
    http.on("GET", "/users/", 200, json.dumps({"fields": stored}))
    loaded = run(repo.find_by_email("ana@x.com"))
    assert loaded == user


def test_geocoding_client_parses_results():
    http = FakeHttp()
    http.on("GET", "geocoding-api", 200, json.dumps({"results": [
        {"name": "Juiz de Fora", "latitude": -21.76, "longitude": -43.35,
         "timezone": "America/Sao_Paulo", "admin1": "Minas Gerais", "country": "Brasil"},
        {"name": "Sem coordenadas"},
    ]}))
    cities = run(GeocodingClient(http).search("juiz"))
    assert cities == [JF]
    http.rules.clear()
    http.on("GET", "geocoding-api", 200, "{}")  # sem "results"
    assert run(GeocodingClient(http).search("zzzz")) == []
    http.rules.clear()
    http.on("GET", "geocoding-api", 503)
    with pytest.raises(ExternalServiceError):
        run(GeocodingClient(http).search("juiz"))


FORECAST = {
    "current_weather": {"temperature": 22.5, "windspeed": 7.0, "winddirection": 180,
                        "weathercode": 3, "is_day": 1, "time": "2026-11-22T13:00"},
    "daily": {"time": ["2026-11-22", "2026-11-23"], "weathercode": [3, 61],
              "temperature_2m_max": [28.0, 25.0], "temperature_2m_min": [17.0, 16.0]},
    "hourly": {"time": [f"2026-11-22T{h:02d}:00" for h in range(24)] + ["2026-11-23T00:00"],
               "temperature_2m": list(range(25)), "precipitation_probability": [10] * 25},
}


def test_forecast_client_parses_snapshot():
    http = FakeHttp()
    http.on("GET", "api.open-meteo.com", 200, json.dumps(FORECAST))
    snap = run(ForecastClient(http).fetch(JF))
    assert snap.current.temperature == 22.5 and snap.current.condition == "Nublado"
    assert snap.current.is_day is True
    assert [d.condition for d in snap.daily] == ["Nublado", "Chuva leve"]
    assert snap.hourly[0].time == "2026-11-22T13:00"   # começa na hora atual
    assert len(snap.hourly) == 12                       # restam 12 horas na lista
    assert snap.to_dict()["current"]["condition"] == "Nublado"


def test_forecast_client_rejects_bad_payload():
    http = FakeHttp()
    http.on("GET", "api.open-meteo.com", 200, "{}")
    with pytest.raises(ExternalServiceError):
        run(ForecastClient(http).fetch(JF))
