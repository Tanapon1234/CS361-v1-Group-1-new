import json
import os
import unittest

from fakes import FakeClientError, FakeS3Client, api_event, http_api_event

import handler
from faculty_service import FacultyService
from s3_repository import S3Repository

BUCKET = "cs361-v1-faculty-data-g1-334177992720-ap-southeast-1-an"


def install_service(objects=None, error=None):
    client = FakeS3Client(objects, error)
    handler.set_service(FacultyService(S3Repository(BUCKET, "serving", client=client)))
    return client


def body_of(response):
    return json.loads(response["body"])


class HandlerTestCase(unittest.TestCase):
    def tearDown(self):
        handler.reset_service()


class TestListEndpoint(HandlerTestCase):
    def test_success(self):
        install_service({"serving/faculties.json": {"data": [{"id": "eng"}]}})
        response = handler.lambda_handler(api_event("/api/v1/faculties"))
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body_of(response), {"data": [{"id": "eng"}]})
        self.assertIn("application/json", response["headers"]["Content-Type"])

    def test_empty_list(self):
        install_service({"serving/faculties.json": {"data": []}})
        response = handler.lambda_handler(api_event("/api/v1/faculties"))
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body_of(response), {"data": []})

    def test_missing_list_object_returns_500(self):
        install_service({})
        response = handler.lambda_handler(api_event("/api/v1/faculties"))
        self.assertEqual(response["statusCode"], 500)
        self.assertEqual(body_of(response)["error"]["code"], "INTERNAL_ERROR")

    def test_invalid_list_json_returns_500(self):
        install_service({"serving/faculties.json": "not-json"})
        self.assertEqual(handler.lambda_handler(api_event("/api/v1/faculties"))["statusCode"], 500)

    def test_s3_permission_error_returns_500(self):
        install_service(error=FakeClientError("AccessDenied"))
        response = handler.lambda_handler(api_event("/api/v1/faculties"))
        self.assertEqual(response["statusCode"], 500)
        self.assertNotIn("AccessDenied", response["body"])

    def test_trailing_slash_is_accepted(self):
        install_service({"serving/faculties.json": []})
        self.assertEqual(handler.lambda_handler(api_event("/api/v1/faculties/"))["statusCode"], 200)

    def test_http_api_payload_v2(self):
        install_service({"serving/faculties.json": {"data": []}})
        response = handler.lambda_handler(http_api_event("/api/v1/faculties"))
        self.assertEqual(response["statusCode"], 200)

    def test_stage_prefixed_path(self):
        install_service({"serving/faculties.json": {"data": []}})
        event = api_event("/dev/api/v1/faculties", stage="dev")
        self.assertEqual(handler.lambda_handler(event)["statusCode"], 200)


class TestDetailEndpoint(HandlerTestCase):
    def test_existing_faculty(self):
        install_service({"serving/faculties/eng.json": {"id": "eng", "name": "Engineering"}})
        event = api_event("/api/v1/faculties/eng", path_parameters={"id": "eng"})
        response = handler.lambda_handler(event)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body_of(response), {"data": {"id": "eng", "name": "Engineering"}})

    def test_unknown_faculty_returns_404(self):
        install_service({})
        event = api_event("/api/v1/faculties/nope", path_parameters={"id": "nope"})
        response = handler.lambda_handler(event)
        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(body_of(response)["error"]["code"], "FACULTY_NOT_FOUND")

    def test_missing_detail_object_returns_404(self):
        install_service({"serving/faculties/eng.json": {"data": None}})
        event = api_event("/api/v1/faculties/eng", path_parameters={"id": "eng"})
        self.assertEqual(handler.lambda_handler(event)["statusCode"], 404)

    def test_invalid_detail_json_returns_500(self):
        install_service({"serving/faculties/eng.json": "<html>"})
        event = api_event("/api/v1/faculties/eng", path_parameters={"id": "eng"})
        self.assertEqual(handler.lambda_handler(event)["statusCode"], 500)

    def test_invalid_id_returns_400(self):
        client = install_service({})
        event = api_event("/api/v1/faculties/Eng_01", path_parameters={"id": "Eng_01"})
        response = handler.lambda_handler(event)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(body_of(response)["error"]["code"], "INVALID_FACULTY_ID")
        self.assertEqual(client.calls, [])

    def test_missing_optional_data_still_returns_200(self):
        install_service({"serving/faculties/eng.json": {"id": "eng"}})
        event = api_event("/api/v1/faculties/eng", path_parameters={"id": "eng"})
        response = handler.lambda_handler(event)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body_of(response)["data"], {"id": "eng"})

    def test_id_taken_from_path_when_path_parameters_absent(self):
        install_service({"serving/faculties/sci.json": {"id": "sci"}})
        response = handler.lambda_handler(api_event("/api/v1/faculties/sci"))
        self.assertEqual(response["statusCode"], 200)


class TestRoutingAndMethods(HandlerTestCase):
    def test_unsupported_method_on_list(self):
        install_service({"serving/faculties.json": []})
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                response = handler.lambda_handler(api_event("/api/v1/faculties", method=method))
                self.assertEqual(response["statusCode"], 405)
                self.assertEqual(body_of(response)["error"]["code"], "METHOD_NOT_ALLOWED")
                self.assertEqual(response["headers"]["Allow"], "GET")

    def test_unsupported_method_on_detail_does_not_touch_s3(self):
        client = install_service({"serving/faculties/eng.json": {"id": "eng"}})
        event = api_event("/api/v1/faculties/eng", method="DELETE", path_parameters={"id": "eng"})
        self.assertEqual(handler.lambda_handler(event)["statusCode"], 405)
        self.assertEqual(client.calls, [])

    def test_unknown_route_returns_404(self):
        install_service({})
        response = handler.lambda_handler(api_event("/api/v1/other"))
        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(body_of(response)["error"]["code"], "ROUTE_NOT_FOUND")

    def test_empty_event_returns_404(self):
        install_service({})
        self.assertEqual(handler.lambda_handler({})["statusCode"], 404)


class TestConfiguration(HandlerTestCase):
    def test_missing_bucket_env_returns_500(self):
        handler.reset_service()
        original = os.environ.pop("DATA_BUCKET_NAME", None)
        try:
            response = handler.lambda_handler(api_event("/api/v1/faculties"))
            self.assertEqual(response["statusCode"], 500)
        finally:
            if original is not None:
                os.environ["DATA_BUCKET_NAME"] = original

    def test_build_service_uses_env(self):
        handler.reset_service()
        os.environ["DATA_BUCKET_NAME"] = BUCKET
        os.environ["SERVING_PREFIX"] = "serving"
        service = handler.build_service()
        self.assertEqual(service._repository.bucket, BUCKET)
        self.assertEqual(service._repository.prefix, "serving")


if __name__ == "__main__":
    unittest.main()
