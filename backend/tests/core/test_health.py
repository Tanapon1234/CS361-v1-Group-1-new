from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError


def test_liveness(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_when_database_is_up(client: TestClient, session: MagicMock) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    session.execute.assert_called_once()


def test_readiness_when_database_is_down(client: TestClient, session: MagicMock) -> None:
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("refused"))

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unreachable"
