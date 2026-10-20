"""The caller comes from a Cognito ID token, or from the dev headers outside prod."""

import json
import time
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.cognito import CognitoTokenVerifier
from app.core.config import Environment, Settings, get_settings
from app.core.error_handlers import register_exception_handlers
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dependencies import CurrentActorDep, get_lecturer_dao, get_token_verifier
from app.v2.models.lecturer import Lecturer

ISSUER = "https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_test"
CLIENT_ID = "web-client"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
JWKS = json.dumps(
    {"keys": [jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key(), as_dict=True) | {"kid": "k1"}]}
)
LECTURER = Lecturer(lecturer_id=uuid4(), name_th="สมชาย", email="s@x.ac.th", cognito_sub="sub-1")


def token(**overrides: Any) -> str:
    now = int(time.time())
    claims = {
        "sub": "sub-1",
        "aud": CLIENT_ID,
        "iss": ISSUER,
        "iat": now,
        "exp": now + 600,
        "token_use": "id",
        "email": "s@x.ac.th",
        "cognito:groups": ["staff", "not-a-role"],
    } | overrides
    return jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": "k1"})


def bearer(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


@pytest.fixture
def lecturer_dao() -> MagicMock:
    dao = create_autospec(LecturerDAO, instance=True)
    dao.get_by_cognito_sub.side_effect = lambda sub: LECTURER if sub == "sub-1" else None
    return dao


def make_client(lecturer_dao: MagicMock, **settings: Any) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/who")
    def who(actor: CurrentActorDep) -> dict[str, Any]:
        return {"lecturer_id": actor.lecturer_id, "roles": sorted(actor.roles)}

    values = {"_env_file": None, "db_password": "x"} | settings
    app.dependency_overrides[get_settings] = lambda: Settings(**values)
    app.dependency_overrides[get_lecturer_dao] = lambda: lecturer_dao
    app.dependency_overrides[get_token_verifier] = lambda: CognitoTokenVerifier(
        issuer=ISSUER, client_id=CLIENT_ID, jwks_json=JWKS
    )
    return TestClient(app)


@pytest.fixture
def client(lecturer_dao: MagicMock) -> Iterator[TestClient]:
    yield make_client(lecturer_dao)


def test_valid_id_token_gives_the_linked_lecturer_and_its_groups(client: TestClient) -> None:
    response = client.get("/who", headers=bearer(token()))

    assert response.status_code == 200
    assert response.json() == {
        "lecturer_id": str(LECTURER.lecturer_id),
        "roles": ["lecturer", "staff"],
    }


@pytest.mark.parametrize(
    "bad",
    [
        {"exp": int(time.time()) - 10},
        {"aud": "other-client"},
        {"iss": "https://cognito-idp.ap-southeast-1.amazonaws.com/other"},
        {"token_use": "access"},
    ],
    ids=["expired", "wrong-client", "wrong-pool", "access-token"],
)
def test_invalid_tokens_are_401(client: TestClient, bad: dict) -> None:
    assert client.get("/who", headers=bearer(token(**bad))).status_code == 401


def test_token_signed_by_another_key_is_401(client: TestClient) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode(
        jwt.decode(token(), options={"verify_signature": False}),
        other,
        algorithm="RS256",
        headers={"kid": "k1"},
    )
    assert client.get("/who", headers=bearer(forged)).status_code == 401


def test_unlinked_account_is_403(client: TestClient) -> None:
    assert client.get("/who", headers=bearer(token(sub="sub-unknown"))).status_code == 403


def test_deactivated_lecturer_is_403(client: TestClient) -> None:
    LECTURER.is_active = False
    try:
        assert client.get("/who", headers=bearer(token())).status_code == 403
    finally:
        LECTURER.is_active = True


def test_no_identity_is_401(client: TestClient) -> None:
    response = client.get("/who")

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")


def test_dev_headers_outside_prod(client: TestClient) -> None:
    lecturer_id = str(uuid4())

    as_lecturer = client.get("/who", headers={"X-Lecturer-Id": lecturer_id})
    as_script = client.get("/who", headers={"X-Dev-Roles": "admin, staff"})

    assert as_lecturer.json() == {"lecturer_id": lecturer_id, "roles": ["lecturer"]}
    assert as_script.json() == {"lecturer_id": None, "roles": ["admin", "staff"]}


def test_dev_headers_are_ignored_in_prod(lecturer_dao: MagicMock) -> None:
    prod = make_client(lecturer_dao, environment=Environment.PROD)

    response = prod.get("/who", headers={"X-Lecturer-Id": str(uuid4()), "X-Dev-Roles": "admin"})

    assert response.status_code == 401


def test_bearer_without_cognito_configured_is_401(lecturer_dao: MagicMock) -> None:
    client = make_client(lecturer_dao)
    client.app.dependency_overrides[get_token_verifier] = lambda: None

    assert client.get("/who", headers=bearer(token())).status_code == 401
