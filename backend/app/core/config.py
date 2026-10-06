"""Application settings, read from environment variables (and `.env` in local dev)."""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Self

from fastapi import Depends
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

_PLACEHOLDER_PASSWORDS = {"", "change-me"}


class Environment(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    DEMO = "demo"
    PROD = "prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "CS361 Faculty Output API"
    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"
    cors_allow_origins: list[str] = []

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cs361v2"
    db_user: str = "postgres"
    db_password: SecretStr = SecretStr("change-me")
    db_sslmode: str = "prefer"
    db_echo: bool = False
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    db_pool_timeout_seconds: int = Field(default=30, ge=1)
    db_pool_recycle_seconds: int = Field(default=1800, ge=-1)

    # Object storage (S3)
    aws_region: str = "ap-southeast-1"
    data_bucket_name: str = ""
    s3_presign_expires_seconds: int = Field(default=900, ge=60, le=3600)
    profile_image_max_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    cv_max_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    evidence_max_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    evidence_allowed_mime_types: list[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
    ]

    # Auth. Cognito is not wired yet: until it is, the caller is taken from the
    # `X-Lecturer-Id` header (see app/v2/dependencies.py). Always off in prod.
    dev_auth_header_enabled: bool = True

    @model_validator(mode="after")
    def _require_real_secrets_outside_local(self) -> Self:
        if (
            self.environment is not Environment.LOCAL
            and self.db_password.get_secret_value() in _PLACEHOLDER_PASSWORDS
        ):
            raise ValueError(f"DB_PASSWORD must be set when ENVIRONMENT={self.environment}")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PROD

    @property
    def allows_dev_auth_header(self) -> bool:
        return self.dev_auth_header_enabled and not self.is_production

    @property
    def database_url(self) -> URL:
        # URL.create escapes special characters in credentials; never build DSNs with f-strings.
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"sslmode": self.db_sslmode},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
