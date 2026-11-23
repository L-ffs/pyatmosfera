"""Configuração lida do ambiente (variáveis e segredos do Cloudflare ou do shell)."""
import os
from dataclasses import dataclass


def _read(env, name: str, default: str | None = None) -> str | None:
    """Lê `name` dos bindings do Workers (objeto ou mapa) e, se faltar, de os.environ."""
    value = None
    if env is not None:
        value = getattr(env, name, None)
        if value is None:
            try:
                value = env[name]
            except (KeyError, TypeError, AttributeError, IndexError):
                value = None
    if value is None:
        value = os.environ.get(name)
    if value is None or str(value) in ("undefined", "null"):
        return default
    return str(value)


def _text(env, name: str, default: str) -> str:
    return _read(env, name, default) or default


@dataclass(frozen=True)
class Settings:
    session_secret: str
    firestore_project_id: str
    firestore_collection: str = "users"
    firestore_api_key: str | None = None
    session_ttl_seconds: int = 8 * 3600
    pbkdf2_iterations: int = 100_000
    cookie_secure: bool = True
    weather_cache_seconds: int = 3600
    search_cache_seconds: int = 3600

    @classmethod
    def load(cls, env=None) -> "Settings":
        secret = _read(env, "SESSION_SECRET")
        project = _read(env, "FIRESTORE_PROJECT_ID")
        if not secret:
            raise RuntimeError("SESSION_SECRET não foi encontrada no ambiente do Worker.")
        if len(secret) < 32:
            raise RuntimeError(f"SESSION_SECRET tem {len(secret)} caracteres; são necessários 32 ou mais.")
        if not project:
            raise RuntimeError("FIRESTORE_PROJECT_ID não foi encontrada no ambiente do Worker.")
        return cls(
            session_secret=secret,
            firestore_project_id=project,
            firestore_collection=_read(env, "FIRESTORE_COLLECTION", "users") or "users",
            firestore_api_key=_read(env, "FIRESTORE_API_KEY"),
            session_ttl_seconds=int(_text(env, "SESSION_TTL_SECONDS", str(8 * 3600))),
            pbkdf2_iterations=int(_text(env, "PBKDF2_ITERATIONS", "100000")),
            cookie_secure=_text(env, "COOKIE_SECURE", "true").lower() != "false",
            weather_cache_seconds=int(_text(env, "WEATHER_CACHE_SECONDS", "3600")),
            search_cache_seconds=int(_text(env, "SEARCH_CACHE_SECONDS", "3600")),
        )