from __future__ import annotations

from typing import Any

from .dao import EducationDao
from .dto import parse_create_education, validate_lecturer_id


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
