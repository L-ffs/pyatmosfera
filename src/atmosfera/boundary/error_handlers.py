"""Converte exceções em respostas JSON no formato {"error": "..."}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..support.errors import AppError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse({"error": exc.message}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        field = str(first.get("loc", ["", ""])[-1]) if first.get("loc") else ""
        message = str(first.get("msg", ""))
        if first.get("type") == "value_error":
            message = message.removeprefix("Value error, ")
        else:
            message = "Dados inválidos."
        return JSONResponse({"error": message, "field": field}, status_code=400)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        print(f"Erro inesperado: {exc!r}")
        return JSONResponse({"error": AppError.message}, status_code=500)
