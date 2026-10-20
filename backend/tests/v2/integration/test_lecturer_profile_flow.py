"""Education, expertise, publication authors, profile image and CV over HTTP against a real
PostgreSQL. How to run it: see support.py.
"""

from fastapi.testclient import TestClient

from tests.v2.integration.support import FakeStorage, ok, requires_database

pytestmark = requires_database

V2 = "/api/v2"


def new_lecturer(api: TestClient, name: str) -> str:
    body = {"name_th": name, "email": f"{name}@x.ac.th"}
    return ok(api.post(f"{V2}/lecturers", json=body), 201)["lecturer_id"]


def test_education(api: TestClient) -> None:
    somchai, other = new_lecturer(api, "edu-somchai"), new_lecturer(api, "edu-other")
    base = f"{V2}/lecturers/{somchai}/educations"

    old = ok(api.post(base, json={"degree": "B.Sc.", "graduation_year": "2545"}), 201)
    phd = ok(api.post(base, json={"degree": "Ph.D.", "graduation_year": "2555"}), 201)
    ok(api.post(base, json={"degree": " "}), 422)

    listed = ok(api.get(base))
    assert [item["education_id"] for item in listed["items"]] == [
        phd["education_id"],
        old["education_id"],
    ]

    updated = ok(api.patch(f"{base}/{phd['education_id']}", json={"institution": "TU"}))
    assert updated == phd | {"institution": "TU"}
    # Another lecturer's row is not reachable through this lecturer
    ok(
        api.patch(
            f"{V2}/lecturers/{other}/educations/{phd['education_id']}", json={"country": "x"}
        ),
        404,
    )

    ok(api.delete(f"{base}/{old['education_id']}"), 204)
    assert ok(api.get(base))["meta"]["count"] == 1


def test_expertise(api: TestClient) -> None:
    somchai = new_lecturer(api, "exp-somchai")
    cloud = ok(api.post(f"{V2}/expertise", json={"description": "Cloud Computing"}), 201)
    ai = ok(api.post(f"{V2}/expertise", json={"description": "AI"}), 201)
    ok(api.post(f"{V2}/expertise", json={"description": "cloud computing"}), 409)

    page = ok(api.get(f"{V2}/expertise", params={"q": "cloud"}))
    assert [item["expertise_id"] for item in page["items"]] == [cloud["expertise_id"]]
    assert page["meta"]["total"] == 1

    mine = f"{V2}/lecturers/{somchai}/expertise"
    ids = [cloud["expertise_id"], ai["expertise_id"]]
    replaced = ok(api.put(mine, json={"expertise_ids": ids}))
    assert [item["description"] for item in replaced["items"]] == ["AI", "Cloud Computing"]
    ok(api.put(mine, json={"expertise_ids": [cloud["expertise_id"], 999]}), 404)
    assert ok(api.get(mine))["meta"]["count"] == 2  # failed replace changed nothing

    ok(api.delete(f"{mine}/{ai['expertise_id']}"), 204)
    ok(api.delete(f"{mine}/{ai['expertise_id']}"), 404)

    # Deleting the master row also removes it from the lecturer
    ok(api.delete(f"{V2}/expertise/{cloud['expertise_id']}"), 204)
    assert ok(api.get(mine))["meta"]["count"] == 0


def test_publication_authors(api: TestClient) -> None:
    first, second = new_lecturer(api, "pub-first"), new_lecturer(api, "pub-second")
    body = {"title": "Cloud paper", "publication_year": 2567, "lecturer_ids": [second, first]}
    publication = ok(api.post(f"{V2}/publications", json=body), 201)

    for lecturer_id, order in ((second, 1), (first, 2)):
        items = ok(api.get(f"{V2}/lecturers/{lecturer_id}/publications"))["items"]
        assert [(p["publication_id"], p["author_order"]) for p in items] == [
            (publication["publication_id"], order)
        ]


def test_profile_image_and_cv(api: TestClient, storage: FakeStorage) -> None:
    somchai = new_lecturer(api, "file-somchai")
    image = f"{V2}/lecturers/{somchai}/profile-image"

    ok(api.get(image), 404)
    ok(
        api.post(f"{image}/presign", json={"content_type": "application/pdf", "size_bytes": 10}),
        400,
    )

    first = ok(api.post(f"{image}/presign", json={"content_type": "image/png", "size_bytes": 10}))
    ok(api.post(f"{image}/complete", json={"object_key": first["object_key"]}), 400)  # not uploaded

    storage.uploaded[first["object_key"]] = 10
    storage.content_types[first["object_key"]] = "image/png"
    lecturer = ok(api.post(f"{image}/complete", json={"object_key": first["object_key"]}))
    assert lecturer["profile_image_url"] == first["object_key"]
    assert ok(api.get(image))["download_url"].endswith(first["object_key"])

    # Replacing the image removes the old file
    second = ok(api.post(f"{image}/presign", json={"content_type": "image/jpeg", "size_bytes": 5}))
    storage.uploaded[second["object_key"]] = 5
    storage.content_types[second["object_key"]] = "image/jpeg"
    ok(api.post(f"{image}/complete", json={"object_key": second["object_key"]}))
    assert storage.deleted == [first["object_key"]]

    cv = f"{V2}/lecturers/{somchai}/cv"
    upload = ok(
        api.post(f"{cv}/presign", json={"content_type": "application/pdf", "size_bytes": 9})
    )
    storage.uploaded[upload["object_key"]] = 9
    storage.content_types[upload["object_key"]] = "application/pdf"
    ok(api.post(f"{cv}/complete", json={"object_key": upload["object_key"]}))
    assert ok(api.get(cv))["download_url"].endswith(upload["object_key"])

    ok(api.delete(cv), 204)
    ok(api.get(cv), 404)
    assert storage.deleted[-1] == upload["object_key"]
