from collections.abc import Sequence

from sqlalchemy import func
from sqlmodel import col, select

from app.v2.models.enums import EvidenceStatus, VerificationStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication import FacultyPublication, Publication
from app.v2.models.submission import EntryEvidence, Submission, SubmissionEntry
from app.v3.daos.sql.base import SqlDAO
from app.v3.daos.verification_dao import EvidenceQueueRow, VerificationDAO


class SqlVerificationDAO(SqlDAO, VerificationDAO):
    def find_publications(
        self, status: VerificationStatus, *, limit: int, offset: int
    ) -> tuple[Sequence[Publication], int]:
        statement = select(Publication).where(Publication.verification_status == status)
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = self.session.exec(
            statement.order_by(col(Publication.created_at), col(Publication.publication_id))
            .offset(offset)
            .limit(limit)
        ).all()
        return items, total

    def author_names(self, publication_id: int) -> list[str]:
        statement = (
            select(Lecturer.name_th)
            .join(FacultyPublication, FacultyPublication.lecturer_id == Lecturer.lecturer_id)
            .where(FacultyPublication.publication_id == publication_id)
            .order_by(col(FacultyPublication.author_order).asc().nulls_last())
        )
        return list(self.session.exec(statement).all())

    def find_evidence(
        self, status: VerificationStatus, *, limit: int, offset: int
    ) -> tuple[Sequence[EvidenceQueueRow], int]:
        statement = (
            select(EntryEvidence, SubmissionEntry, Submission, Lecturer)
            .join(SubmissionEntry, SubmissionEntry.id == EntryEvidence.entry_id)
            .join(Submission, Submission.id == SubmissionEntry.submission_id)
            .join(Lecturer, Lecturer.lecturer_id == Submission.lecturer_id)
            .where(
                EntryEvidence.verification_status == status,
                EntryEvidence.status == EvidenceStatus.UPLOADED,
            )
        )
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        rows = self.session.exec(
            statement.order_by(col(EntryEvidence.created_at), col(EntryEvidence.id))
            .offset(offset)
            .limit(limit)
        ).all()
        return [EvidenceQueueRow(*row) for row in rows], total
