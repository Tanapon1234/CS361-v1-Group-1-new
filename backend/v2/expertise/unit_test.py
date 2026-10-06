"""Unit tests for expertise DTO, service, and deferred DAO."""

import unittest

from backend.v2.expertise.dao import (
    DeferredExpertiseDao,
    ExpertisePersistencePendingError,
)
from backend.v2.expertise.dto import (
    CreateExpertiseDTO,
    ExpertiseDTO,
    ExpertiseValidationError,
    PatchExpertiseDTO,
)
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

    def test_expertise_dto_serializes_list_item(self) -> None:
        dto = ExpertiseDTO("exp_1", "fac_1", "Data Mining", "PUBLIC")

        self.assertEqual(
            dto.to_dict(),
            {
                "id": "exp_1",
                "faculty_id": "fac_1",
                "value": "Data Mining",
                "visibility": "PUBLIC",
            },
        )

    def test_patch_expertise_dto_accepts_value_only_and_trims_it(self) -> None:
        dto = PatchExpertiseDTO.from_mapping({"value": " Machine Learning "})

        self.assertEqual(dto, PatchExpertiseDTO("Machine Learning"))

    def test_patch_expertise_dto_rejects_empty_or_extra_fields(self) -> None:
        for payload in (
            {},
            {"value": " "},
            {"value": "Machine Learning", "faculty_id": "fac_1"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ExpertiseValidationError):
                    PatchExpertiseDTO.from_mapping(payload)


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

    def test_list_all_delegates_to_dao(self) -> None:
        class FakeDao:
            def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
                raise AssertionError("create should not be called")

            def list_all(self) -> list[ExpertiseDTO]:
                return [ExpertiseDTO("exp_1", "fac_1", "Data Mining", "PUBLIC")]

        result = ExpertiseService(FakeDao()).list_all()

        self.assertEqual(
            result,
            [ExpertiseDTO("exp_1", "fac_1", "Data Mining", "PUBLIC")],
        )

    def test_get_by_id_delegates_to_dao(self) -> None:
        class FakeDao:
            def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
                raise AssertionError("create should not be called")

            def list_all(self) -> list[ExpertiseDTO]:
                raise AssertionError("list_all should not be called")

            def get_by_id(self, expertise_id: str) -> ExpertiseDTO:
                self.requested_id = expertise_id
                return ExpertiseDTO(expertise_id, "fac_1", "Data Mining", "PUBLIC")

        dao = FakeDao()
        result = ExpertiseService(dao).get_by_id("exp_1")

        self.assertEqual(dao.requested_id, "exp_1")
        self.assertEqual(result, ExpertiseDTO("exp_1", "fac_1", "Data Mining", "PUBLIC"))

    def test_update_delegates_id_and_dto_to_dao(self) -> None:
        class FakeDao:
            def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
                raise AssertionError("create should not be called")

            def list_all(self) -> list[ExpertiseDTO]:
                raise AssertionError("list_all should not be called")

            def get_by_id(self, expertise_id: str) -> ExpertiseDTO:
                raise AssertionError("get_by_id should not be called")

            def update(
                self,
                expertise_id: str,
                expertise: PatchExpertiseDTO,
            ) -> ExpertiseDTO:
                self.requested = (expertise_id, expertise)
                return ExpertiseDTO(
                    expertise_id,
                    "fac_1",
                    expertise.value,
                    "PUBLIC",
                )

        dao = FakeDao()
        dto = PatchExpertiseDTO("Machine Learning")

        result = ExpertiseService(dao).update("exp_1", dto)

        self.assertEqual(dao.requested, ("exp_1", dto))
        self.assertEqual(
            result,
            ExpertiseDTO("exp_1", "fac_1", "Machine Learning", "PUBLIC"),
        )

    def test_delete_delegates_id_to_dao(self) -> None:
        class FakeDao:
            def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
                raise AssertionError("create should not be called")

            def list_all(self) -> list[ExpertiseDTO]:
                raise AssertionError("list_all should not be called")

            def get_by_id(self, expertise_id: str) -> ExpertiseDTO:
                raise AssertionError("get_by_id should not be called")

            def update(
                self,
                expertise_id: str,
                expertise: PatchExpertiseDTO,
            ) -> ExpertiseDTO:
                raise AssertionError("update should not be called")

            def delete(self, expertise_id: str) -> None:
                self.deleted_id = expertise_id

        dao = FakeDao()
        ExpertiseService(dao).delete("exp_1")

        self.assertEqual(dao.deleted_id, "exp_1")

    def test_deferred_dao_reports_pending_deletion(self) -> None:
        with self.assertRaises(ExpertisePersistencePendingError):
            DeferredExpertiseDao().delete("exp_1")

    def test_deferred_dao_reports_pending_listing(self) -> None:
        with self.assertRaises(ExpertisePersistencePendingError):
            DeferredExpertiseDao().list_all()

    def test_deferred_dao_reports_pending_detail_lookup(self) -> None:
        with self.assertRaises(ExpertisePersistencePendingError):
            DeferredExpertiseDao().get_by_id("exp_1")


if __name__ == "__main__":
    unittest.main()
