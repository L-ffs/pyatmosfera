"""Hash de senha com PBKDF2-HMAC-SHA256 e salt aleatório (biblioteca padrão)."""
import base64
import hashlib
import hmac
import secrets


class PasswordHasher:
    ALGORITHM = "pbkdf2_sha256"

    def __init__(self, iterations: int = 100_000):
        self.iterations = iterations

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = self._derive(password, salt, self.iterations)
        return "$".join([
            self.ALGORITHM,
            str(self.iterations),
            base64.b64encode(salt).decode(),
            base64.b64encode(digest).decode(),
        ])

    def verify(self, password: str, stored: str) -> bool:
        try:
            algorithm, iterations, salt_b64, digest_b64 = stored.split("$")
            if algorithm != self.ALGORITHM:
                return False
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(digest_b64)
            actual = self._derive(password, salt, int(iterations))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(actual, expected)

    @staticmethod
    def _derive(password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
