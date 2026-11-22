"""Cliente HTTP de saída.

No Cloudflare Workers usa o `fetch` do runtime (via pyodide); fora dele (desenvolvimento
local e testes) usa o httpx. Não conhece nenhum serviço específico.
"""
import json as jsonlib
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from .errors import ExternalServiceError


@dataclass
class HttpResult:
    status: int
    body: str

    def json(self) -> Any:
        return jsonlib.loads(self.body) if self.body else {}


class HttpClient:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def request(self, method: str, url: str, *, params: dict | list | None = None,
                      json: Any = None) -> HttpResult:
        if params:
            url = f"{url}?{urlencode(params)}"
        headers = {"Content-Type": "application/json"} if json is not None else {}
        body = jsonlib.dumps(json) if json is not None else None
        try:
            try:
                from pyodide.http import pyfetch  # presente só no Workers
            except ImportError:
                return await self._with_httpx(method, url, headers, body)
            options: dict[str, Any] = {"method": method, "headers": headers}
            if body is not None:
                options["body"] = body
            response = await pyfetch(url, **options)
            return HttpResult(status=response.status, body=await response.string())
        except ExternalServiceError:
            raise
        except Exception as exc:
            raise ExternalServiceError() from exc

    async def _with_httpx(self, method: str, url: str, headers: dict,
                          body: str | None) -> HttpResult:
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=headers, content=body)
        return HttpResult(status=response.status_code, body=response.text)
