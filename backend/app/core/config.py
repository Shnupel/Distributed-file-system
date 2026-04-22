from functools import lru_cache
from typing import Literal

from pydantic import field_validator
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

    class Config:
        env_file = ".env"
        frozen = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
