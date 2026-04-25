from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class StorageSettings(BaseSettings):
    storage_node_name: str = "storage-node"
    storage_chunks_dir: str = "storage-node/chunks"

    dfs_chunk_url_secret: str = "CHANGE_ME_DFS_CHUNK_URL_SECRET_MIN_32_CHARS"
    dfs_internal_token: str = "CHANGE_ME_DFS_INTERNAL_TOKEN_MIN_32_CHARS"

    @field_validator("dfs_chunk_url_secret", "dfs_internal_token")
    @classmethod
    def validate_secret_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("DFS secrets must be at least 32 characters long")
        return value

    class Config:
        env_file = ".env"
        frozen = True


@lru_cache
def get_storage_settings() -> StorageSettings:
    return StorageSettings()
