"""Database credentials from AWS Secrets Manager (DB_SECRET_ARN), cached for a few minutes.

Read on every new connection, so a rotated password is picked up within the cache time
without restarting the app.
"""

import json
import time
from threading import Lock
from typing import Any

import boto3


class SecretCredentials:
    def __init__(self, secret_arn: str, region: str, ttl_seconds: int, client: Any = None) -> None:
        self.secret_arn = secret_arn
        self.ttl_seconds = ttl_seconds
        self._client = client or boto3.client("secretsmanager", region_name=region)
        self._value: dict[str, Any] | None = None
        self._loaded_at = 0.0
        self._lock = Lock()

    def connect_params(self) -> dict[str, Any]:
        """psycopg connect() keyword arguments taken from the secret."""
        secret = self._get()
        params: dict[str, Any] = {"user": secret["username"], "password": secret["password"]}
        if secret.get("host"):
            params["host"] = secret["host"]
        if secret.get("port"):
            params["port"] = int(secret["port"])
        return params

    def _get(self) -> dict[str, Any]:
        with self._lock:
            expired = time.monotonic() - self._loaded_at >= self.ttl_seconds
            if self._value is None or expired:
                response = self._client.get_secret_value(SecretId=self.secret_arn)
                self._value = json.loads(response["SecretString"])
                self._loaded_at = time.monotonic()
            return self._value


class IamTokenCredentials:
    """Short-lived RDS IAM auth token used as the password (DB_IAM_AUTH=true).

    A token is only checked when a connection opens and lasts 15 minutes, so one is cached
    for a shorter time than that.
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        region: str,
        ttl_seconds: int = 600,
        client: Any = None,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.ttl_seconds = ttl_seconds
        self._client = client or boto3.client("rds", region_name=region)
        self._token: str | None = None
        self._loaded_at = 0.0
        self._lock = Lock()

    def connect_params(self) -> dict[str, Any]:
        with self._lock:
            expired = time.monotonic() - self._loaded_at >= self.ttl_seconds
            if self._token is None or expired:
                self._token = self._client.generate_db_auth_token(
                    DBHostname=self.host, Port=self.port, DBUsername=self.user
                )
                self._loaded_at = time.monotonic()
            return {"user": self.user, "password": self._token}
