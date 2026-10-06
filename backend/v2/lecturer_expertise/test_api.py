"""HTTP contract tests for lecturer-expertise mapping endpoints."""

import base64
import json
import unittest

from backend.v2.expertise.dto import ExpertiseDTO
from backend.v2.lecturer_expertise.controller import handle_request
from backend.v2.lecturer_expertise.dao import LecturerExpertisePersistencePendingError
from backend.v2.lecturer_expertise.dto import ReplaceLecturerExpertiseDTO
from backend.v2.lecturer_expertise.service import LecturerExpertiseService


def api_event(
    method: str,
    path: str = "/api/v2/lecturers/fac_1/expertise",
    body: str | None = None,
) -> dict:
    return {
        "rawPath": path,
        "body": body,
        "requestContext": {"http": {"method": method, "path": path}},
    }


def response_body(response: dict) -> dict:
    return json.loads(response["body"])


class LecturerExpertiseApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.items = [
            ExpertiseDTO(
                id="exp_1",
                faculty_id="fac_1",
                value="Data Mining",
                visibility="PUBLIC",
            )
        ]

        class FakeDao:
            def list_for_lecturer(self, lecturer_id: str) -> list[ExpertiseDTO]:
                self.requested_lecturer_id = lecturer_id
                return self.items

            def replace_for_lecturer(
                self,
                lecturer_id: str,
                expertise: ReplaceLecturerExpertiseDTO,
            ) -> list[ExpertiseDTO]:
                self.replacement = (lecturer_id, expertise)
                return self.items

            def remove_for_lecturer(self, lecturer_id: str, expertise_id: str) -> None:
                self.removal = (lecturer_id, expertise_id)

        self.dao = FakeDao()
        self.dao.items = self.items
        self.service = LecturerExpertiseService(self.dao)

    def test_get_returns_lecturer_expertise_and_count(self) -> None:
        response = handle_request(api_event("GET"), self.service)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            response_body(response),
            {
                "items": [
                    {
                        "id": "exp_1",
                        "faculty_id": "fac_1",
                        "value": "Data Mining",
                        "visibility": "PUBLIC",
                    }
                ],
                "meta": {"count": 1},
            },
        )
        self.assertEqual(self.dao.requested_lecturer_id, "fac_1")

    def test_get_without_connected_dao_returns_not_implemented(self) -> None:
        response = handle_request(api_event("GET"))

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")

    def test_put_replaces_lecturer_expertise(self) -> None:
        response = handle_request(
            api_event("PUT", body=json.dumps({"expertiseIds": ["exp_1"]})),
            self.service,
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            self.dao.replacement,
            ("fac_1", ReplaceLecturerExpertiseDTO(("exp_1",))),
        )
        self.assertEqual(response_body(response)["meta"], {"count": 1})

    def test_put_accepts_base64_encoded_request_body(self) -> None:
        event = api_event(
            "PUT",
            body=base64.b64encode(
                json.dumps({"expertiseIds": ["exp_1"]}).encode("utf-8")
            ).decode("ascii"),
        )
        event["isBase64Encoded"] = True

        response = handle_request(event, self.service)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            self.dao.replacement,
            ("fac_1", ReplaceLecturerExpertiseDTO(("exp_1",))),
        )

    def test_put_rejects_invalid_request_body(self) -> None:
        for body in (
            "{invalid",
            json.dumps({}),
            json.dumps({"expertiseIds": "exp_1"}),
            json.dumps({"expertiseIds": [1]}),
        ):
            with self.subTest(body=body):
                response = handle_request(
                    api_event("PUT", body=body),
                    self.service,
                )

                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(
                    response_body(response)["error"]["code"],
                    "INVALID_BODY",
                )

    def test_put_without_connected_dao_returns_not_implemented(self) -> None:
        response = handle_request(
            api_event("PUT", body=json.dumps({"expertiseIds": []}))
        )

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")

    def test_delete_removes_lecturer_expertise(self) -> None:
        response = handle_request(
            api_event(
                "DELETE",
                path="/api/v2/lecturers/fac_1/expertise/exp_1",
            ),
            self.service,
        )

        self.assertEqual(response["statusCode"], 204)
        self.assertEqual(response["body"], "")
        self.assertEqual(self.dao.removal, ("fac_1", "exp_1"))

    def test_delete_without_connected_dao_returns_not_implemented(self) -> None:
        response = handle_request(
            api_event(
                "DELETE",
                path="/api/v2/lecturers/fac_1/expertise/exp_1",
            )
        )

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")

    def test_unknown_route_returns_not_found(self) -> None:
        response = handle_request(
            api_event("GET", path="/api/v2/lecturers/fac_1/interests")
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_FOUND")

    def test_wrong_method_returns_method_not_allowed(self) -> None:
        response = handle_request(api_event("POST"), self.service)

        self.assertEqual(response["statusCode"], 405)
        self.assertEqual(
            response_body(response)["error"]["code"],
            "METHOD_NOT_ALLOWED",
        )

    def test_malformed_detail_route_returns_not_found(self) -> None:
        response = handle_request(
            api_event(
                "DELETE",
                path="/api/v2/lecturers/fac_1/expertise/exp_1/extra",
            )
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_FOUND")


class LecturerExpertiseApiPersistenceErrorTest(unittest.TestCase):
    def test_unexpected_service_error_returns_internal_error(self) -> None:
        class BrokenDao:
            def list_for_lecturer(self, lecturer_id: str) -> list[ExpertiseDTO]:
                raise RuntimeError("database failure")

        response = handle_request(
            api_event("GET"),
            LecturerExpertiseService(BrokenDao()),
        )

        self.assertEqual(response["statusCode"], 500)
        self.assertEqual(response_body(response)["error"]["code"], "INTERNAL_ERROR")

    def test_pending_persistence_errors_are_not_silenced(self) -> None:
        class PendingDao:
            def list_for_lecturer(self, lecturer_id: str) -> list[ExpertiseDTO]:
                raise LecturerExpertisePersistencePendingError("pending")

        response = handle_request(
            api_event("GET"),
            LecturerExpertiseService(PendingDao()),
        )

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
