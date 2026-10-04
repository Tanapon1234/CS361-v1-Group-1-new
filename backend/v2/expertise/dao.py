"""Persistence boundary for expertise records."""

from __future__ import annotations

from typing import Protocol

from .dto import CreateExpertiseDTO


class ExpertisePersistencePendingError(Exception):
    """Raised until expertise persistence is connected."""


class ExpertiseDao(Protocol):
    def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
        """Persist one expertise record."""


class DeferredExpertiseDao:
    """Placeholder persistence implementation for the unconnected endpoint."""

    def create(self, expertise: CreateExpertiseDTO) -> dict[str, str]:
        del expertise
        raise ExpertisePersistencePendingError(
            "Expertise persistence is not connected yet"
        )
