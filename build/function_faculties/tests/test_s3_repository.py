import unittest

from fakes import FakeClientError, FakeS3Client
from s3_repository import (
    InvalidJsonError,
    ObjectAccessError,
    ObjectNotFoundError,
    S3Repository,
)

BUCKET = "cs361-v1-faculty-data-g1-334177992720-ap-southeast-1-an"


class TestKeyBuilding(unittest.TestCase):
    def setUp(self):
        self.repo = S3Repository(BUCKET, "serving", client=FakeS3Client())

    def test_keys_are_prefixed_with_serving(self):
        self.assertEqual(self.repo.build_key("faculties.json"), "serving/faculties.json")
        self.assertEqual(self.repo.build_key("faculties/eng.json"), "serving/faculties/eng.json")

    def test_rejects_escape_attempts(self):
        for relative in ("../source/private.json", "/absolute.json", "a\\b.json", "", "..", "a//b.json"):
            with self.subTest(relative=relative):
                with self.assertRaises(ObjectAccessError):
                    self.repo.build_key(relative)

    def test_bucket_is_required(self):
        with self.assertRaises(ValueError):
            S3Repository("", "serving")


class TestGetJson(unittest.TestCase):
    def test_reads_and_parses_json(self):
        client = FakeS3Client({"serving/faculties.json": {"data": [{"id": "eng"}]}})
        repo = S3Repository(BUCKET, "serving", client=client)
        self.assertEqual(repo.get_json("faculties.json"), {"data": [{"id": "eng"}]})
        self.assertEqual(client.calls, [(BUCKET, "serving/faculties.json")])

    def test_missing_object_raises_not_found(self):
        repo = S3Repository(BUCKET, "serving", client=FakeS3Client({}))
        with self.assertRaises(ObjectNotFoundError):
            repo.get_json("faculties.json")

    def test_invalid_json_raises(self):
        client = FakeS3Client({"serving/faculties.json": "{not json"})
        repo = S3Repository(BUCKET, "serving", client=client)
        with self.assertRaises(InvalidJsonError):
            repo.get_json("faculties.json")

    def test_access_denied_raises_access_error(self):
        client = FakeS3Client(error=FakeClientError("AccessDenied"))
        repo = S3Repository(BUCKET, "serving", client=client)
        with self.assertRaises(ObjectAccessError):
            repo.get_json("faculties.json")

    def test_service_error_raises_access_error(self):
        client = FakeS3Client(error=FakeClientError("InternalError"))
        repo = S3Repository(BUCKET, "serving", client=client)
        with self.assertRaises(ObjectAccessError):
            repo.get_json("faculties.json")

    def test_repository_exposes_no_mutating_methods(self):
        repo = S3Repository(BUCKET, "serving", client=FakeS3Client())
        for name in ("put_json", "put_object", "delete_object", "write", "save", "upload"):
            self.assertFalse(hasattr(repo, name), name)


if __name__ == "__main__":
    unittest.main()
