import pytest
from pydantic import ValidationError

from atmosfera.boundary.schemas import ChangePasswordRequest, CityRequest, LoginRequest, SignupRequest


def message(exc: ValidationError) -> str:
    return exc.errors()[0]["msg"]


def test_signup_valid_normalizes_fields():
    req = SignupRequest(nome="  Ana ", email=" ANA@Exemplo.COM ", senha="12345678")
    assert req.nome == "Ana" and req.email == "ana@exemplo.com"


@pytest.mark.parametrize("data,fragment", [
    ({"nome": "A", "email": "a@b.co", "senha": "12345678"}, "Informe como podemos te chamar."),
    ({"nome": "Ana", "email": "sem-arroba", "senha": "12345678"}, "e-mail válido"),
    ({"nome": "Ana", "email": "a/b@c.co", "senha": "12345678"}, "e-mail válido"),
    ({"nome": "Ana", "email": "a@b.co", "senha": "1234567"}, "pelo menos 8"),
])
def test_signup_invalid(data, fragment):
    with pytest.raises(ValidationError) as err:
        SignupRequest(**data)
    assert fragment in message(err.value)


def test_login_and_password_change_and_city():
    assert LoginRequest(email=" A@B.co ", senha="x").email == "a@b.co"
    with pytest.raises(ValidationError):
        ChangePasswordRequest(senha_atual="x", nova_senha="curta")
    with pytest.raises(ValidationError):
        CityRequest(name="X", latitude=91, longitude=0)
    assert CityRequest(name="X", latitude=-21.7, longitude=-43.3).timezone == "UTC"
