"""Every /api/v2 endpoint against docs/v2/permissions.md, with the real caller check.

The cases are generated from the OpenAPI document and ROUTE_RULES, so a new endpoint is
covered (or fails, if it has no rule) without editing this file.
"""

import re
from collections.abc import Iterator
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.main import create_app
from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.dependencies import get_member_position_dao
from app.v2.permissions import ROUTE_RULES, Rule

APP = create_app()
ENDPOINTS = sorted(
    (method.upper(), path)
    for path, operations in APP.openapi()["paths"].items()
    if path.startswith("/api/v2/")
    for method in operations
)
CALLER = str(uuid4())
SOMEONE_ELSE = str(uuid4())


def rule(method: str, path: str) -> Rule:
    return ROUTE_RULES[(method, path.removeprefix("/api/v2"))]


def url(path: str, lecturer_id: str = SOMEONE_ELSE) -> str:
    """Fill path parameters with well-formed values (`lecturer_id` as given)."""

    def value(match: re.Match[str]) -> str:
        name = match.group(1)
        if name == "lecturer_id":
            return lecturer_id
        if name in {"submission_id", "entry_id", "evidence_id", "position_id"}:
            return str(uuid4())
        return "1"

    return re.sub(r"\{(\w+)\}", value, path)


def call(client: TestClient, method: str, path: str, headers: dict[str, str], **kw: str) -> int:
    body = {} if method in {"POST", "PUT", "PATCH"} else None
    return client.request(method, url(path, **kw), headers=headers, json=body).status_code


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    positions = create_autospec(MemberPositionDAO, instance=True)
    positions.list_active.return_value = []
    APP.dependency_overrides[get_session] = lambda: MagicMock(spec=Session)
    APP.dependency_overrides[get_member_position_dao] = lambda: positions
    # Past the check, services hit a mock session; any status but 401 / 403 means "let in"
    with TestClient(APP, raise_server_exceptions=False) as client:
        yield client
    APP.dependency_overrides.clear()


def test_every_endpoint_has_a_rule_and_no_rule_is_stale() -> None:
    documented = {(method, path.removeprefix("/api/v2")) for method, path in ENDPOINTS}

    assert sorted(documented - ROUTE_RULES.keys()) == []
    assert sorted(ROUTE_RULES.keys() - documented) == []


@pytest.mark.parametrize(("method", "path"), ENDPOINTS, ids=" ".join)
def test_no_sign_in_is_401(client: TestClient, method: str, path: str) -> None:
    assert call(client, method, path, headers={}) == 401


LECTURER_ONLY = {"X-Lecturer-Id": CALLER}


@pytest.mark.parametrize(
    ("method", "path"),
    [(m, p) for m, p in ENDPOINTS if not rule(m, p).anyone],
    ids=" ".join,
)
def test_plain_lecturer_is_403_on_someone_elses_or_staff_endpoints(
    client: TestClient, method: str, path: str
) -> None:
    assert call(client, method, path, headers=LECTURER_ONLY) == 403


@pytest.mark.parametrize(
    ("method", "path"),
    [(m, p) for m, p in ENDPOINTS if rule(m, p).self_param == "lecturer_id"],
    ids=" ".join,
)
def test_lecturer_is_let_in_on_their_own_record(client: TestClient, method: str, path: str) -> None:
    assert call(client, method, path, headers=LECTURER_ONLY, lecturer_id=CALLER) not in {401, 403}


@pytest.mark.parametrize(
    ("method", "path"),
    [(m, p) for m, p in ENDPOINTS if rule(m, p).anyone],
    ids=" ".join,
)
def test_any_signed_in_lecturer_is_let_in(client: TestClient, method: str, path: str) -> None:
    # 403 may still come from a data check in the service; the route itself must let them in
    status = call(client, method, path, headers=LECTURER_ONLY)
    assert status != 401


@pytest.mark.parametrize("role", ["staff", "admin"])
@pytest.mark.parametrize(
    ("method", "path"),
    [(m, p) for m, p in ENDPOINTS if not rule(m, p).anyone],
    ids=" ".join,
)
def test_staff_and_admin_pass_the_route_check(
    client: TestClient, method: str, path: str, role: str
) -> None:
    status = call(client, method, path, headers=LECTURER_ONLY | {"X-Dev-Roles": role})
    assert status not in {401, 403}
