import unittest

from fakes import FakeClientError, FakeS3Client
from faculty_service import BackendDataError, FacultyNotFoundError, FacultyService
from s3_repository import S3Repository
from validation import InvalidFacultyIdError

BUCKET = "cs361-v1-faculty-data-g1-334177992720-ap-southeast-1-an"


def make_service(objects=None, error=None):
    client = FakeS3Client(objects, error)
    return FacultyService(S3Repository(BUCKET, "serving", client=client)), client


class TestListFaculties(unittest.TestCase):
    def test_success_with_data_envelope(self):
        service, client = make_service({"serving/faculties.json": {"data": [{"id": "eng"}, {"id": "sci"}]}})
        self.assertEqual(len(service.list_faculties()), 2)
        self.assertEqual(client.calls, [(BUCKET, "serving/faculties.json")])

    def test_success_with_bare_array(self):
        service, _ = make_service({"serving/faculties.json": [{"id": "eng"}]})
        self.assertEqual(service.list_faculties(), [{"id": "eng"}])

    def test_empty_list(self):
        service, _ = make_service({"serving/faculties.json": {"data": []}})
        self.assertEqual(service.list_faculties(), [])

    def test_does_not_read_detail_objects(self):
        service, client = make_service({
            "serving/faculties.json": {"data": [{"id": "eng"}, {"id": "sci"}]},
            "serving/faculties/eng.json": {"id": "eng"},
            "serving/faculties/sci.json": {"id": "sci"},
        })
        service.list_faculties()
        self.assertEqual(len(client.calls), 1)

    def test_missing_list_object_is_backend_error(self):
        service, _ = make_service({})
        with self.assertRaises(BackendDataError):
            service.list_faculties()

    def test_invalid_list_json_is_backend_error(self):
        service, _ = make_service({"serving/faculties.json": "[[[not json"})
        with self.assertRaises(BackendDataError):
            service.list_faculties()

    def test_invalid_list_shape_is_backend_error(self):
        service, _ = make_service({"serving/faculties.json": {"data": {"id": "eng"}}})
        with self.assertRaises(BackendDataError):
            service.list_faculties()

    def test_s3_permission_error_is_backend_error(self):
        service, _ = make_service(error=FakeClientError("AccessDenied"))
        with self.assertRaises(BackendDataError):
            service.list_faculties()


class TestFacultyDetail(unittest.TestCase):
    def test_existing_faculty(self):
        service, client = make_service({"serving/faculties/eng.json": {"id": "eng", "name": "Engineering"}})
        self.assertEqual(service.get_faculty("eng"), {"id": "eng", "name": "Engineering"})
        self.assertEqual(client.calls, [(BUCKET, "serving/faculties/eng.json")])

    def test_detail_with_data_envelope_is_unwrapped(self):
        service, _ = make_service({"serving/faculties/eng.json": {"data": {"id": "eng"}}})
        self.assertEqual(service.get_faculty("eng"), {"id": "eng"})

    def test_missing_optional_fields_are_passed_through(self):
        service, _ = make_service({"serving/faculties/eng.json": {"id": "eng"}})
        result = service.get_faculty("eng")
        self.assertEqual(result, {"id": "eng"})
        self.assertNotIn("departments", result)

    def test_unknown_faculty_raises_not_found(self):
        service, _ = make_service({})
        with self.assertRaises(FacultyNotFoundError):
            service.get_faculty("unknown-faculty")

    def test_missing_detail_object_raises_not_found(self):
        service, _ = make_service({"serving/faculties/eng.json": {"data": None}})
        with self.assertRaises(FacultyNotFoundError):
            service.get_faculty("eng")

    def test_invalid_detail_json_is_backend_error(self):
        service, _ = make_service({"serving/faculties/eng.json": "{oops"})
        with self.assertRaises(BackendDataError):
            service.get_faculty("eng")

    def test_invalid_detail_shape_is_backend_error(self):
        service, _ = make_service({"serving/faculties/eng.json": [1, 2, 3]})
        with self.assertRaises(BackendDataError):
            service.get_faculty("eng")

    def test_invalid_id_never_touches_s3(self):
        service, client = make_service({})
        with self.assertRaises(InvalidFacultyIdError):
            service.get_faculty("../source/secret")
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
