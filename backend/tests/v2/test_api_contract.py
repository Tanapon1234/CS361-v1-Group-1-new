"""The agreed endpoint list. Adding, removing or renaming an endpoint must update this file.

Path parameters use snake_case here and in code (`{lecturer_id}`); the URLs are the same
as the `{lecturerId}` placeholders in the team's API list.
"""

import pytest
from fastapi import FastAPI

EXPECTED_ENDPOINTS = {
    # lecturer
    ("POST", "/api/v2/lecturers"),
    ("GET", "/api/v2/lecturers"),
    ("GET", "/api/v2/lecturers/{lecturer_id}"),
    ("PATCH", "/api/v2/lecturers/{lecturer_id}"),
    ("POST", "/api/v2/lecturers/{lecturer_id}/activate"),
    ("POST", "/api/v2/lecturers/{lecturer_id}/deactivate"),
    # profile image
    ("POST", "/api/v2/lecturers/{lecturer_id}/profile-image/presign"),
    ("POST", "/api/v2/lecturers/{lecturer_id}/profile-image/complete"),
    ("DELETE", "/api/v2/lecturers/{lecturer_id}/profile-image"),
    # cv
    ("POST", "/api/v2/lecturers/{lecturer_id}/cv/presign"),
    ("POST", "/api/v2/lecturers/{lecturer_id}/cv/complete"),
    ("GET", "/api/v2/lecturers/{lecturer_id}/cv"),
    ("DELETE", "/api/v2/lecturers/{lecturer_id}/cv"),
    # education
    ("GET", "/api/v2/lecturers/{lecturer_id}/educations"),
    ("POST", "/api/v2/lecturers/{lecturer_id}/educations"),
    ("PATCH", "/api/v2/lecturers/{lecturer_id}/educations/{education_id}"),
    ("DELETE", "/api/v2/lecturers/{lecturer_id}/educations/{education_id}"),
    # research interest (master)
    ("GET", "/api/v2/research-interests"),
    ("POST", "/api/v2/research-interests"),
    ("PATCH", "/api/v2/research-interests/{research_interest_id}"),
    ("DELETE", "/api/v2/research-interests/{research_interest_id}"),
    # research interest (lecturer)
    ("GET", "/api/v2/lecturers/{lecturer_id}/research-interests"),
    ("PUT", "/api/v2/lecturers/{lecturer_id}/research-interests"),
    ("DELETE", "/api/v2/lecturers/{lecturer_id}/research-interests/{research_interest_id}"),
    # publication profile
    ("GET", "/api/v2/lecturers/{lecturer_id}/publication-profiles"),
    ("POST", "/api/v2/lecturers/{lecturer_id}/publication-profiles"),
    ("PATCH", "/api/v2/lecturers/{lecturer_id}/publication-profiles/{publication_profile_id}"),
    ("DELETE", "/api/v2/lecturers/{lecturer_id}/publication-profiles/{publication_profile_id}"),
    # publication
    ("GET", "/api/v2/publications"),
    ("POST", "/api/v2/publications"),
    ("GET", "/api/v2/publications/{publication_id}"),
    ("PATCH", "/api/v2/publications/{publication_id}"),
    ("DELETE", "/api/v2/publications/{publication_id}"),
    ("GET", "/api/v2/lecturers/{lecturer_id}/publications"),
    # expertise (master)
    ("GET", "/api/v2/expertise"),
    ("POST", "/api/v2/expertise"),
    ("GET", "/api/v2/expertise/{expertise_id}"),
    ("PATCH", "/api/v2/expertise/{expertise_id}"),
    ("DELETE", "/api/v2/expertise/{expertise_id}"),
    # expertise (lecturer)
    ("GET", "/api/v2/lecturers/{lecturer_id}/expertise"),
    ("PUT", "/api/v2/lecturers/{lecturer_id}/expertise"),
    ("DELETE", "/api/v2/lecturers/{lecturer_id}/expertise/{expertise_id}"),
}


@pytest.fixture
def documented_endpoints(app: FastAPI) -> set[tuple[str, str]]:
    return {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        if path.startswith("/api/v2/")
        for method in operations
    }


def test_every_agreed_endpoint_exists(documented_endpoints: set[tuple[str, str]]) -> None:
    assert sorted(EXPECTED_ENDPOINTS - documented_endpoints) == []


def test_no_endpoint_outside_the_agreed_list(documented_endpoints: set[tuple[str, str]]) -> None:
    assert sorted(documented_endpoints - EXPECTED_ENDPOINTS) == []


def test_operation_ids_are_unique(app: FastAPI) -> None:
    operation_ids = [
        operation["operationId"]
        for operations in app.openapi()["paths"].values()
        for operation in operations.values()
    ]
    assert len(operation_ids) == len(set(operation_ids))
