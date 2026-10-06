from __future__ import annotations

from typing import Any

from .dao import EducationDao
from .dto import (
    parse_create_education,
    parse_patch_education,
    validate_education_id,
    validate_lecturer_id,
)


class LecturerEducationService:
    def __init__(self, education_dao: EducationDao) -> None:
        self._education_dao = education_dao

    def create(self, lecturer_id: Any, payload: Any) -> dict[str, Any]:
        normalized_lecturer_id = validate_lecturer_id(lecturer_id)
        education = parse_create_education(payload)
        return self._education_dao.create(normalized_lecturer_id, education)

    def list_for_lecturer(self, lecturer_id: Any) -> list[dict[str, Any]]:
        normalized_lecturer_id = validate_lecturer_id(lecturer_id)
        return self._education_dao.list_for_lecturer(normalized_lecturer_id)

    def get_for_lecturer(
        self,
        lecturer_id: Any,
        education_id: Any,
    ) -> dict[str, Any]:
        normalized_lecturer_id = validate_lecturer_id(lecturer_id)
        normalized_education_id = validate_education_id(education_id)
        return self._education_dao.get_for_lecturer(
            normalized_lecturer_id,
            normalized_education_id,
        )

    def update_for_lecturer(
        self,
        lecturer_id: Any,
        education_id: Any,
        payload: Any,
    ) -> dict[str, Any]:
        normalized_lecturer_id = validate_lecturer_id(lecturer_id)
        normalized_education_id = validate_education_id(education_id)
        education = parse_patch_education(payload)
        return self._education_dao.update_for_lecturer(
            normalized_lecturer_id,
            normalized_education_id,
            education,
        )

    def delete_for_lecturer(self, lecturer_id: Any, education_id: Any) -> None:
        normalized_lecturer_id = validate_lecturer_id(lecturer_id)
        normalized_education_id = validate_education_id(education_id)
        self._education_dao.delete_for_lecturer(
            normalized_lecturer_id,
            normalized_education_id,
        )
