from app.crud import DFSCRUD
from app.crud import UserCRUD


async def get_dfs_crud():
    return DFSCRUD()


async def get_user_crud():
    return UserCRUD()