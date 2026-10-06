"""HTTP contract tests for POST /api/v2/expertise."""

import base64
import json
import unittest

from backend.v2.expertise.controller import handle_request
from backend.v2.expertise.dao import ExpertiseNotFoundError
from backend.v2.expertise.dto import (
    CreateExpertiseDTO,
    ExpertiseDTO,
    PatchExpertiseDTO,
)
from backend.v2.expertise.service import ExpertiseService


def api_event(
    method: str = "POST",
    body: str | None = None,
    path: str = "/api/v2/expertise",
    is_base64_encoded: bool = False,
) -> dict:
    return {
        "rawPath": path,
        "body": body,
        "isBase64Encoded": is_base64_encoded,
        "requestContext": {"http": {"method": method, "path": path}},
    }


def response_body(response: dict) -> dict:
    return json.loads(response["body"])


class ExpertiseApiTest(unittest.TestCase):
    def setUp(self) -> None:
        class FakeDao:
            def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
                return {
                    "id": "exp_1",
                    "faculty_id": expertise.faculty_id,
                    "value": expertise.value,
                }

            def list_all(self) -> list[ExpertiseDTO]:
                return [
                    ExpertiseDTO(
                        id="exp_1",
                        faculty_id="fac_1",
                        value="Data Mining",
                        visibility="PUBLIC",
                    )
                ]

            def get_by_id(self, expertise_id: str) -> ExpertiseDTO:
                if expertise_id != "exp_1":
                    raise ExpertiseNotFoundError(expertise_id)
                return ExpertiseDTO(
                    id="exp_1",
                    faculty_id="fac_1",
                    value="Data Mining",
                    visibility="PUBLIC",
                )

            def update(
                self,
                expertise_id: str,
                expertise: PatchExpertiseDTO,
            ) -> ExpertiseDTO:
                if expertise_id != "exp_1":
                    raise ExpertiseNotFoundError(expertise_id)
                return ExpertiseDTO(
                    id=expertise_id,
                    faculty_id="fac_1",
                    value=expertise.value,
                    visibility="PUBLIC",
                )

            def delete(self, expertise_id: str) -> None:
                if expertise_id != "exp_1":
                    raise ExpertiseNotFoundError(expertise_id)

        self.service = ExpertiseService(FakeDao())

    def test_list_returns_items_and_count(self) -> None:
        response = handle_request(api_event(method="GET"), self.service)

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

    def test_list_without_connected_dao_returns_not_implemented(self) -> None:
        response = handle_request(api_event(method="GET"))

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")

    def test_get_detail_returns_requested_item(self) -> None:
        response = handle_request(
            api_event(method="GET", path="/api/v2/expertise/exp_1"),
            self.service,
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            response_body(response),
            {
                "item": {
                    "id": "exp_1",
                    "faculty_id": "fac_1",
                    "value": "Data Mining",
                    "visibility": "PUBLIC",
                }
            },
        )

    def test_get_detail_returns_not_found_for_unknown_id(self) -> None:
        response = handle_request(
            api_event(method="GET", path="/api/v2/expertise/missing"),
            self.service,
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(
            response_body(response)["error"]["code"],
            "EXPERTISE_NOT_FOUND",
        )

    def test_get_detail_without_connected_dao_returns_not_implemented(self) -> None:
        response = handle_request(
            api_event(method="GET", path="/api/v2/expertise/exp_1")
        )

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")

    def test_patch_detail_updates_value(self) -> None:
        response = handle_request(
            api_event(
                method="PATCH",
                path="/api/v2/expertise/exp_1",
                body=json.dumps({"value": "  Machine Learning "}),
            ),
            self.service,
        )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            response_body(response)["item"],
            {
                "id": "exp_1",
                "faculty_id": "fac_1",
                "value": "Machine Learning",
                "visibility": "PUBLIC",
            },
        )

    def test_patch_detail_returns_not_found_for_unknown_id(self) -> None:
        response = handle_request(
            api_event(
                method="PATCH",
                path="/api/v2/expertise/missing",
                body=json.dumps({"value": "Machine Learning"}),
            ),
            self.service,
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(
            response_body(response)["error"]["code"],
            "EXPERTISE_NOT_FOUND",
        )

    def test_patch_detail_rejects_invalid_body(self) -> None:
        for body in (
            "{invalid",
            json.dumps({}),
            json.dumps({"value": " "}),
            json.dumps({"value": "Machine Learning", "faculty_id": "fac_2"}),
        ):
            with self.subTest(body=body):
                response = handle_request(
                    api_event(
                        method="PATCH",
                        path="/api/v2/expertise/exp_1",
                        body=body,
                    ),
                    self.service,
                )

                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(
                    response_body(response)["error"]["code"],
                    "INVALID_BODY",
                )

    def test_patch_detail_without_connected_dao_returns_not_implemented(self) -> None:
        response = handle_request(
            api_event(
                method="PATCH",
                path="/api/v2/expertise/exp_1",
                body=json.dumps({"value": "Machine Learning"}),
            )
        )

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")

    def test_delete_detail_returns_empty_204(self) -> None:
        response = handle_request(
            api_event(method="DELETE", path="/api/v2/expertise/exp_1"),
            self.service,
        )

        self.assertEqual(response["statusCode"], 204)
        self.assertEqual(response["body"], "")

    def test_delete_detail_returns_not_found_for_unknown_id(self) -> None:
        response = handle_request(
            api_event(method="DELETE", path="/api/v2/expertise/missing"),
            self.service,
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(
            response_body(response)["error"]["code"],
            "EXPERTISE_NOT_FOUND",
        )

    def test_delete_detail_without_connected_dao_returns_not_implemented(self) -> None:
        response = handle_request(
            api_event(method="DELETE", path="/api/v2/expertise/exp_1")
        )

        self.assertEqual(response["statusCode"], 501)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_IMPLEMENTED")

    def test_delete_collection_route_is_not_allowed(self) -> None:
        response = handle_request(
            api_event(method="DELETE", path="/api/v2/expertise"),
            self.service,
        )

        self.assertEqual(response["statusCode"], 405)
        self.assertEqual(response_body(response)["error"]["code"], "METHOD_NOT_ALLOWED")

    def test_create_returns_created_item(self) -> None:
        response = handle_request(
            api_event(
                body=json.dumps({"faculty_id": " fac_1 ", "value": " Data Mining "})
            ),
            self.service,
        )

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(
            response_body(response)["item"],
            {"id": "exp_1", "faculty_id": "fac_1", "value": "Data Mining"},
        )

    def test_create_accepts_base64_encoded_json(self) -> None:
        body = base64.b64encode(
            json.dumps({"faculty_id": "fac_1", "value": "Data Mining"}).encode()
        ).decode()

        response = handle_request(
            api_event(body=body, is_base64_encoded=True),
            self.service,
        )

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(response_body(response)["item"]["value"], "Data Mining")

    def test_invalid_json_returns_bad_request(self) -> None:
        response = handle_request(api_event(body="{invalid"), self.service)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body(response)["error"]["code"], "INVALID_BODY")

    def test_invalid_fields_return_bad_request(self) -> None:
        for body in (
            {"faculty_id": "fac_1"},
            {"faculty_id": "fac_1", "value": "Data Mining", "visibility": "PUBLIC"},
            {"faculty_id": " ", "value": "Data Mining"},
            {"faculty_id": "fac_1", "value": " "},
        ):
            with self.subTest(body=body):
                response = handle_request(api_event(body=json.dumps(body)), self.service)

                self.assertEqual(response["statusCode"], 400)
                self.assertEqual(response_body(response)["error"]["code"], "INVALID_BODY")

    def test_missing_body_returns_bad_request(self) -> None:
        response = handle_request(api_event(), self.service)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body(response)["error"]["code"], "INVALID_BODY")

    def test_unsupported_method_is_not_allowed(self) -> None:
        response = handle_request(api_event(method="DELETE"), self.service)

        self.assertEqual(response["statusCode"], 405)
        self.assertEqual(response_body(response)["error"]["code"], "METHOD_NOT_ALLOWED")

    def test_unknown_path_is_not_found(self) -> None:
        response = handle_request(
            api_event(path="/api/v2/other", body="{}"),
            self.service,
        )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(response_body(response)["error"]["code"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
