"""DTO, service, and RDS Data API DAO tests for education creation."""

from __future__ import annotations

import unittest

from backend.v2.lecturer_educations.dao import (
    DataApiEducationDao,
    LecturerNotFoundError,
)
from backend.v2.lecturer_educations.dto import (
    CreateEducationDTO,
    EducationValidationError,
    parse_create_education,
)
from backend.v2.lecturer_educations.service import LecturerEducationService


class FakeEducationDao:
    def __init__(self, result=None):
        self.result = result or {"id": "edu_test", "faculty_id": "fac_demo"}
        self.calls = []

    def create(self, lecturer_id, education):
        self.calls.append((lecturer_id, education))
        return self.result


class ScriptedDataApiClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.committed = False
        self.rolled_back = False

    def begin_transaction(self, **kwargs):
        self.calls.append(("begin", kwargs))
        return {"transactionId": "tx_test"}

    def execute_statement(self, **kwargs):
        self.calls.append(("execute", kwargs))
        return self.responses.pop(0)

    def commit_transaction(self, **kwargs):
        self.calls.append(("commit", kwargs))
        self.committed = True

    def rollback_transaction(self, **kwargs):
        self.calls.append(("rollback", kwargs))
        self.rolled_back = True


def data_api_response(columns, values):
    return {
        "columnMetadata": [{"name": column} for column in columns],
        "records": [[value if isinstance(value, dict) else _data_value(value) for value in values]],
    }


def _data_value(value):
    if value is None:
        return {"isNull": True}
    if isinstance(value, int):
        return {"longValue": value}
    return {"stringValue": value}


class CreateEducationDtoTest(unittest.TestCase):
    def test_parse_trims_text_and_preserves_year(self):
        dto = parse_create_education(
            {
                "degree": "  Ph.D. ",
                "field_of_study": "Computer Science",
                "graduation_year": 2560,
            }
        )

        self.assertEqual(dto.degree, "Ph.D.")
        self.assertEqual(dto.graduation_year, 2560)
        self.assertIsNone(dto.display_order)

    def test_empty_or_non_informative_payload_is_rejected(self):
        for payload in ({}, {"degree": "  "}, {"display_order": 2}):
            with self.subTest(payload=payload), self.assertRaises(EducationValidationError):
                parse_create_education(payload)

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(EducationValidationError) as error:
            parse_create_education({"degree": "Ph.D.", "id": "caller-controlled"})
        self.assertEqual(error.exception.field, "id")

    def test_field_types_and_ranges_are_validated(self):
        invalid_payloads = [
            {"degree": 123},
            {"graduation_year": True},
            {"graduation_year": 0},
            {"graduation_year": 10000},
            {"graduation_year": "2560"},
            {"degree": "Ph.D.", "display_order": -1},
            {"degree": "Ph.D.", "display_order": True},
            {"degree": "Ph.D.", "display_order": None},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload), self.assertRaises(EducationValidationError):
                parse_create_education(payload)


class LecturerEducationServiceTest(unittest.TestCase):
    def test_service_validates_and_delegates(self):
        dao = FakeEducationDao()
        service = LecturerEducationService(dao)

        result = service.create(" fac_demo ", {"degree": "M.Sc."})

        self.assertEqual(result["id"], "edu_test")
        self.assertEqual(dao.calls[0][0], "fac_demo")
        self.assertEqual(
            dao.calls[0][1],
            CreateEducationDTO("M.Sc.", None, None, None, None, None),
        )

    def test_service_rejects_invalid_lecturer_id(self):
        service = LecturerEducationService(FakeEducationDao())

        with self.assertRaises(EducationValidationError):
            service.create("fac_demo'; DROP TABLE faculty;--", {"degree": "M.Sc."})


class DataApiEducationDaoTest(unittest.TestCase):
    def test_create_commits_and_uses_bound_parameters(self):
        client = ScriptedDataApiClient(
            [
                data_api_response(["id"], ["fac_demo"]),
                data_api_response(["display_order"], [2]),
                data_api_response(
                    [
                        "id",
                        "faculty_id",
                        "degree",
                        "field_of_study",
                        "institution",
                        "country",
                        "graduation_year",
                        "display_order",
                        "created_at",
                        "updated_at",
                    ],
                    [
                        "edu_generated",
                        "fac_demo",
                        "Ph.D.",
                        "Computer Science",
                        "Demo University",
                        "Thailand",
                        2560,
                        2,
                        "2026-10-05T00:00:00+00:00",
                        "2026-10-05T00:00:00+00:00",
                    ],
                ),
            ]
        )
        dao = DataApiEducationDao("cluster", "secret", "database", client)

        result = dao.create(
            "fac_demo",
            parse_create_education({"degree": "Ph.D.", "graduation_year": 2560}),
        )

        self.assertEqual(result["display_order"], 2)
        self.assertTrue(client.committed)
        self.assertFalse(client.rolled_back)
        insert_call = [call[1] for call in client.calls if call[0] == "execute"][2]
        self.assertNotIn("Ph.D.", insert_call["sql"])
        self.assertIn(
            {"name": "degree", "value": {"stringValue": "Ph.D."}},
            insert_call["parameters"],
        )
        self.assertEqual(insert_call["transactionId"], "tx_test")

    def test_missing_lecturer_rolls_back_without_inserting(self):
        client = ScriptedDataApiClient([{"columnMetadata": [{"name": "id"}], "records": []}])
        dao = DataApiEducationDao("cluster", "secret", "database", client)

        with self.assertRaises(LecturerNotFoundError):
            dao.create("missing", parse_create_education({"degree": "Ph.D."}))

        self.assertTrue(client.rolled_back)
        self.assertFalse(client.committed)
        self.assertEqual(len([call for call in client.calls if call[0] == "execute"]), 1)

    def test_insert_failure_rolls_back_transaction(self):
        client = ScriptedDataApiClient(
            [
                data_api_response(["id"], ["fac_demo"]),
                data_api_response(["display_order"], [0]),
            ]
        )

        def fail_insert(**kwargs):
            client.calls.append(("execute", kwargs))
            raise RuntimeError("database unavailable")

        client.execute_statement = fail_insert
        dao = DataApiEducationDao("cluster", "secret", "database", client)

        with self.assertRaisesRegex(RuntimeError, "database unavailable"):
            dao.create("fac_demo", parse_create_education({"degree": "Ph.D."}))

        self.assertTrue(client.rolled_back)
        self.assertFalse(client.committed)


if __name__ == "__main__":
    unittest.main()
