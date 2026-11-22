"""Fronteira de conta: RF1 (criar conta), RF2 (login), RF7 (trocar senha) e sessão."""
from fastapi import APIRouter, Depends, Response

from ..control.auth_service import AuthService
from ..support.settings import Settings
from .dependencies import SESSION_COOKIE, get_auth_service, get_current_email, get_settings
from .schemas import ChangePasswordRequest, LoginRequest, SignupRequest


class AuthRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api", tags=["conta"])
        self.router.add_api_route("/auth/signup", self.signup, methods=["POST"], status_code=201)
        self.router.add_api_route("/auth/login", self.login, methods=["POST"])
        self.router.add_api_route("/auth/logout", self.logout, methods=["POST"])
        self.router.add_api_route("/auth/password", self.change_password, methods=["POST"])
        self.router.add_api_route("/me", self.me, methods=["GET"])

    async def signup(self, body: SignupRequest, auth: AuthService = Depends(get_auth_service)):
        await auth.signup(body.nome, body.email, body.senha)
        return {"message": "Conta criada com sucesso."}

    async def login(self, body: LoginRequest, response: Response,
                    auth: AuthService = Depends(get_auth_service),
                    settings: Settings = Depends(get_settings)):
        user, token = await auth.login(body.email, body.senha)
        response.set_cookie(
            SESSION_COOKIE, token, max_age=settings.session_ttl_seconds, path="/",
            httponly=True, secure=settings.cookie_secure, samesite="lax")
        return {"name": user.name, "email": user.email}

    async def logout(self, response: Response):
        response.delete_cookie(SESSION_COOKIE, path="/")
        return {"message": "Sessão encerrada."}

    async def change_password(self, body: ChangePasswordRequest,
                              email: str = Depends(get_current_email),
                              auth: AuthService = Depends(get_auth_service)):
        await auth.change_password(email, body.senha_atual, body.nova_senha)
        return {"message": "Senha alterada com sucesso."}

    async def me(self, email: str = Depends(get_current_email),
                 auth: AuthService = Depends(get_auth_service)):
        user = await auth.get_user(email)
        return {"name": user.name, "email": user.email}
