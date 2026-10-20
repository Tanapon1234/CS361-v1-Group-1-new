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
    # Fail a stuck connect after this long so the cause shows up in the logs, instead of the
    # request silently running into the Lambda timeout
    db_connect_timeout_seconds: int = Field(default=10, ge=1)
    # Secrets Manager secret (JSON with username / password, and host / port if present).
    # When set it replaces DB_USER / DB_PASSWORD and is re-read every few minutes, so a
    # rotated password keeps working (see docs/v2/backend-db-connection-decision.md).
    db_secret_arn: str = ""
    db_secret_cache_seconds: int = Field(default=300, ge=0)
    # Sign in with a short-lived IAM token instead of a password (DB_HOST and DB_USER are
    # used). Needed for Aurora Express Configuration, whose public endpoint refuses passwords.
    db_iam_auth: bool = False

    # Object storage (S3)
    aws_region: str = "ap-southeast-1"
    data_bucket_name: str = ""
    s3_presign_expires_seconds: int = Field(default=900, ge=60, le=3600)
    profile_image_max_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    profile_image_allowed_mime_types: list[str] = ["image/jpeg", "image/png", "image/webp"]
    cv_max_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    cv_allowed_mime_types: list[str] = ["application/pdf"]
    evidence_max_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    evidence_allowed_mime_types: list[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
    ]

    # Auth (docs/v2/permissions.md). With COGNITO_USER_POOL_ID set, the caller is the
    # lecturer linked to the Cognito ID token in `Authorization: Bearer <token>`.
    # COGNITO_JWKS_JSON (the pool's public keys) lets a Lambda without internet access
    # verify tokens; empty means fetch them from the pool.
    cognito_region: str = ""
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_jwks_json: str = ""
    # Until then, and in local tests / scripts, the X-Lecturer-Id and X-Dev-Roles headers
    # stand in for a token. Never accepted when ENVIRONMENT=prod.
    dev_auth_header_enabled: bool = True

    @model_validator(mode="after")
    def _require_real_secrets_outside_local(self) -> Self:
        if (
            self.environment is not Environment.LOCAL
            and not self.db_secret_arn
            and not self.db_iam_auth
            and self.db_password.get_secret_value() in _PLACEHOLDER_PASSWORDS
        ):
            raise ValueError(
                f"DB_PASSWORD or DB_SECRET_ARN must be set when ENVIRONMENT={self.environment}"
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PROD

    @property
    def cognito_issuer(self) -> str:
        region = self.cognito_region or self.aws_region
        return f"https://cognito-idp.{region}.amazonaws.com/{self.cognito_user_pool_id}"

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
