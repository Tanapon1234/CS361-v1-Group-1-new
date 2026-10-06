"""HTTP contract of the workload endpoints (services are strict mocks)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import ConflictError, PreconditionFailedError
from app.v2.dependencies import (
    get_entry_service,
    get_evidence_service,
    get_rubric_service,
    get_submission_service,
)
from app.v2.dtos.submission_dto import EntryResponse, entry_etag
from app.v2.models.enums import DataSource
from app.v2.services.entry_service import EntryService
from app.v2.services.evidence_service import EvidenceService
from app.v2.services.rubric_service import RubricService
from app.v2.services.submission_service import SubmissionService
from app.v2.storage.object_storage import PresignedDownload

V2 = "/api/v2"
ACTOR = str(uuid4())
AS_ACTOR = {"X-Lecturer-Id": ACTOR}


@pytest.fixture
def services(app: FastAPI) -> Iterator[dict[str, MagicMock]]:
    mocks = {
        "submission": create_autospec(SubmissionService, instance=True),
        "entry": create_autospec(EntryService, instance=True),
        "evidence": create_autospec(EvidenceService, instance=True),
        "rubric": create_autospec(RubricService, instance=True),
    }
    app.dependency_overrides[get_submission_service] = lambda: mocks["submission"]
    app.dependency_overrides[get_entry_service] = lambda: mocks["entry"]
    app.dependency_overrides[get_evidence_service] = lambda: mocks["evidence"]
    app.dependency_overrides[get_rubric_service] = lambda: mocks["rubric"]
    yield mocks


def make_entry() -> EntryResponse:
    now = datetime.now(UTC)
    return EntryResponse(
        id=uuid4(),
        submission_id=uuid4(),
        item_id=1,
        title=None,
        course_code="CS222",
        section_no=None,
        student_count=60,
        data_source=DataSource.MANUAL,
        synced_at=None,
        quantity=Decimal(3),
        participation_pct=Decimal(100),
        weight_applied=Decimal(1),
        credits=Decimal(3),
        score=Decimal(200),
        details={"hours": 45},
        note=None,
        sort_order=0,
        created_at=now,
        updated_at=now,
    )


def test_caller_header_is_required(client: TestClient, services: dict[str, MagicMock]) -> None:
    response = client.post(f"{V2}/submissions", json={"round_id": 1})

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    services["submission"].create_submission.assert_not_called()


def test_caller_header_is_passed_to_the_service(
    client: TestClient, services: dict[str, MagicMock]
) -> None:
    client.delete(f"{V2}/submissions/{uuid4()}", headers=AS_ACTOR)

    assert str(services["submission"].delete_submission.call_args.args[1]) == ACTOR


def test_entry_numbers_are_json_numbers_and_etag_is_sent(
    client: TestClient, services: dict[str, MagicMock]
) -> None:
    entry = make_entry()
    services["entry"].get_entry.return_value = entry

    response = client.get(f"{V2}/entries/{entry.id}")

    assert response.status_code == 200
    assert response.json()["score"] == 200.0
    assert response.headers["ETag"] == entry_etag(entry)


def test_patch_entry_forwards_if_match_and_maps_412(
    client: TestClient, services: dict[str, MagicMock]
) -> None:
    services["entry"].update_entry.side_effect = PreconditionFailedError("changed")

    response = client.patch(
        f"{V2}/entries/{uuid4()}", json={"note": "x"}, headers=AS_ACTOR | {"If-Match": '"v1"'}
    )

    assert response.status_code == 412
    assert services["entry"].update_entry.call_args.args[3] == '"v1"'


@pytest.mark.parametrize(
    "body",
    [
        {"item_id": 1, "quantity": 0},
        {"item_id": 1, "participation_pct": 120},
        {"item_id": 1, "score": 999},
    ],
    ids=["zero-quantity", "pct-over-100", "client-sent-score"],
)
def test_entry_body_is_validated(
    client: TestClient, services: dict[str, MagicMock], body: dict[str, Any]
) -> None:
    response = client.post(f"{V2}/submissions/{uuid4()}/entries", json=body, headers=AS_ACTOR)

    assert response.status_code == 422
    services["entry"].create_entry.assert_not_called()


def test_approval_role_cannot_be_sent(client: TestClient, services: dict[str, MagicMock]) -> None:
    response = client.post(
        f"{V2}/submissions/{uuid4()}/approvals",
        json={"decision": "approved", "role": "dept_chair"},
        headers=AS_ACTOR,
    )

    assert response.status_code == 422


def test_locked_submission_is_409(client: TestClient, services: dict[str, MagicMock]) -> None:
    services["entry"].delete_entry.side_effect = ConflictError("submitted")

    assert client.delete(f"{V2}/entries/{uuid4()}", headers=AS_ACTOR).status_code == 409


def test_pdf_is_not_implemented_yet(client: TestClient, services: dict[str, MagicMock]) -> None:
    services["submission"].get_pdf.side_effect = NotImplementedError

    assert client.get(f"{V2}/submissions/{uuid4()}/pdf").status_code == 501


def test_evidence_content_redirects_to_s3(
    client: TestClient, services: dict[str, MagicMock]
) -> None:
    services["evidence"].get_download.return_value = PresignedDownload(
        url="https://s3.example/file", expires_at=datetime.now(UTC) + timedelta(minutes=15)
    )

    response = client.get(f"{V2}/evidence/{uuid4()}/content", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://s3.example/file"


@pytest.mark.parametrize(
    "body",
    [
        {"label_th": "x", "unit": "term"},
        {
            "label_th": "x",
            "unit": "term",
            "weight_mode": "ranged",
            "weight_min": 2,
            "weight_max": 1,
        },
        {"label_th": "x", "unit": "term", "weight": 1, "field_schema": {"q": {"type": "enum"}}},
    ],
    ids=["fixed-without-weight", "min-above-max", "enum-without-values"],
)
def test_rubric_item_rules_are_validated(
    client: TestClient, services: dict[str, MagicMock], body: dict[str, Any]
) -> None:
    response = client.post(f"{V2}/rubric-sections/1/items", json=body)

    assert response.status_code == 422
    services["rubric"].create_item.assert_not_called()


def test_round_period_is_validated(client: TestClient) -> None:
    body = {
        "rubric_version_id": 1,
        "name_th": "รอบ",
        "period_start": "2025-06-30",
        "period_end": "2025-01-01",
        "salary_effective_on": "2025-10-01",
        "academic_year": 2568,
    }

    assert client.post(f"{V2}/rounds", json=body).status_code == 422
