"""Vocabulário de erros do sistema.

O controle lança estas exceções; a fronteira (error_handlers) as converte em
respostas HTTP. Assim nenhuma regra de negócio precisa conhecer códigos HTTP.
"""


class AppError(Exception):
    status_code = 500
    message = "Erro interno. Tente novamente."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class InvalidCredentials(AppError):
    status_code = 401
    message = "E-mail ou senha incorretos."


class Unauthorized(AppError):
    status_code = 401
    message = "Sessão inválida ou expirada."


class EmailAlreadyExists(AppError):
    status_code = 409
    message = "E-mail já cadastrado."


class WrongCurrentPassword(AppError):
    status_code = 400
    message = "A senha atual está incorreta."


class CityAlreadyFavorited(AppError):
    status_code = 409
    message = "Cidade já está nos favoritos."


class FavoriteNotFound(AppError):
    status_code = 404
    message = "Cidade não encontrada nos favoritos."


class ExternalServiceError(AppError):
    status_code = 502
    message = "Serviço externo indisponível. Tente novamente."
