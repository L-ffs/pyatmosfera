"""Dublês usados nos testes (sem rede e sem banco)."""
from atmosfera.entity.user import User
from atmosfera.support.errors import ExternalServiceError
from atmosfera.support.http_client import HttpResult


class FakeHttp:
    """Responde conforme regras (método, trecho da URL) e guarda as chamadas feitas."""

    def __init__(self):
        self.rules: list[tuple[str, str, HttpResult]] = []
        self.calls: list[dict] = []

    def on(self, method: str, url_part: str, status: int = 200, body: str = "{}"):
        self.rules.append((method, url_part, HttpResult(status, body)))

    async def request(self, method, url, *, params=None, json=None):
        self.calls.append({"method": method, "url": url, "params": params, "json": json})
        for rule_method, part, result in self.rules:
            if rule_method == method and part in url:
                return result
        raise ExternalServiceError()


class FakeUserRepository:
    def __init__(self):
        self.users: dict[str, User] = {}

    async def find_by_email(self, email):
        return self.users.get(email)

    async def add(self, user):
        if user.email in self.users:
            return False
        self.users[user.email] = user
        return True

    async def save_cities(self, user):
        self.users[user.email] = user

    async def save_password_hash(self, user):
        self.users[user.email] = user
