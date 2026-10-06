import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error_handlers import register_exception_handlers
from app.core.exceptions import AppError, BadRequestError, ConflictError, NotFoundError


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise/{kind}")
    def raise_error(kind: str) -> None:
        errors: dict[str, Exception] = {
            "bad-request": BadRequestError("Only PDF files are allowed"),
            "not-found": NotFoundError("Lecturer not found"),
            "conflict": ConflictError("Email already used"),
            "not-implemented": NotImplementedError(),
        }
        raise errors[kind]

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict[str, int]:
        return {"id": item_id}

    return TestClient(app)


@pytest.mark.parametrize(
    ("kind", "error_cls"),
    [("bad-request", BadRequestError), ("not-found", NotFoundError), ("conflict", ConflictError)],
)
def test_app_errors_become_problem_details(
    client: TestClient, kind: str, error_cls: type[AppError]
) -> None:
    response = client.get(f"/raise/{kind}")

    assert response.status_code == error_cls.status_code
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == f"urn:cs361:problem:{error_cls.problem_type}"
    assert body["title"] == error_cls.title
    assert body["status"] == error_cls.status_code
    assert body["instance"] == f"/raise/{kind}"


def test_not_implemented_is_501(client: TestClient) -> None:
    response = client.get("/raise/not-implemented")

    assert response.status_code == 501
    assert response.json()["type"] == "urn:cs361:problem:not-implemented"


def test_validation_error_lists_each_bad_field(client: TestClient) -> None:
    response = client.get("/items/abc")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["errors"] == [
        {
            "field": "path.item_id",
            "message": "Input should be a valid integer, unable to parse string as an integer",
        }
    ]


def test_unknown_route_is_404_problem(client: TestClient) -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["type"] == "urn:cs361:problem:not-found"
