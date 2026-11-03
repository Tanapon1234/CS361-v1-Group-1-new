from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlmodel import col, select

from app.v2.models.publication import PublicationEvidence
from app.v3.daos.publication_evidence_dao import PublicationEvidenceDAO
from app.v3.daos.sql.base import SqlDAO


class SqlPublicationEvidenceDAO(SqlDAO, PublicationEvidenceDAO):
    def get_by_id(self, evidence_id: UUID) -> PublicationEvidence | None:
        return self.session.get(PublicationEvidence, evidence_id)

    def list_by_publication(self, publication_id: int) -> Sequence[PublicationEvidence]:
        statement = (
            select(PublicationEvidence)
            .where(PublicationEvidence.publication_id == publication_id)
            .order_by(col(PublicationEvidence.created_at), col(PublicationEvidence.id))
        )
        return self.session.exec(statement).all()

    def add(self, evidence: PublicationEvidence) -> PublicationEvidence:
        return self._add(evidence)

    def update(
        self, evidence: PublicationEvidence, values: Mapping[str, Any]
    ) -> PublicationEvidence:
        return self._update(evidence, values)

    def delete(self, evidence: PublicationEvidence) -> None:
        self._delete(evidence)
