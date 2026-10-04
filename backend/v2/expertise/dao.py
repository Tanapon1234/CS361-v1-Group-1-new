"""Persistence boundary for expertise records."""

from __future__ import annotations

from typing import Protocol

from .dto import CreateExpertiseDTO, ExpertiseDTO


class ExpertisePersistencePendingError(Exception):
    """Raised until expertise persistence is connected."""


class ExpertiseDao(Protocol):
    def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
        """Persist one expertise record."""

    def list_all(self) -> list[ExpertiseDTO]:
        """Return all expertise records."""


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
