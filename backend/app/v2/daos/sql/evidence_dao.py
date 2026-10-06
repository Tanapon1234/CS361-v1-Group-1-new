from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlmodel import col, select

from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.submission import EntryEvidence, SubmissionEntry


class SqlEvidenceDAO(SqlDAO, EvidenceDAO):
    def get_by_id(self, evidence_id: UUID) -> EntryEvidence | None:
        return self.session.get(EntryEvidence, evidence_id)

    def list_by_entry(self, entry_id: UUID) -> Sequence[EntryEvidence]:
        statement = (
            select(EntryEvidence)
            .where(EntryEvidence.entry_id == entry_id)
            .order_by(col(EntryEvidence.created_at), col(EntryEvidence.id))
        )
        return self.session.exec(statement).all()

    def list_by_submission(self, submission_id: UUID) -> Sequence[EntryEvidence]:
        statement = (
            select(EntryEvidence)
            .join(SubmissionEntry, col(SubmissionEntry.id) == EntryEvidence.entry_id)
            .where(SubmissionEntry.submission_id == submission_id)
        )
        return self.session.exec(statement).all()

    def add(self, evidence: EntryEvidence) -> EntryEvidence:
        return self._add(evidence)

    def update(self, evidence: EntryEvidence, values: Mapping[str, Any]) -> EntryEvidence:
        return self._update(evidence, values)

    def delete(self, evidence: EntryEvidence) -> None:
        self._delete(evidence)
