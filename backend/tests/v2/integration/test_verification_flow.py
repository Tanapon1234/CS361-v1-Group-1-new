"""Verification of publications against a real PostgreSQL (migration 005).
How to run it: see support.py."""

from fastapi.testclient import TestClient

from tests.v2.integration.support import ok, requires_database

pytestmark = requires_database

V2 = "/api/v2"


def person(api: TestClient, name: str) -> str:
    body = {"name_th": name, "email": f"{name}@x.ac.th"}
    return ok(api.post(f"{V2}/lecturers", json=body), 201)["lecturer_id"]


def as_(lecturer_id: str, roles: str = "") -> dict[str, str]:
    return {"X-Lecturer-Id": lecturer_id, "X-Dev-Roles": roles}


def test_reviewer_verifies_and_the_author_is_locked_out(api: TestClient) -> None:
    author, reviewer = person(api, "ver-author"), person(api, "ver-reviewer")
    body = {"title": "Edge scheduling", "publication_year": 2024, "lecturer_ids": [author]}
    pub = ok(api.post(f"{V2}/publications", json=body, headers=as_(author)), 201)
    url = f"{V2}/publications/{pub['publication_id']}"

    queue = ok(api.get(f"{V2}/verifications/publications", headers=as_(reviewer, "reviewer")))
    assert [p["publication_id"] for p in queue["items"]] == [pub["publication_id"]]
    assert queue["items"][0]["authors"] == ["ver-author"]

    # the author is not a reviewer; a reviewer cannot verify their own work
    ok(api.put(f"{url}/verification", json={"status": "verified"}, headers=as_(author)), 403)
    ok(
        api.put(
            f"{url}/verification", json={"status": "verified"}, headers=as_(author, "reviewer")
        ),
        403,
    )
    ok(
        api.put(
            f"{url}/verification", json={"status": "rejected"}, headers=as_(reviewer, "reviewer")
        ),
        422,
    )  # rejection needs a note

    verdict = ok(
        api.put(
            f"{url}/verification", json={"status": "verified"}, headers=as_(reviewer, "reviewer")
        )
    )
    assert (verdict["verification_status"], verdict["verified_by"]) == ("verified", reviewer)
    assert ok(api.get(f"{url}/verification", headers=as_(author)))["verification_status"] == (
        "verified"
    )

    ok(api.patch(url, json={"volume": "9"}, headers=as_(author)), 403)
    ok(api.patch(url, json={"volume": "9"}, headers=as_(reviewer, "staff")))

    ok(
        api.put(
            f"{url}/verification",
            json={"status": "rejected", "note": "ไม่พบ DOI"},
            headers=as_(reviewer, "reviewer"),
        )
    )
    ok(api.patch(url, json={"doi": "10.1/edge"}, headers=as_(author)))
    back = ok(api.get(f"{url}/verification", headers=as_(author)))
    assert (back["verification_status"], back["verified_by"]) == ("pending", None)
