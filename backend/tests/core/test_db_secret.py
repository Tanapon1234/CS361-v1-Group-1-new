"""DB_SECRET_ARN: credentials come from Secrets Manager and are re-read after the cache time."""

import json
from unittest.mock import MagicMock

import pytest

from app.core import database
from app.core.config import Settings
from app.core.db_secret import SecretCredentials


def secrets_client(*secrets: dict) -> MagicMock:
    client = MagicMock()
    client.get_secret_value.side_effect = [{"SecretString": json.dumps(s)} for s in secrets]
    return client


def test_connect_params_use_the_secret() -> None:
    client = secrets_client(
        {"username": "app", "password": "p1", "host": "db.internal", "port": "5432"}
    )
    credentials = SecretCredentials("arn:secret", "ap-southeast-1", 300, client=client)

    assert credentials.connect_params() == {
        "user": "app",
        "password": "p1",
        "host": "db.internal",
        "port": 5432,
    }


def test_the_secret_is_cached() -> None:
    client = secrets_client({"username": "app", "password": "p1"})
    credentials = SecretCredentials("arn:secret", "ap-southeast-1", 300, client=client)

    credentials.connect_params()
    credentials.connect_params()

    assert client.get_secret_value.call_count == 1


def test_a_rotated_password_is_picked_up_after_the_cache_time() -> None:
    client = secrets_client(
        {"username": "app", "password": "old"}, {"username": "app", "password": "new"}
    )
    credentials = SecretCredentials("arn:secret", "ap-southeast-1", 0, client=client)

    assert credentials.connect_params()["password"] == "old"
    assert credentials.connect_params()["password"] == "new"


def test_engine_reads_the_secret_on_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(_env_file=None, db_secret_arn="arn:secret")  # type: ignore[call-arg]
    monkeypatch.setattr(database, "get_settings", lambda: settings)
    fake = MagicMock()
    fake.connect_params.return_value = {"user": "app", "password": "from-secret"}
    monkeypatch.setattr(database, "SecretCredentials", lambda *args: fake)
    database.get_engine.cache_clear()
    try:
        engine = database.get_engine()
        cparams: dict = {}
        engine.dialect.dispatch.do_connect(engine.dialect, None, [], cparams)
    finally:
        database.get_engine.cache_clear()

    assert cparams == {"user": "app", "password": "from-secret"}
