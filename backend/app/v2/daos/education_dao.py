from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.education import Education


class EducationDAO(ABC):
    @abstractmethod
    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[Education]: ...

    @abstractmethod
    def get_by_id(self, education_id: int) -> Education | None: ...

    @abstractmethod
    def add(self, education: Education) -> Education: ...

    @abstractmethod
    def update(self, education: Education, values: Mapping[str, Any]) -> Education: ...

    @abstractmethod
    def delete(self, education: Education) -> None: ...
