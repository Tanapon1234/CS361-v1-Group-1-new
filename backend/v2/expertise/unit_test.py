"""Unit tests for expertise DTO, service, and deferred DAO."""

import unittest

from backend.v2.expertise.dao import (
    DeferredExpertiseDao,
    ExpertisePersistencePendingError,
)
from backend.v2.expertise.dto import CreateExpertiseDTO, ExpertiseValidationError
from backend.v2.expertise.service import ExpertiseService


class CreateExpertiseDtoTest(unittest.TestCase):
    def test_trims_fields(self) -> None:
        dto = CreateExpertiseDTO.from_mapping(
            {"faculty_id": " fac_1 ", "value": " Data Mining "}
        )

        self.assertEqual(dto, CreateExpertiseDTO("fac_1", "Data Mining"))

    def test_rejects_missing_and_extra_fields(self) -> None:
        for payload in (
            {"faculty_id": "fac_1"},
            {"faculty_id": "fac_1", "value": "Data Mining", "visibility": "PUBLIC"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ExpertiseValidationError):
                    CreateExpertiseDTO.from_mapping(payload)

    def test_rejects_empty_fields(self) -> None:
        for payload in (
            {"faculty_id": " ", "value": "Data Mining"},
            {"faculty_id": "fac_1", "value": " "},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ExpertiseValidationError):
                    CreateExpertiseDTO.from_mapping(payload)

    def test_rejects_non_object_payload(self) -> None:
        with self.assertRaises(ExpertiseValidationError):
            CreateExpertiseDTO.from_mapping(["fac_1", "Data Mining"])


class ExpertiseServiceTest(unittest.TestCase):
    def test_create_delegates_to_dao(self) -> None:
        class FakeDao:
            def __init__(self) -> None:
                self.created: CreateExpertiseDTO | None = None

            def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
                self.created = expertise
                return {
                    "id": "exp_1",
                    "faculty_id": expertise.faculty_id,
                    "value": expertise.value,
                }

        dao = FakeDao()
        dto = CreateExpertiseDTO("fac_1", "Data Mining")

        result = ExpertiseService(dao).create(dto)

        self.assertEqual(dao.created, dto)
        self.assertEqual(
            result,
            {"id": "exp_1", "faculty_id": "fac_1", "value": "Data Mining"},
        )

    def test_deferred_dao_reports_pending_persistence(self) -> None:
        with self.assertRaises(ExpertisePersistencePendingError):
            DeferredExpertiseDao().create(
                CreateExpertiseDTO("fac_1", "Data Mining")
            )


if __name__ == "__main__":
    unittest.main()
