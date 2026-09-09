from pathlib import Path
from typing import Any

from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 465
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Contacts App"

    REDIS_DOMAIN: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    CLD_NAME: str
    CLD_API_KEY: int
    CLD_API_SECRET: str

    @property
    def DB_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: Any):
        if v not in ["HS256", "HS512"]:
            raise ValueError("algorithm must be HS256 or HS512")
        return v

    @field_validator("REDIS_PASSWORD", mode="before")
    @classmethod
    def empty_redis_password(cls, v: Any):
        if v == "":
            return None
        return v

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = Settings()
