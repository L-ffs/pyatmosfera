"""Modelos de requisição. Conferem só o FORMATO dos dados; as regras de negócio ficam no controle."""
import re

from pydantic import BaseModel, Field, field_validator

_EMAIL = re.compile(r"^[^\s@/]+@[^\s@/]+\.[^\s@/]{2,}$")
MIN_PASSWORD = 8
MAX_PASSWORD = 128


def _check_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 254 or not _EMAIL.match(value):
        raise ValueError("Informe um e-mail válido.")
    return value


def _check_new_password(value: str) -> str:
    if len(value) < MIN_PASSWORD:
        raise ValueError(f"Use pelo menos {MIN_PASSWORD} caracteres.")
    if len(value) > MAX_PASSWORD:
        raise ValueError(f"Use no máximo {MAX_PASSWORD} caracteres.")
    return value


class SignupRequest(BaseModel):
    nome: str
    email: str
    senha: str

    @field_validator("nome")
    @classmethod
    def _nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Informe como podemos te chamar.")
        if len(v) > 80:
            raise ValueError("O nome deve ter no máximo 80 caracteres.")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _check_email(v)

    @field_validator("senha")
    @classmethod
    def _senha(cls, v: str) -> str:
        return _check_new_password(v)


class LoginRequest(BaseModel):
    email: str
    senha: str = Field(max_length=MAX_PASSWORD)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class ChangePasswordRequest(BaseModel):
    senha_atual: str = Field(max_length=MAX_PASSWORD)
    nova_senha: str

    @field_validator("nova_senha")
    @classmethod
    def _nova(cls, v: str) -> str:
        return _check_new_password(v)


class CityRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = Field(default="UTC", max_length=64)
    state: str = Field(default="", max_length=120)
    country: str = Field(default="", max_length=120)
