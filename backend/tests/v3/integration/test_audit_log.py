"""Every change through the API leaves an audit_log row (006). How to run: see support.py."""

from fastapi.testclient import TestClient

from tests.v3.integration.support import ok, requires_database

pytestmark = requires_database

V2 = "/api/v3"


def test_changes_are_audited_with_who_and_what(api: TestClient) -> None:
    lecturer = ok(
        api.post(f"{V2}/lecturers", json={"name_th": "audit-a", "email": "audit-a@x.ac.th"}), 201
    )
    me = {"X-Lecturer-Id": lecturer["lecturer_id"], "X-Dev-Roles": ""}
    ok(api.patch(f"{V2}/lecturers/{lecturer['lecturer_id']}", json={"office": "SC-9"}, headers=me))
    education = ok(
        api.post(
            f"{V2}/lecturers/{lecturer['lecturer_id']}/educations",
            json={"degree": "Ph.D."},
            headers=me,
        ),
        201,
    )
    ok(
        api.delete(
            f"{V2}/lecturers/{lecturer['lecturer_id']}/educations/{education['education_id']}",
            headers=me,
        ),
        204,
    )
    # A request that fails leaves no audit row (the transaction rolls back)
    ok(api.post(f"{V2}/lecturers", json={"name_th": "dup", "email": "audit-a@x.ac.th"}), 409)

    log = ok(api.get(f"{V2}/audit-log", params={"actor_id": lecturer["lecturer_id"]}))
    actions = [(row["action"], row["entity"]) for row in log["items"]]
    assert actions == [("delete", "education"), ("insert", "education"), ("update", "lecturer")]
    update = log["items"][2]
    assert update["changes"]["office"] == [None, "SC-9"]
    assert update["request"] == f"PATCH /api/v3/lecturers/{lecturer['lecturer_id']}"
    assert update["actor_roles"] == "lecturer"

    created = ok(
        api.get(
            f"{V2}/audit-log",
            params={"entity": "lecturer", "entity_id": lecturer["lecturer_id"]},
        )
    )
    assert [row["action"] for row in created["items"]] == ["update", "insert"]
    assert created["items"][1]["actor_roles"] == "admin"
    assert sum(row["changes"].get("email") == "dup" for row in created["items"]) == 0

    # Only admins read it
    ok(api.get(f"{V2}/audit-log", headers={"X-Dev-Roles": "staff"}), 403)
