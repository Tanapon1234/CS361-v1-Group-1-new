from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func
from sqlmodel import col, select

from app.v2.daos.sql.base import SqlDAO
from app.v2.daos.submission_dao import SubmissionDAO, SubmissionEntity
from app.v2.models.enums import SubmissionStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.rubric import RubricItem
from app.v2.models.submission import (
    Submission,
    SubmissionApproval,
    SubmissionCategoryTotal,
    SubmissionEntry,
)


class SqlSubmissionDAO(SqlDAO, SubmissionDAO):
    # --- submission ---

    def get_by_id(self, submission_id: UUID) -> Submission | None:
        return self.session.get(Submission, submission_id)

    def get_by_round_and_lecturer(self, round_id: int, lecturer_id: UUID) -> Submission | None:
        statement = select(Submission).where(
            Submission.round_id == round_id, Submission.lecturer_id == lecturer_id
        )
        return self.session.exec(statement).first()

    def find_page(
        self,
        *,
        round_id: int | None,
        lecturer_id: UUID | None,
        department_id: int | None,
        status: SubmissionStatus | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Submission], int]:
        statement = select(Submission)
        if round_id is not None:
            statement = statement.where(Submission.round_id == round_id)
        if lecturer_id is not None:
            statement = statement.where(Submission.lecturer_id == lecturer_id)
        if department_id is not None:
            statement = statement.where(Submission.department_snapshot == department_id)
        if status is not None:
            statement = statement.where(Submission.status == status)
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = self.session.exec(
            statement.order_by(col(Submission.created_at).desc(), col(Submission.id))
            .offset(offset)
            .limit(limit)
        ).all()
        return items, total

    def list_with_lecturer(
        self, round_id: int, department_id: int | None
    ) -> Sequence[tuple[Submission, Lecturer]]:
        statement = (
            select(Submission, Lecturer)
            .join(Lecturer, col(Lecturer.lecturer_id) == Submission.lecturer_id)
            .where(Submission.round_id == round_id)
        )
        if department_id is not None:
            statement = statement.where(Submission.department_snapshot == department_id)
        return self.session.exec(statement.order_by(col(Lecturer.name_th))).all()

    # --- entries ---

    def get_entry(self, entry_id: UUID) -> SubmissionEntry | None:
        return self.session.get(SubmissionEntry, entry_id)

    def list_entries(
        self, submission_id: UUID, *, section_id: int | None = None
    ) -> Sequence[SubmissionEntry]:
        statement = select(SubmissionEntry).where(SubmissionEntry.submission_id == submission_id)
        if section_id is not None:
            statement = statement.join(
                RubricItem, col(RubricItem.id) == SubmissionEntry.item_id
            ).where(RubricItem.section_id == section_id)
        statement = statement.order_by(
            col(SubmissionEntry.sort_order), col(SubmissionEntry.created_at)
        )
        return self.session.exec(statement).all()

    def count_entries(
        self,
        submission_id: UUID,
        *,
        item_id: int | None = None,
        section_id: int | None = None,
        exclude_entry_id: UUID | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(SubmissionEntry)
            .where(SubmissionEntry.submission_id == submission_id)
        )
        if item_id is not None:
            statement = statement.where(SubmissionEntry.item_id == item_id)
        if section_id is not None:
            statement = statement.join(
                RubricItem, col(RubricItem.id) == SubmissionEntry.item_id
            ).where(RubricItem.section_id == section_id)
        if exclude_entry_id is not None:
            statement = statement.where(SubmissionEntry.id != exclude_entry_id)
        return self.session.exec(statement).one()

    # --- frozen totals ---

    def list_category_totals(self, submission_id: UUID) -> Sequence[SubmissionCategoryTotal]:
        statement = select(SubmissionCategoryTotal).where(
            SubmissionCategoryTotal.submission_id == submission_id
        )
        return self.session.exec(statement).all()

    def replace_category_totals(
        self, submission_id: UUID, totals: Sequence[SubmissionCategoryTotal]
    ) -> None:
        self.session.execute(
            delete(SubmissionCategoryTotal).where(
                col(SubmissionCategoryTotal.submission_id) == submission_id
            )
        )
        self.session.add_all(totals)
        self.session.flush()

    # --- approvals ---

    def list_approvals(self, submission_id: UUID) -> Sequence[SubmissionApproval]:
        statement = (
            select(SubmissionApproval)
            .where(SubmissionApproval.submission_id == submission_id)
            .order_by(col(SubmissionApproval.signed_at), col(SubmissionApproval.id))
        )
        return self.session.exec(statement).all()

    # --- write ---

    def add[T: SubmissionEntity](self, entity: T) -> T:
        return self._add(entity)

    def update[T: SubmissionEntity](self, entity: T, values: Mapping[str, Any]) -> T:
        return self._update(entity, values)

    def delete(self, entity: Submission | SubmissionEntry) -> None:
        self._delete(entity)
