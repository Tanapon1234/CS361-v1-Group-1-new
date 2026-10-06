"""End-to-end workload flow over HTTP against a real PostgreSQL (migrations 002-004).

Skipped unless TEST_DATABASE_URL points at a database that may be wiped, e.g.

    createdb cs361_test
    TEST_DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/cs361_test uv run pytest

Never point it at a dev or prod database: every run drops and recreates the public schema.
"""

import os
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlmodel import Session, create_engine

from app.core.database import get_session
from app.v2.dependencies import get_object_storage
from app.v2.storage.object_storage import (
    ObjectStorage,
    PresignedDownload,
    PresignedUpload,
    StoredObject,
)

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
MIGRATIONS = Path(__file__).parents[4] / "database" / "migrations"

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is not set")


class FakeStorage(ObjectStorage):
    """In-memory S3: `uploaded` holds the keys a client 'uploaded'."""

    def __init__(self) -> None:
        self.uploaded: dict[str, int] = {}
        self.deleted: list[str] = []

    def create_presigned_upload(
        self, *, key: str, content_type: str, max_size_bytes: int, expires_in_seconds: int
    ) -> PresignedUpload:
        return PresignedUpload(
            url="https://s3.example/upload",
            fields={"key": key, "Content-Type": content_type},
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_seconds),
        )

    def create_presigned_download(
        self, *, key: str, file_name: str, expires_in_seconds: int
    ) -> PresignedDownload:
        return PresignedDownload(
            url=f"https://s3.example/{key}",
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_seconds),
        )

    def head_object(self, key: str) -> StoredObject | None:
        size = self.uploaded.get(key)
        return None if size is None else StoredObject(key=key, size_bytes=size, content_type=None)

    def delete_object(self, key: str) -> None:
        self.deleted.append(key)


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    engine = create_engine(DATABASE_URL)  # type: ignore[arg-type]
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cursor:
            for name in (
                "002_lecturer_profile.sql",
                "003_faculty_workload.sql",
                "004_workload_entry_lock.sql",
            ):
                cursor.execute((MIGRATIONS / name).read_text())
        raw.commit()
    finally:
        raw.close()
    yield engine
    engine.dispose()


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def api(app: FastAPI, engine: Engine, storage: FakeStorage) -> Iterator[TestClient]:
    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_object_storage] = lambda: storage
    with TestClient(app) as client:
        yield client


def as_(lecturer_id: str) -> dict[str, str]:
    return {"X-Lecturer-Id": lecturer_id}


def ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, response.text
    return response.json() if response.content else None


