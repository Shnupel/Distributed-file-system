from fastapi import Depends

from app.core import Settings, get_settings
from app.crud import DFSCRUD, UserCRUD
from app.services import AuthService, DFSService, UserService
from .repositories import get_dfs_crud, get_user_crud


async def get_user_service(user_crud: UserCRUD = Depends(get_user_crud)):
    return UserService(user_crud)


async def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    settings: Settings = Depends(get_settings),
):
    return AuthService(user_service, settings)


async def get_dfs_service(
    dfs_crud: DFSCRUD = Depends(get_dfs_crud),
    settings: Settings = Depends(get_settings),
):
    return DFSService(dfs_crud, settings)