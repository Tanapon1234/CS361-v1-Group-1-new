"""Persistence boundary for lecturer-expertise mappings."""

from __future__ import annotations

from typing import Protocol

from backend.v2.expertise.dto import ExpertiseDTO

from .dto import ReplaceLecturerExpertiseDTO


class LecturerExpertisePersistencePendingError(Exception):
    """Raised until lecturer-expertise persistence is connected."""


class LecturerExpertiseDao(Protocol):
    def list_for_lecturer(self, lecturer_id: str) -> list[ExpertiseDTO]:
        """Return the expertise assigned to one lecturer."""

    def replace_for_lecturer(
        self,
        lecturer_id: str,
        expertise: ReplaceLecturerExpertiseDTO,
    ) -> list[ExpertiseDTO]:
        """Replace all expertise assignments for one lecturer."""

    def remove_for_lecturer(self, lecturer_id: str, expertise_id: str) -> None:
        """Remove one expertise assignment from a lecturer."""


class DeferredLecturerExpertiseDao:
    """Placeholder persistence implementation for unconnected mapping routes."""

    def list_for_lecturer(self, lecturer_id: str) -> list[ExpertiseDTO]:
        del lecturer_id
        raise LecturerExpertisePersistencePendingError(
            "Lecturer expertise listing is not connected yet"
        )

    def replace_for_lecturer(
        self,
        lecturer_id: str,
        expertise: ReplaceLecturerExpertiseDTO,
    ) -> list[ExpertiseDTO]:
        del lecturer_id, expertise
        raise LecturerExpertisePersistencePendingError(
            "Lecturer expertise replacement is not connected yet"
        )

    def remove_for_lecturer(self, lecturer_id: str, expertise_id: str) -> None:
        del lecturer_id, expertise_id
        raise LecturerExpertisePersistencePendingError(
            "Lecturer expertise removal is not connected yet"
        )
