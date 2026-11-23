"""Casos de uso de conta: criar conta (RF1), login (RF2) e trocar senha (RF7)."""
from ..entity.user import User
from ..external.user_repository import UserRepository
from ..support.errors import EmailAlreadyExists, InvalidCredentials, Unauthorized, WrongCurrentPassword
from ..support.password_hasher import PasswordHasher
from .session_service import SessionService


class AuthService:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, sessions: SessionService):
        self._users = users
        self._hasher = hasher
        self._sessions = sessions

    async def signup(self, name: str, email: str, password: str) -> User:
        user = User(email=email, name=name, password_hash=await self._hasher.hash(password))
        if not await self._users.add(user):
            raise EmailAlreadyExists()
        return user

    async def login(self, email: str, password: str) -> tuple[User, str]:
        user = await self._users.find_by_email(email)
        if user is None:
            # gasta o mesmo tempo de uma verificação real para não revelar quais e-mails existem
            await self._hasher.verify(password, await self._hasher.hash("atmosfera"))
            raise InvalidCredentials()
        if not await self._hasher.verify(password, user.password_hash):
            raise InvalidCredentials()
        return user, self._sessions.issue(user.email)

    async def get_user(self, email: str) -> User:
        user = await self._users.find_by_email(email)
        if user is None:
            raise Unauthorized()
        return user

    async def change_password(self, email: str, current: str, new: str) -> None:
        user = await self.get_user(email)
        if not await self._hasher.verify(current, user.password_hash):
            raise WrongCurrentPassword()
        user.password_hash = await self._hasher.hash(new)
        await self._users.save_password_hash(user)
