import json
import os
import re
import unittest

from fakes import FakeS3Client, api_event

import handler
from faculty_service import FacultyService
from s3_repository import S3Repository

BUCKET = "cs361-v1-faculty-data-g1-334177992720-ap-southeast-1-an"
LAMBDA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","lambda"))
SOURCE_FILES = ["handler.py", "faculty_service.py", "s3_repository.py", "validation.py", "responses.py"]

MUTATION_PATTERNS = [
    r"put_object", r"delete_object", r"delete_objects", r"copy_object",
    r"upload_file", r"upload_fileobj", r"create_multipart_upload",
    r"put_bucket", r"put_object_acl", r"restore_object", r"write_get_object_response",
]


def install_service(objects=None):
    client = FakeS3Client(objects or {})
    handler.set_service(FacultyService(S3Repository(BUCKET, "serving", client=client)))
    return client


class TestPathTraversal(unittest.TestCase):
    def tearDown(self):
        handler.reset_service()

    def test_traversal_ids_are_rejected_before_s3(self):
        malicious = [
            "../",
            "..",
            "../../source/faculties",
            "..%2f..%2fsource",
            "%2e%2e%2f",
            "eng/../../source",
            "eng\\..\\source",
            "/etc/passwd",
            "source/private",
            "faculties.json",
            "",
            "\x00",
        ]
        for value in malicious:
            with self.subTest(value=repr(value)):
                client = install_service({})
                event = api_event("/api/v1/faculties/x", path_parameters={"id": value})
                response = handler.lambda_handler(event)
                self.assertIn(response["statusCode"], (400, 404))
                if response["statusCode"] == 400:
                    self.assertEqual(json.loads(response["body"])["error"]["code"], "INVALID_FACULTY_ID")
                self.assertEqual(client.calls, [], f"S3 was called for {value!r}")

    def test_source_prefix_is_never_reachable(self):
        client = install_service({"serving/faculties/eng.json": {"id": "eng"}})
        handler.lambda_handler(api_event("/api/v1/faculties/eng", path_parameters={"id": "eng"}))
        for _, key in client.calls:
            self.assertTrue(key.startswith("serving/"), key)
            self.assertNotIn("source/", key)
            self.assertNotIn("..", key)


class TestNoWriteCodePath(unittest.TestCase):
    def test_no_mutating_s3_calls_in_source(self):
        for filename in SOURCE_FILES:
            path = os.path.join(LAMBDA_DIR, filename)
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            for pattern in MUTATION_PATTERNS:
                with self.subTest(file=filename, pattern=pattern):
                    self.assertIsNone(re.search(pattern, source), f"{pattern} found in {filename}")

    def test_only_get_object_is_used(self):
        with open(os.path.join(LAMBDA_DIR, "s3_repository.py"), encoding="utf-8") as handle:
            source = handle.read()
        used = set(re.findall(r"client\.([a-z_]+)\(", source))
        self.assertEqual(used, {"get_object"})

    def test_no_mutation_route_exists(self):
        install_service({"serving/faculties.json": []})
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            for path in ("/api/v1/faculties", "/api/v1/faculties/eng"):
                with self.subTest(method=method, path=path):
                    response = handler.lambda_handler(api_event(path, method=method))
                    self.assertIn(response["statusCode"], (404, 405))
        handler.reset_service()


class TestResponseLeakage(unittest.TestCase):
    def tearDown(self):
        handler.reset_service()

    def test_error_responses_expose_no_internal_details(self):
        install_service({})
        response = handler.lambda_handler(api_event("/api/v1/faculties"))
        body = response["body"]
        for leak in ("Traceback", "boto", "Bucket", BUCKET, "serving/", "NoSuchKey"):
            self.assertNotIn(leak, body)

    def test_success_response_contains_no_s3_metadata(self):
        install_service({"serving/faculties.json": {"data": [{"id": "eng"}]}})
        body = json.loads(handler.lambda_handler(api_event("/api/v1/faculties"))["body"])
        self.assertEqual(set(body.keys()), {"data"})


if __name__ == "__main__":
    unittest.main()
