"""Fronteira com o Google Firestore (API REST, sem conta de serviço).

Conhece o formato dos documentos do Firestore ("stringValue", "mapValue"...) e
converte de/para dicionários comuns. O acesso depende das regras do banco.
"""
from typing import Any
from urllib.parse import quote

from ..support.errors import ExternalServiceError
from ..support.http_client import HttpClient
from ..support.settings import Settings


class FirestoreClient:
    def __init__(self, settings: Settings, http: HttpClient):
        self._http = http
        self._api_key = settings.firestore_api_key
        self._base = (
            "https://firestore.googleapis.com/v1/projects/"
            f"{settings.firestore_project_id}/databases/(default)/documents/"
            f"{settings.firestore_collection}"
        )

    async def get_document(self, doc_id: str) -> dict | None:
        result = await self._http.request("GET", self._doc_url(doc_id), params=self._auth())
        if result.status == 404:
            return None
        self._expect_ok(result.status)
        return self._decode_fields(result.json())

    async def create_document(self, doc_id: str, fields: dict) -> bool:
        """Cria o documento. Retorna False se já existir um com o mesmo id."""
        params = {"documentId": doc_id, **self._auth()}
        result = await self._http.request(
            "POST", self._base, params=params, json=self._encode_fields(fields))
        if result.status == 409:
            return False
        self._expect_ok(result.status)
        return True

    async def update_document(self, doc_id: str, fields: dict) -> None:
        """Atualiza só os campos informados (merge parcial)."""
        params = [("updateMask.fieldPaths", name) for name in fields]
        params += list(self._auth().items())
        result = await self._http.request(
            "PATCH", self._doc_url(doc_id), params=params, json=self._encode_fields(fields))
        self._expect_ok(result.status)

    # --- internos ---------------------------------------------------------
    def _doc_url(self, doc_id: str) -> str:
        return f"{self._base}/{quote(doc_id, safe='')}"

    def _auth(self) -> dict:
        return {"key": self._api_key} if self._api_key else {}

    @staticmethod
    def _expect_ok(status: int) -> None:
        if status != 200:
            raise ExternalServiceError()

    @classmethod
    def _encode_fields(cls, plain: dict) -> dict:
        return {"fields": {k: cls._encode_value(v) for k, v in plain.items()}}

    @classmethod
    def _encode_value(cls, value: Any) -> dict:
        if value is None:
            return {"nullValue": None}
        if isinstance(value, bool):
            return {"booleanValue": value}
        if isinstance(value, int):
            return {"integerValue": str(value)}
        if isinstance(value, float):
            return {"doubleValue": value}
        if isinstance(value, str):
            return {"stringValue": value}
        if isinstance(value, (list, tuple)):
            return {"arrayValue": {"values": [cls._encode_value(v) for v in value]}}
        if isinstance(value, dict):
            return {"mapValue": {"fields": {k: cls._encode_value(v) for k, v in value.items()}}}
        raise TypeError(f"Tipo não suportado: {type(value).__name__}")

    @classmethod
    def _decode_fields(cls, document: dict) -> dict:
        return {k: cls._decode_value(v) for k, v in document.get("fields", {}).items()}

    @classmethod
    def _decode_value(cls, value: dict) -> Any:
        if "stringValue" in value:
            return value["stringValue"]
        if "integerValue" in value:
            return int(value["integerValue"])
        if "doubleValue" in value:
            return float(value["doubleValue"])
        if "booleanValue" in value:
            return bool(value["booleanValue"])
        if "arrayValue" in value:
            return [cls._decode_value(v) for v in value["arrayValue"].get("values", [])]
        if "mapValue" in value:
            return cls._decode_fields(value["mapValue"])
        return None
