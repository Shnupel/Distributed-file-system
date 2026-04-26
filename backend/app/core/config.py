from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    database_url: str = "DATABASE_URL"
    redis_url: str = "REDIS_URL"
    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
    access_secret: str = "CHANGE_ME_ACCESS_SECRET_MIN_32_CHARS"
    refresh_secret: str = "CHANGE_ME_REFRESH_SECRET_MIN_32_CHARS"
    access_token_expire_m: int = 15  # 15 minutes
    refresh_token_expire_m: int = 43200  # 30 days
    cookie_secure: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "strict"

    dfs_master_public_base_url: str = "http://127.0.0.1:8000"
    dfs_chunk_size_bytes: int = 4 * 1024 * 1024
    dfs_manifest_url_ttl_s: int = 300
    dfs_local_chunks_dir: str = "storage/chunks"
    dfs_local_node_name: str = "master-local"
    dfs_chunk_url_secret: str = "CHANGE_ME_DFS_CHUNK_URL_SECRET_MIN_32_CHARS"
    dfs_internal_token: str = "CHANGE_ME_DFS_INTERNAL_TOKEN_MIN_32_CHARS"
    dfs_replication_factor: int = 2
    dfs_write_quorum: int = 2
    dfs_storage_timeout_s: int = 10

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if value == "DATABASE_URL":
            raise ValueError("DATABASE_URL is not configured")

        if not value.startswith(("postgresql+asyncpg://", "postgres+asyncpg://")):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg")

        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        if value == "REDIS_URL":
            raise ValueError("REDIS_URL is not configured")

        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must use redis:// or rediss://")

        return value

    @field_validator("access_secret", "refresh_secret")
    @classmethod
    def validate_secret_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT secret must be at least 32 characters long")
        return value

    @field_validator("dfs_chunk_url_secret", "dfs_internal_token")
    @classmethod
    def validate_dfs_secret_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("DFS secret must be at least 32 characters long")
        return value

    @field_validator(
        "dfs_chunk_size_bytes",
        "dfs_manifest_url_ttl_s",
        "dfs_replication_factor",
        "dfs_write_quorum",
        "dfs_storage_timeout_s",
    )
    @classmethod
    def validate_positive_dfs_number(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("DFS numeric settings must be positive")
        return value

    @field_validator("dfs_master_public_base_url")
    @classmethod
    def validate_master_public_base_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("DFS master public base url must start with http:// or https://")
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_dfs_quorum_relation(self):
        if self.dfs_write_quorum > self.dfs_replication_factor:
            raise ValueError("DFS_WRITE_QUORUM must be less than or equal to DFS_REPLICATION_FACTOR")
        return self

    class Config:
        env_file = ".env.master"
        frozen = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
