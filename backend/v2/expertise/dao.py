"""Persistence boundary for expertise records."""

from __future__ import annotations

from typing import Protocol

from .dto import CreateExpertiseDTO, ExpertiseDTO, PatchExpertiseDTO


class ExpertisePersistencePendingError(Exception):
    """Raised until expertise persistence is connected."""


class ExpertiseNotFoundError(Exception):
    """Requested expertise record does not exist."""


class ExpertiseDao(Protocol):
    def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
        """Persist one expertise record."""

    def list_all(self) -> list[ExpertiseDTO]:
        """Return all expertise records."""

    def get_by_id(self, expertise_id: str) -> ExpertiseDTO:
        """Return one expertise record by its identifier."""

    def update(self, expertise_id: str, expertise: PatchExpertiseDTO) -> ExpertiseDTO:
        """Update an expertise record by its identifier."""

    def delete(self, expertise_id: str) -> None:
        """Delete an expertise record by its identifier."""


class DeferredExpertiseDao:
    """Placeholder persistence implementation for the unconnected endpoint."""

    def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
        del expertise
        raise ExpertisePersistencePendingError(
            "Expertise persistence is not connected yet"
        )

    def list_all(self) -> list[ExpertiseDTO]:
        raise ExpertisePersistencePendingError(
            "Expertise listing is not connected yet"
        )

    def get_by_id(self, expertise_id: str) -> ExpertiseDTO:
        del expertise_id
        raise ExpertisePersistencePendingError(
            "Expertise detail lookup is not connected yet"
        )

    def update(self, expertise_id: str, expertise: PatchExpertiseDTO) -> ExpertiseDTO:
        del expertise_id, expertise
        raise ExpertisePersistencePendingError(
            "Expertise updates are not connected yet"
        )

    def delete(self, expertise_id: str) -> None:
        del expertise_id
        raise ExpertisePersistencePendingError(
            "Expertise deletion is not connected yet"
        )
