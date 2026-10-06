import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Environment, Settings
from app.main import create_app


def make_settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


def test_database_url_escapes_special_characters_in_password() -> None:
    settings = make_settings(db_password="p@ss:w/rd", db_host="db.example", db_name="cs361")

    url = settings.database_url

    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss:w/rd"
    assert "p%40ss%3Aw%2Frd" in url.render_as_string(hide_password=False)
    assert url.query == {"sslmode": "prefer"}


def test_placeholder_password_is_allowed_locally() -> None:
    assert make_settings(environment=Environment.LOCAL).db_password.get_secret_value()


@pytest.mark.parametrize("environment", [Environment.DEV, Environment.DEMO, Environment.PROD])
def test_placeholder_password_is_rejected_outside_local(environment: Environment) -> None:
    with pytest.raises(ValidationError, match="DB_PASSWORD must be set"):
        make_settings(environment=environment, db_password="change-me")


def test_docs_are_disabled_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    prod = make_settings(environment=Environment.PROD, db_password="real-secret")
    monkeypatch.setattr("app.main.get_settings", lambda: prod)

    client = TestClient(create_app())

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
