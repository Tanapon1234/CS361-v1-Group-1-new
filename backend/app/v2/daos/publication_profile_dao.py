from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.publication_profile import PublicationProfile


class PublicationProfileDAO(ABC):
    @abstractmethod
    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[PublicationProfile]: ...

    @abstractmethod
    def get_by_id(self, publication_profile_id: int) -> PublicationProfile | None: ...

    @abstractmethod
    def add(self, profile: PublicationProfile) -> PublicationProfile: ...

    @abstractmethod
    def update(
        self, profile: PublicationProfile, values: Mapping[str, Any]
    ) -> PublicationProfile: ...

    @abstractmethod
    def delete(self, profile: PublicationProfile) -> None: ...
