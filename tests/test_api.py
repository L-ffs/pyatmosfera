"""Teste ponta a ponta da API (routers + serviços) com banco e Open-Meteo falsos.

Precisa de fastapi e httpx instalados; sem eles o arquivo é ignorado.
"""
import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from atmosfera.boundary import dependencies as deps  # noqa: E402
from atmosfera.main import create_app  # noqa: E402
from atmosfera.support.settings import Settings  # noqa: E402

from fakes import FakeHttp, FakeUserRepository  # noqa: E402
from test_external import FORECAST  # noqa: E402

CITY = {"name": "Juiz de Fora", "state": "Minas Gerais", "country": "Brasil",
        "latitude": -21.76, "longitude": -43.35, "timezone": "America/Sao_Paulo"}


@pytest.fixture()
def client():
    app = create_app()
    http, users = FakeHttp(), FakeUserRepository()
    http.on("GET", "geocoding-api", 200, json.dumps({"results": [CITY]}))
    http.on("GET", "api.open-meteo.com", 200, json.dumps(FORECAST))
    settings = Settings(session_secret="k" * 32, firestore_project_id="p",
                        cookie_secure=False, pbkdf2_iterations=1000)
    app.dependency_overrides[deps.get_settings] = lambda: settings
    app.dependency_overrides[deps.get_http_client] = lambda: http
    app.dependency_overrides[deps.get_user_repository] = lambda: users
    return TestClient(app)


def login(client):
    body = {"nome": "Ana", "email": "ana@x.com", "senha": "senha-forte-1"}
    assert client.post("/api/auth/signup", json=body).status_code == 201
    response = client.post("/api/auth/login", json={"email": "ana@x.com", "senha": "senha-forte-1"})
    assert response.status_code == 200
    return response


def test_full_flow(client):
    login(client)
    assert client.get("/api/me").json() == {"name": "Ana", "email": "ana@x.com"}
    found = client.get("/api/cities/search", params={"q": "juiz"}).json()["results"]
    assert found[0]["name"] == "Juiz de Fora"
    assert client.post("/api/favorites", json=CITY).status_code == 201
    assert client.post("/api/favorites", json=CITY).status_code == 409
    cities = client.get("/api/weather/favorites").json()["cities"]
    assert cities[0]["current"]["condition"] == "Nublado"
    key = cities[0]["city"]["key"]
    assert client.delete(f"/api/favorites/{key}").status_code == 200
    assert client.get("/api/weather/favorites").json()["cities"] == []
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/me").status_code == 401


def test_errors(client):
    assert client.get("/api/me").status_code == 401
    bad = client.post("/api/auth/signup", json={"nome": "A", "email": "x", "senha": "1"})
    assert bad.status_code == 400 and bad.json()["field"] == "nome"
    login(client)
    wrong = client.post("/api/auth/login", json={"email": "ana@x.com", "senha": "errada-errada"})
    assert wrong.status_code == 401 and wrong.json()["error"] == "E-mail ou senha incorretos."
    assert client.post("/api/auth/password",
                       json={"senha_atual": "senha-forte-1", "nova_senha": "nova-senha-9"}).status_code == 200
