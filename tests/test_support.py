import pytest

from atmosfera.support.errors import Unauthorized
from atmosfera.support.password_hasher import PasswordHasher
from atmosfera.support.settings import Settings
from atmosfera.support.ttl_cache import TtlCache
from atmosfera.control.session_service import SessionService


def test_hasher_roundtrip_and_salt():
    hasher = PasswordHasher(iterations=1000)
    h1, h2 = hasher.hash("senha-secreta"), hasher.hash("senha-secreta")
    assert h1 != h2  # salt diferente
    assert hasher.verify("senha-secreta", h1)
    assert not hasher.verify("outra-senha", h1)
    assert not hasher.verify("senha-secreta", "lixo")
    assert "senha-secreta" not in h1


def test_session_issue_and_validate():
    now = [1000.0]
    sessions = SessionService("s" * 32, 60, clock=lambda: now[0])
    token = sessions.issue("ana@exemplo.com")
    assert sessions.validate(token) == "ana@exemplo.com"
    now[0] += 61
    with pytest.raises(Unauthorized):
        sessions.validate(token)


def test_session_rejects_tampered_and_foreign_tokens():
    a = SessionService("a" * 32, 60)
    b = SessionService("b" * 32, 60)
    token = a.issue("ana@exemplo.com")
    header, payload, sig = token.split(".")
    for bad in ["", "abc", token + "x", f"{header}.{payload}.", b.issue("ana@exemplo.com"),
                f"{header}.{payload[:-2]}AA.{sig}"]:
        with pytest.raises(Unauthorized):
            a.validate(bad)


def test_ttl_cache_expiry_and_limit():
    now = [0.0]
    cache = TtlCache[int](10, max_size=2, clock=lambda: now[0])
    cache.set("a", 1)
    assert cache.get("a") == 1
    now[0] = 10
    assert cache.get("a") is None
    cache.set("x", 1)
    now[0] = 11
    cache.set("y", 2)
    cache.set("z", 3)  # cheio: descarta o mais antigo
    assert cache.get("x") is None and cache.get("y") == 2 and cache.get("z") == 3


def test_settings_load_and_validation():
    with pytest.raises(RuntimeError):
        Settings.load({"FIRESTORE_PROJECT_ID": "p", "SESSION_SECRET": "curto"})
    ok = Settings.load({"FIRESTORE_PROJECT_ID": "proj", "SESSION_SECRET": "x" * 32,
                        "COOKIE_SECURE": "false"})
    assert ok.firestore_project_id == "proj" and ok.cookie_secure is False
    assert ok.firestore_collection == "users"
