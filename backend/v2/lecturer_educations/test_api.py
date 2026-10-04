"""API/controller tests for lecturer education creation."""

from __future__ import annotations

import base64
import json
import unittest

from backend.v2.lecturer_educations.controller import handle_request
from backend.v2.lecturer_educations.dao import EducationNotFoundError, LecturerNotFoundError
from backend.v2.lecturer_educations.service import LecturerEducationService


class FakeEducationDao:
    def __init__(self, error=None, items=None):
        self.error = error
        self.items = items or []
        self.calls = []
        self.list_calls = []
        self.get_calls = []

    def create(self, lecturer_id, education):
        self.calls.append((lecturer_id, education))
        if self.error:
            raise self.error
        return {
            "id": "edu_123",
            "faculty_id": lecturer_id,
            "degree": education.degree,
            "display_order": education.display_order or 0,
        }

    def list_for_lecturer(self, lecturer_id):
        self.list_calls.append(lecturer_id)
        if self.error:
            raise self.error
        return self.items

    def get_for_lecturer(self, lecturer_id, education_id):
        self.get_calls.append((lecturer_id, education_id))
        if self.error:
            raise self.error
        if self.error:
            raise self.error
        return {
            "id": education_id,
            "faculty_id": lecturer_id,
            "degree": "Ph.D.",
        }


def api_event(method="POST", lecturer_id="fac_demo", body=None, education_id=None):
    path = f"/api/v2/lecturers/{lecturer_id}/educations"
    if education_id is not None:
        path += f"/{education_id}"
    return {
        "rawPath": path,
        "requestContext": {"http": {"method": method}},
        "body": json.dumps(body) if body is not None else None,
    }


