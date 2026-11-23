"""Hash de senha com PBKDF2-HMAC-SHA256 e salt aleatório.

No Cloudflare Workers o `hashlib.pbkdf2_hmac` não existe; lá usamos o WebCrypto do
runtime (nativo e rápido). Fora do Workers (desenvolvimento e testes) usa a biblioteca padrão.
Os dois caminhos geram exatamente o mesmo resultado.
"""
import base64
import hashlib
import hmac
import secrets


class PasswordHasher:
    ALGORITHM = "pbkdf2_sha256"

    def __init__(self, iterations: int = 100_000):
        self.iterations = iterations

    async def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = await self._derive(password, salt, self.iterations)
        return "$".join([
            self.ALGORITHM,
            str(self.iterations),
            base64.b64encode(salt).decode(),
            base64.b64encode(digest).decode(),
        ])

    async def verify(self, password: str, stored: str) -> bool:
        try:
            algorithm, iterations, salt_b64, digest_b64 = stored.split("$")
            if algorithm != self.ALGORITHM:
                return False
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(digest_b64)
            actual = await self._derive(password, salt, int(iterations))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(actual, expected)

    @staticmethod
    async def _derive(password: str, salt: bytes, iterations: int) -> bytes:
        try:
            from js import Object, Uint8Array, crypto  # só existem dentro do Workers
            from pyodide.ffi import to_js
        except ImportError:
            return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

        def to_uint8(data: bytes):
            array = Uint8Array.new(len(data))
            array.assign(data)
            return array

        key = await crypto.subtle.importKey(
            "raw", to_uint8(password.encode("utf-8")), "PBKDF2", False, to_js(["deriveBits"]))
        params = to_js(
            {"name": "PBKDF2", "hash": "SHA-256", "salt": to_uint8(salt), "iterations": iterations},
            dict_converter=Object.fromEntries)
        bits = await crypto.subtle.deriveBits(params, key, 256)
        return bytes(Uint8Array.new(bits).to_py())
