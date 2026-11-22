"""Sessão do usuário: emite e valida tokens JWT (HS256) assinados pelo servidor."""
import base64
import hashlib
import hmac
import json
import time
from typing import Callable

from ..support.errors import Unauthorized


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class SessionService:
    def __init__(self, secret: str, ttl_seconds: int, clock: Callable[[], float] = time.time):
        self._secret = secret.encode()
        self.ttl_seconds = ttl_seconds
        self._clock = clock

    def issue(self, email: str) -> str:
        now = int(self._clock())
        header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = _b64(json.dumps({"sub": email, "iat": now, "exp": now + self.ttl_seconds}).encode())
        return f"{header}.{payload}.{self._sign(f'{header}.{payload}')}"

    def validate(self, token: str) -> str:
        """Retorna o e-mail do dono do token ou lança Unauthorized."""
        try:
            header, payload, signature = token.split(".")
            if not hmac.compare_digest(signature, self._sign(f"{header}.{payload}")):
                raise Unauthorized()
            if json.loads(_unb64(header)).get("alg") != "HS256":
                raise Unauthorized()
            claims = json.loads(_unb64(payload))
            if claims["exp"] <= self._clock():
                raise Unauthorized()
            return claims["sub"]
        except Unauthorized:
            raise
        except (ValueError, KeyError, TypeError):
            raise Unauthorized() from None

    def _sign(self, message: str) -> str:
        return _b64(hmac.new(self._secret, message.encode(), hashlib.sha256).digest())
