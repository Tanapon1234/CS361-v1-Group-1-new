"""Unit tests for lecturer-expertise request DTOs."""

import unittest

from backend.v2.expertise.dto import ExpertiseDTO
from backend.v2.lecturer_expertise.dao import (
    DeferredLecturerExpertiseDao,
    LecturerExpertisePersistencePendingError,
)
from backend.v2.lecturer_expertise.dto import (
    LecturerExpertiseValidationError,
    ReplaceLecturerExpertiseDTO,
)
from backend.v2.lecturer_expertise.service import LecturerExpertiseService


class ReplaceLecturerExpertiseDtoTest(unittest.TestCase):
    def test_trims_expertise_ids(self) -> None:
        dto = ReplaceLecturerExpertiseDTO.from_mapping(
            {"expertiseIds": [" exp_1 ", "exp_2"]}
        )

        self.assertEqual(dto, ReplaceLecturerExpertiseDTO(("exp_1", "exp_2")))

    def test_allows_empty_expertise_ids(self) -> None:
        dto = ReplaceLecturerExpertiseDTO.from_mapping({"expertiseIds": []})

        self.assertEqual(dto, ReplaceLecturerExpertiseDTO(()))

    def test_rejects_missing_or_extra_fields(self) -> None:
        for payload in (
            {},
            {"expertise_ids": ["exp_1"]},
            {"expertiseIds": ["exp_1"], "extra": True},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(LecturerExpertiseValidationError):
                    ReplaceLecturerExpertiseDTO.from_mapping(payload)

    def test_rejects_non_object_payloads(self) -> None:
        for payload in (None, ["exp_1"], "exp_1"):
            with self.subTest(payload=payload):
                with self.assertRaises(LecturerExpertiseValidationError):
                    ReplaceLecturerExpertiseDTO.from_mapping(payload)

    def test_rejects_non_array_or_non_string_ids(self) -> None:
        for expertise_ids in ("exp_1", None, [1], ["exp_1", None], ["  "]):
            with self.subTest(expertise_ids=expertise_ids):
                with self.assertRaises(LecturerExpertiseValidationError):
                    ReplaceLecturerExpertiseDTO.from_mapping(
                        {"expertiseIds": expertise_ids}
                    )

    def test_rejects_duplicate_ids_after_trimming(self) -> None:
        with self.assertRaises(LecturerExpertiseValidationError):
            ReplaceLecturerExpertiseDTO.from_mapping(
                {"expertiseIds": ["exp_1", " exp_1 "]}
            )


class DeferredLecturerExpertiseDaoTest(unittest.TestCase):
    def test_listing_reports_pending_persistence(self) -> None:
        with self.assertRaises(LecturerExpertisePersistencePendingError):
            DeferredLecturerExpertiseDao().list_for_lecturer("fac_1")

    def test_replacement_reports_pending_persistence(self) -> None:
        with self.assertRaises(LecturerExpertisePersistencePendingError):
            DeferredLecturerExpertiseDao().replace_for_lecturer(
                "fac_1",
                ReplaceLecturerExpertiseDTO(("exp_1",)),
            )

    def test_removal_reports_pending_persistence(self) -> None:
        with self.assertRaises(LecturerExpertisePersistencePendingError):
            DeferredLecturerExpertiseDao().remove_for_lecturer("fac_1", "exp_1")


class LecturerExpertiseServiceTest(unittest.TestCase):
    def test_listing_delegates_lecturer_id_to_dao(self) -> None:
        expertise = [ExpertiseDTO("exp_1", "fac_1", "Data Mining", "PUBLIC")]

        class FakeDao:
            def list_for_lecturer(self, lecturer_id: str) -> list[ExpertiseDTO]:
                self.requested_lecturer_id = lecturer_id
                return expertise

        dao = FakeDao()
        result = LecturerExpertiseService(dao).list_for_lecturer("fac_1")

        self.assertEqual(dao.requested_lecturer_id, "fac_1")
        self.assertEqual(result, expertise)

    def test_replacement_delegates_lecturer_id_and_request_to_dao(self) -> None:
        expertise = [ExpertiseDTO("exp_1", "fac_1", "Data Mining", "PUBLIC")]
        request = ReplaceLecturerExpertiseDTO(("exp_1",))

        class FakeDao:
            def replace_for_lecturer(
                self,
                lecturer_id: str,
                replacement: ReplaceLecturerExpertiseDTO,
            ) -> list[ExpertiseDTO]:
                self.requested = (lecturer_id, replacement)
                return expertise

        dao = FakeDao()
        result = LecturerExpertiseService(dao).replace_for_lecturer(
            "fac_1",
            request,
        )

        self.assertEqual(dao.requested, ("fac_1", request))
        self.assertEqual(result, expertise)

    def test_removal_delegates_lecturer_and_expertise_ids_to_dao(self) -> None:
        class FakeDao:
            def remove_for_lecturer(
                self,
                lecturer_id: str,
                expertise_id: str,
            ) -> None:
                self.requested = (lecturer_id, expertise_id)

        dao = FakeDao()
        LecturerExpertiseService(dao).remove_for_lecturer("fac_1", "exp_1")

        self.assertEqual(dao.requested, ("fac_1", "exp_1"))

    def test_deferred_dao_errors_propagate_from_service(self) -> None:
        service = LecturerExpertiseService(DeferredLecturerExpertiseDao())

        with self.assertRaises(LecturerExpertisePersistencePendingError):
            service.list_for_lecturer("fac_1")

        with self.assertRaises(LecturerExpertisePersistencePendingError):
            service.replace_for_lecturer(
                "fac_1",
                ReplaceLecturerExpertiseDTO(()),
            )

        with self.assertRaises(LecturerExpertisePersistencePendingError):
            service.remove_for_lecturer("fac_1", "exp_1")


if __name__ == "__main__":
    unittest.main()