class LecturerEducationApiTest(unittest.TestCase):
    def test_get_detail_returns_education(self):
        dao = FakeEducationDao()

        response = handle_request(
            api_event(method="GET", education_id="edu_123"),
            LecturerEducationService(dao),
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            json.loads(response["body"])["data"],
            {"id": "edu_123", "faculty_id": "fac_demo", "degree": "Ph.D."},
        )
        self.assertEqual(dao.get_calls, [("fac_demo", "edu_123")])

    def test_get_detail_unknown_education_returns_not_found(self):
        service = LecturerEducationService(FakeEducationDao(error=EducationNotFoundError()))

        response = handle_request(
            api_event(method="GET", education_id="edu_missing"),
            service,
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response["body"])["error"]["code"], "EDUCATION_NOT_FOUND")

    def test_get_detail_unknown_lecturer_returns_not_found(self):
        service = LecturerEducationService(FakeEducationDao(error=LecturerNotFoundError()))

        response = handle_request(
            api_event(method="GET", education_id="edu_123"),
            service,
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response["body"])["error"]["code"], "LECTURER_NOT_FOUND")

    def test_get_detail_invalid_education_id_returns_validation_error(self):
        dao = FakeEducationDao()

        response = handle_request(
            api_event(method="GET", education_id="edu bad/id"),
            LecturerEducationService(dao),
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            json.loads(response["body"])["error"]["details"],
            {"field": "educationId"},
        )
        self.assertEqual(dao.get_calls, [])

    def test_detail_route_rejects_post(self):
        response = handle_request(
            api_event(method="POST", education_id="edu_123", body={"degree": "Ph.D."}),
            LecturerEducationService(FakeEducationDao()),
        )

        self.assertEqual(response["statusCode"], 405)
        self.assertEqual(response["headers"]["Allow"], "GET")

    def test_get_returns_education_list_and_count(self):
        items = [
            {"id": "edu_123", "faculty_id": "fac_demo", "display_order": 0},
            {"id": "edu_456", "faculty_id": "fac_demo", "display_order": 1},
        ]
        dao = FakeEducationDao(items=items)

        response = handle_request(
            api_event(method="GET"),
            LecturerEducationService(dao),
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), {"items": items, "meta": {"count": 2}})
        self.assertEqual(dao.list_calls, ["fac_demo"])
        self.assertEqual(dao.calls, [])

    def test_get_returns_empty_list_for_lecturer_without_education(self):
        response = handle_request(
            api_event(method="GET"),
            LecturerEducationService(FakeEducationDao()),
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            json.loads(response["body"]),
            {"items": [], "meta": {"count": 0}},
        )

    def test_get_unknown_or_inactive_lecturer_returns_not_found(self):
        service = LecturerEducationService(FakeEducationDao(error=LecturerNotFoundError()))

        response = handle_request(api_event(method="GET"), service)

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response["body"])["error"]["code"], "LECTURER_NOT_FOUND")

    def test_create_returns_created_education_and_location(self):
        dao = FakeEducationDao()
        service = LecturerEducationService(dao)

        response = handle_request(
            api_event(body={"degree": "M.Sc.", "institution": "Demo University"}),
            service,
        )

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(json.loads(response["body"])["data"]["id"], "edu_123")
        self.assertEqual(
            response["headers"]["Location"],
            "/api/v2/lecturers/fac_demo/educations/edu_123",
        )
        self.assertEqual(dao.calls[0][0], "fac_demo")

    def test_invalid_payload_returns_validation_error(self):
        service = LecturerEducationService(FakeEducationDao())

        response = handle_request(api_event(body={"graduation_year": "2560"}), service)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response["body"])["error"]["code"], "VALIDATION_ERROR")

    def test_invalid_lecturer_id_returns_validation_error(self):
        service = LecturerEducationService(FakeEducationDao())

        response = handle_request(
            api_event(lecturer_id="fac_demo'; DROP TABLE faculty;--", body={"degree": "Ph.D."}),
            service,
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            json.loads(response["body"])["error"]["details"],
            {"field": "lecturerId"},
        )

    def test_malformed_json_returns_bad_request(self):
        event = api_event()
        event["body"] = "{"

        response = handle_request(event, LecturerEducationService(FakeEducationDao()))

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response["body"])["error"]["details"], {"field": "body"})

    def test_base64_json_body_is_decoded(self):
        event = api_event()
        event["body"] = base64.b64encode(b'{"degree":"Ph.D."}').decode("ascii")
        event["isBase64Encoded"] = True
        dao = FakeEducationDao()

        response = handle_request(event, LecturerEducationService(dao))

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(dao.calls[0][1].degree, "Ph.D.")

    def test_invalid_base64_returns_bad_request(self):
        event = api_event()
        event["body"] = "not-base64!"
        event["isBase64Encoded"] = True

        response = handle_request(event, LecturerEducationService(FakeEducationDao()))

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response["body"])["error"]["details"], {"field": "body"})

    def test_unknown_or_inactive_lecturer_returns_not_found(self):
        service = LecturerEducationService(FakeEducationDao(error=LecturerNotFoundError()))

        response = handle_request(api_event(body={"degree": "Ph.D."}), service)

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response["body"])["error"]["code"], "LECTURER_NOT_FOUND")

    def test_unsupported_method_is_rejected(self):
        response = handle_request(
            api_event(method="PATCH"),
            LecturerEducationService(FakeEducationDao()),
        )

        self.assertEqual(response["statusCode"], 405)
        self.assertEqual(response["headers"]["Allow"], "GET, POST")

    def test_unmatched_route_is_not_found(self):
        event = api_event(body={"degree": "Ph.D."})
        event["rawPath"] = "/api/v2/faculties/fac_demo/educations"

        response = handle_request(event, LecturerEducationService(FakeEducationDao()))

        self.assertEqual(response["statusCode"], 404)

    def test_internal_error_does_not_leak_details(self):
        service = LecturerEducationService(
            FakeEducationDao(error=RuntimeError("database password must not leak"))
        )

        response = handle_request(api_event(body={"degree": "Ph.D."}), service)

        self.assertEqual(response["statusCode"], 500)
        self.assertEqual(json.loads(response["body"])["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("password", response["body"])


if __name__ == "__main__":
    unittest.main()
