from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class StorageSettings(BaseSettings):
    storage_node_name: str = "storage-node"
    storage_public_base_url: str = "http://127.0.0.1:8010"
    storage_internal_base_url: str | None = None
    storage_chunks_dir: str = "storage-node/chunks"
    dfs_master_base_url: str = "http://127.0.0.1:8000"
    dfs_heartbeat_interval_s: int = 15

    dfs_chunk_url_secret: str = "CHANGE_ME_DFS_CHUNK_URL_SECRET_MIN_32_CHARS"
    dfs_internal_token: str = "CHANGE_ME_DFS_INTERNAL_TOKEN_MIN_32_CHARS"

    @field_validator("dfs_chunk_url_secret", "dfs_internal_token")
    @classmethod
    def validate_secret_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("DFS secrets must be at least 32 characters long")
        return value

    @field_validator("dfs_master_base_url")
    @classmethod
    def validate_master_base_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("DFS master base url must start with http:// or https://")
        return value.rstrip("/")

    @field_validator("storage_public_base_url")
    @classmethod
    def validate_storage_public_base_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("Storage public base url must start with http:// or https://")
        return value.rstrip("/")

    @field_validator("storage_internal_base_url")
    @classmethod
    def validate_storage_internal_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith(("http://", "https://")):
            raise ValueError("Storage internal base url must start with http:// or https://")
        return value.rstrip("/")

    @field_validator("dfs_heartbeat_interval_s")
    @classmethod
    def validate_heartbeat_interval(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Heartbeat interval must be positive")
        return value

    class Config:
        env_file = ".env"
        frozen = True


@lru_cache
def get_storage_settings() -> StorageSettings:
    return StorageSettings()
