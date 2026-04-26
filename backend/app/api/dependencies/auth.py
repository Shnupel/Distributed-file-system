from collections.abc import Callable

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import API_V1_PREFIX, ROLE_ADMIN, Settings, get_settings
from app.db import db_helper
from app.exceptions import PermissionDenied
from app.models import User
from app.services import AuthService, UserService
from shared import INTERNAL_TOKEN_HEADER, is_internal_token_valid

from .providers import get_auth_service, get_user_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/login", auto_error=False)


def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> int:
    return service.get_user_id_from_token(token)


async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.get_by_id(session, current_user_id)


def require_roles(*roles: str) -> Callable[[User], User]:
    allowed_roles = {role.lower() for role in roles}

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role = (current_user.role or "").lower()
        if user_role not in allowed_roles:
            raise PermissionDenied()
        return current_user

    return dependency


def require_admin(current_user: User = Depends(require_roles(ROLE_ADMIN))) -> User:
    return current_user


def require_internal_token(
    internal_token: str | None = Header(default=None, alias=INTERNAL_TOKEN_HEADER),
    settings: Settings = Depends(get_settings),
) -> None:
    if not is_internal_token_valid(internal_token, settings.dfs_internal_token):
        raise PermissionDenied("Invalid internal token")


async def require_admin_or_internal(
    token: str | None = Depends(oauth2_scheme_optional),
    internal_token: str | None = Header(default=None, alias=INTERNAL_TOKEN_HEADER),
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> User | None:
    if is_internal_token_valid(internal_token, settings.dfs_internal_token):
        return None

    if not token:
        raise PermissionDenied()

    user_id = auth_service.get_user_id_from_token(token)
    user = await user_service.get_by_id(session, user_id)
    if (user.role or "").lower() != ROLE_ADMIN:
        raise PermissionDenied()
    return user
