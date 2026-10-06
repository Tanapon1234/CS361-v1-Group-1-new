"""Business logic for lecturer-expertise mapping endpoints."""

from __future__ import annotations

from backend.v2.expertise.dto import ExpertiseDTO

from .dao import LecturerExpertiseDao
from .dto import ReplaceLecturerExpertiseDTO


class LecturerExpertiseService:
    def __init__(self, dao: LecturerExpertiseDao) -> None:
        self._dao = dao

    def list_for_lecturer(self, lecturer_id: str) -> list[ExpertiseDTO]:
        return self._dao.list_for_lecturer(lecturer_id)

    def replace_for_lecturer(
        self,
        lecturer_id: str,
        expertise: ReplaceLecturerExpertiseDTO,
    ) -> list[ExpertiseDTO]:
        return self._dao.replace_for_lecturer(lecturer_id, expertise)

    def remove_for_lecturer(self, lecturer_id: str, expertise_id: str) -> None:
        self._dao.remove_for_lecturer(lecturer_id, expertise_id)
