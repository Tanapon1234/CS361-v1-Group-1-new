from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.v2.models.audit_log import AuditLog


class AuditLogDAO(ABC):
    @abstractmethod
    def find_page(
        self,
        *,
        entity: str | None,
        entity_id: str | None,
        actor_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[AuditLog], int]:
        """Newest first."""
