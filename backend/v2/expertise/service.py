"""Business logic for expertise endpoints."""

from __future__ import annotations

from .dao import ExpertiseDao
from .dto import CreateExpertiseDTO, ExpertiseDTO


class ExpertiseService:
    def __init__(self, dao: ExpertiseDao) -> None:
        self._dao = dao

    def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
        return self._dao.create(expertise)

    def list_all(self) -> list[ExpertiseDTO]:
        return self._dao.list_all()

    def get_by_id(self, expertise_id: str) -> ExpertiseDTO:
        return self._dao.get_by_id(expertise_id)
