from collections.abc import Sequence
from uuid import UUID

from sqlmodel import col, select

from app.v2.daos.lecturer_work_dao import LecturerWorkDAO, WorkEntryRow
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.publication import FacultyPublication, Publication
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection
from app.v2.models.submission import EvaluationRound, Submission, SubmissionEntry


class SqlLecturerWorkDAO(SqlDAO, LecturerWorkDAO):
    def list_entries(
        self, lecturer_id: UUID, *, academic_year: int | None, category_code: str | None
    ) -> Sequence[WorkEntryRow]:
        statement = (
            select(
                SubmissionEntry,
                RubricItem,
                RubricSection,
                RubricCategory,
                Submission,
                EvaluationRound,
            )
            .join(Submission, Submission.id == SubmissionEntry.submission_id)
            .join(EvaluationRound, EvaluationRound.id == Submission.round_id)
            .join(RubricItem, RubricItem.id == SubmissionEntry.item_id)
            .join(RubricSection, RubricSection.id == RubricItem.section_id)
            .join(RubricCategory, RubricCategory.id == RubricSection.category_id)
            .where(Submission.lecturer_id == lecturer_id)
        )
        if academic_year is not None:
            statement = statement.where(EvaluationRound.academic_year == academic_year)
        if category_code is not None:
            statement = statement.where(RubricCategory.code == category_code)

        statement = statement.order_by(
            col(EvaluationRound.academic_year).desc(),
            col(EvaluationRound.semester).asc().nulls_last(),
            col(RubricCategory.sort_order).asc(),
            col(RubricSection.sort_order).asc(),
            col(SubmissionEntry.sort_order).asc(),
            col(SubmissionEntry.created_at).asc(),
        )
        return [WorkEntryRow(*row) for row in self.session.exec(statement).all()]

    def list_publications(
        self, lecturer_id: UUID, *, publication_year: int | None
    ) -> Sequence[tuple[Publication, int | None]]:
        statement = (
            select(Publication, FacultyPublication.author_order)
            .join(FacultyPublication)
            .where(FacultyPublication.lecturer_id == lecturer_id)
        )
        if publication_year is not None:
            statement = statement.where(Publication.publication_year == publication_year)
        statement = statement.order_by(
            col(Publication.publication_year).desc().nulls_last(),
            col(Publication.title).asc(),
        )
        return self.session.exec(statement).all()

    def list_entry_years(self, lecturer_id: UUID) -> list[int]:
        statement = (
            select(EvaluationRound.academic_year)
            .join(Submission, Submission.round_id == EvaluationRound.id)
            .join(SubmissionEntry, SubmissionEntry.submission_id == Submission.id)
            .where(Submission.lecturer_id == lecturer_id)
            .distinct()
        )
        return list(self.session.exec(statement).all())

    def list_publication_years(self, lecturer_id: UUID) -> list[int]:
        statement = (
            select(Publication.publication_year)
            .join(FacultyPublication)
            .where(
                FacultyPublication.lecturer_id == lecturer_id,
                col(Publication.publication_year).is_not(None),
            )
            .distinct()
        )
        return [year for year in self.session.exec(statement).all() if year is not None]

    def get_category_name(self, code: str) -> str | None:
        statement = (
            select(RubricCategory.name_th)
            .where(RubricCategory.code == code)
            .order_by(col(RubricCategory.version_id).desc())
            .limit(1)
        )
        return self.session.exec(statement).first()