def test_full_workload_flow(api: TestClient, storage: FakeStorage) -> None:
    v2 = "/api/v2"
    # --- people and positions ---
    dept = ok(api.post(f"{v2}/departments", json={"code": "CS", "name_th": "คอม"}), 201)
    ok(api.post(f"{v2}/departments", json={"code": "CS", "name_th": "ซ้ำ"}), 409)

    def lecturer(name: str, rank: str | None = None) -> str:
        body = {"name_th": name, "email": f"{name}@x.ac.th", "department_id": dept["id"]}
        if rank:
            body["rank"] = rank
        return ok(api.post(f"{v2}/lecturers", json=body), 201)["lecturer_id"]

    owner = lecturer("owner", "ผู้ช่วยศาสตราจารย์")
    chair, committee, staff = lecturer("chair"), lecturer("committee"), lecturer("staff")
    exec1, exec2 = lecturer("exec1"), lecturer("exec2")
    start = (date.today() - timedelta(days=30)).isoformat()

    def appoint(who: str, position: str, department_id: int | None = None) -> Any:
        body = {"position": position, "department_id": department_id, "start_date": start}
        return api.post(f"{v2}/lecturers/{who}/positions", json=body)

    ok(appoint(chair, "dept_chair", dept["id"]), 201)
    ok(appoint(committee, "dept_committee", dept["id"]), 201)
    ok(appoint(exec1, "exec_committee"), 201)
    ok(appoint(exec2, "exec_committee"), 201)
    ok(appoint(exec2, "exec_committee"), 409)  # overlapping term
    ok(appoint(chair, "dept_chair"), 400)  # department position without a department
    me = ok(api.get(f"{v2}/me", headers=as_(chair)))
    assert me["signer_roles"] == ["performer", "dept_chair"]
    ok(api.get(f"{v2}/me"), 401)

    # --- rubric ---
    version = ok(api.post(f"{v2}/rubric-versions", json={"code": "2567-r1"}), 201)
    vid = version["id"]
    teaching = ok(
        api.post(
            f"{v2}/rubric-versions/{vid}/categories",
            json={"code": "1", "name_th": "งานสอน", "cap": 900, "sort_order": 10},
        ),
        201,
    )
    admin = ok(
        api.post(
            f"{v2}/rubric-versions/{vid}/categories",
            json={"code": "3", "name_th": "งานบริหาร", "cap": 400, "sort_order": 30},
        ),
        201,
    )
    s11 = ok(
        api.post(
            f"{v2}/rubric-categories/{teaching['id']}/sections",
            json={"code": "1.1", "name_th": "วิชาบรรยาย", "sort_order": 20},
        ),
        201,
    )
    s31 = ok(
        api.post(
            f"{v2}/rubric-categories/{admin['id']}/sections",
            json={"code": "3.1", "name_th": "งานบริหาร", "cap": 400, "sort_order": 10},
        ),
        201,
    )
    lecture = ok(
        api.post(
            f"{v2}/rubric-sections/{s11['id']}/items",
            json={
                "label_th": "นักศึกษา < 100 คน",
                "weight": 1.0,
                "unit": "credit",
                "unit_divisor": 3,
                "counts_teaching_credit": True,
                "tier_min": 0,
                "tier_max": 99,
                "field_schema": {"hours": {"type": "int", "required": True}},
            },
        ),
        201,
    )
    head = ok(
        api.post(
            f"{v2}/rubric-sections/{s31['id']}/items",
            json={
                "label_th": "หัวหน้าสาขาวิชา",
                "weight_mode": "ranged",
                "weight_min": 1.0,
                "weight_max": 2.0,
                "range_basis": "weight",
                "assessor_position": "exec_committee",
                "assessment_agg": "average",
                "unit": "term",
            },
        ),
        201,
    )
    ok(
        api.post(
            f"{v2}/rubric-sections/{s31['id']}/items",
            json={"label_th": "x", "weight_mode": "ranged", "unit": "term"},
        ),
        422,
    )
    ok(
        api.post(
            f"{v2}/rubric-categories/{teaching['id']}/sections",
            json={"code": "1.1.1", "name_th": "ย่อย", "parent_id": s11["id"], "sort_order": 21},
        ),
        201,
    )
    form = ok(api.get(f"{v2}/rubric-versions/{vid}/form"))
    assert [c["code"] for c in form["categories"][0]["sections"][0]["children"]] == ["1.1.1"]
    assert [c["code"] for c in form["categories"]] == ["1", "3"]
    assert form["categories"][0]["sections"][0]["items"][0]["id"] == lecture["id"]

    # --- round (locks the rubric) ---
    rnd = ok(
        api.post(
            f"{v2}/rounds",
            json={
                "rubric_version_id": vid,
                "name_th": "รอบ 1/2568",
                "period_start": "2025-01-01",
                "period_end": "2025-06-30",
                "salary_effective_on": "2025-10-01",
                "academic_year": 2568,
                "is_open": True,
            },
        ),
        201,
    )
    ok(api.patch(f"{v2}/rubric-versions/{vid}", json={"overall_cap": 1}), 409)
    ok(api.patch(f"{v2}/rubric-items/{lecture['id']}", json={"weight": 2}), 409)
    ok(api.patch(f"{v2}/rubric-items/{lecture['id']}", json={"is_active": True}))
    # a locked version can still be copied into a new, editable one
    copy = ok(
        api.post(f"{v2}/rubric-versions", json={"code": "2568-r1", "source_version_id": vid}),
        201,
    )
    copied_form = ok(api.get(f"{v2}/rubric-versions/{copy['id']}/form"))
    assert [c["code"] for c in copied_form["categories"]] == ["1", "3"]
    assert [
        item["label_th"] for c in copied_form["categories"] for item in c["sections"][0]["items"]
    ] == ["นักศึกษา < 100 คน", "หัวหน้าสาขาวิชา"]
    copied_child = copied_form["categories"][0]["sections"][0]["children"][0]
    assert copied_child["parent_id"] == copied_form["categories"][0]["sections"][0]["id"]
    ok(api.patch(f"{v2}/rubric-versions/{copy['id']}", json={"overall_cap": 1800}))

    # --- the owner fills in the form ---
    sub = ok(api.post(f"{v2}/submissions", json={"round_id": rnd["id"]}, headers=as_(owner)), 201)
    assert sub["rank_snapshot"] == "asst_prof"
    ok(api.post(f"{v2}/submissions", json={"round_id": rnd["id"]}, headers=as_(owner)), 409)
    entries = f"{v2}/submissions/{sub['id']}/entries"
    line = {
        "item_id": lecture["id"],
        "course_code": "CS222",
        "student_count": 60,
        "quantity": 3,
        "credits": 3,
        "details": {"hours": 45},
    }
    e1 = ok(api.post(entries, json=line, headers=as_(owner)), 201)
    assert (e1["score"], e1["weight_applied"]) == (200.0, 1.0)
    ok(api.post(entries, json=line | {"details": {}}, headers=as_(owner)), 400)
    ok(api.post(entries, json=line | {"student_count": 150}, headers=as_(owner)), 400)
    e2 = ok(api.post(entries, json={"item_id": head["id"]}, headers=as_(owner)), 201)
    assert (e2["score"], e2["weight_applied"]) == (0.0, None)

    summary = ok(api.get(f"{v2}/submissions/{sub['id']}/summary"))
    assert (summary["raw_total"], summary["teaching_credits"]) == (200.0, 3.0)
    assert (summary["pending_assessments"], summary["meets_min_teaching_credits"]) == (1, False)
    ok(api.get(f"{v2}/submissions/{sub['id']}/totals"), 409)  # not sent yet

    got = api.get(f"{v2}/entries/{e1['id']}")
    ok(
        api.patch(
            f"{v2}/entries/{e1['id']}",
            json={"quantity": 6},
            headers=as_(owner) | {"If-Match": '"stale"'},
        ),
        412,
    )
    e1 = ok(
        api.patch(
            f"{v2}/entries/{e1['id']}",
            json={"quantity": 6, "credits": 6},
            headers=as_(owner) | {"If-Match": got.headers["ETag"]},
        )
    )
    assert e1["score"] == 400.0

    # --- evidence ---
    upload = ok(
        api.post(
            f"{v2}/entries/{e1['id']}/evidence",
            json={"file_name": "คำสั่ง.pdf", "mime_type": "application/pdf", "size_bytes": 1000},
            headers=as_(owner),
        ),
        201,
    )
    evidence = upload["evidence"]
    ok(
        api.patch(
            f"{v2}/evidence/{evidence['id']}", json={"status": "uploaded"}, headers=as_(owner)
        ),
        400,
    )
    storage.uploaded[upload["fields"]["key"]] = 900
    confirmed = ok(
        api.patch(
            f"{v2}/evidence/{evidence['id']}", json={"status": "uploaded"}, headers=as_(owner)
        )
    )
    assert (confirmed["status"], confirmed["size_bytes"]) == ("uploaded", 900)
    redirect = api.get(f"{v2}/evidence/{evidence['id']}/content", follow_redirects=False)
    assert redirect.status_code == 302

    # --- send and review ---
    approvals = f"{v2}/submissions/{sub['id']}/approvals"
    sent = ok(api.post(approvals, json={"decision": "approved"}, headers=as_(owner)), 201)
    assert sent["role"] == "performer"
    totals = ok(api.get(f"{v2}/submissions/{sub['id']}/totals"))
    assert totals["raw_total"] == 400.0
    ok(api.patch(f"{v2}/entries/{e1['id']}", json={"quantity": 3}, headers=as_(owner)), 409)
    ok(api.post(approvals, json={"decision": "approved"}, headers=as_(staff)), 201)  # -> assessing

    my_value = f"{v2}/entries/{e2['id']}/assessments/me"
    ok(api.put(my_value, json={"value_given": 1.8}, headers=as_(chair)), 403)  # not exec
    ok(api.put(my_value, json={"value_given": 2.5}, headers=as_(exec1)), 400)  # out of range
    ok(api.put(my_value, json={"value_given": 1.8}, headers=as_(exec1)))
    ok(api.put(my_value, json={"value_given": 1.5}, headers=as_(exec2)))
    queue = ok(api.get(f"{v2}/assessments", params={"status": "done"}, headers=as_(exec1)))
    assert queue["meta"]["total"] == 1
    scored = ok(api.get(f"{v2}/entries/{e2['id']}"))
    assert (scored["weight_applied"], scored["score"]) == (1.65, 330.0)
    totals = ok(api.get(f"{v2}/submissions/{sub['id']}/totals"))
    assert (totals["raw_total"], totals["capped_total"]) == (730.0, 730.0)

    ok(api.post(approvals, json={"decision": "approved"}, headers=as_(chair)), 201)  # -> review
    ok(api.post(approvals, json={"decision": "returned"}, headers=as_(committee)), 400)
    ok(
        api.post(
            approvals, json={"decision": "returned", "comment": "แนบคำสั่ง"}, headers=as_(committee)
        ),
        201,
    )
    # returned: the owner may fix entries again (migration 004), then send again
    ok(api.patch(f"{v2}/entries/{e1['id']}", json={"note": "แก้แล้ว"}, headers=as_(owner)))
    ok(api.post(approvals, json={"decision": "approved"}, headers=as_(owner)), 201)
    history = ok(api.get(approvals))
    assert [a["role"] for a in history["items"]] == [
        "performer",
        "receiver",
        "dept_chair",
        "dept_committee",
        "performer",
    ]

    report = ok(api.get(f"{v2}/rounds/{rnd['id']}/report"))
    assert report["summary"]["submissions"] == 1
    assert report["rows"][0]["capped_total"] == 730.0
    ok(api.delete(f"{v2}/submissions/{sub['id']}", headers=as_(owner)), 409)
    ok(api.get(f"{v2}/submissions/not-a-uuid"), 422)
