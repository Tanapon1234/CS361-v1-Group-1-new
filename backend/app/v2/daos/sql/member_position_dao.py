from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import or_
from sqlmodel import col, select

from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.enums import PositionCode
from app.v2.models.member_position import MemberPosition


class SqlMemberPositionDAO(SqlDAO, MemberPositionDAO):
    def get_by_id(self, position_id: UUID) -> MemberPosition | None:
        return self.session.get(MemberPosition, position_id)

    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[MemberPosition]:
        statement = (
            select(MemberPosition)
            .where(MemberPosition.lecturer_id == lecturer_id)
            .order_by(col(MemberPosition.start_date).desc(), col(MemberPosition.position))
        )
        return self.session.exec(statement).all()

    def list_active(self, lecturer_id: UUID, on: date) -> Sequence[MemberPosition]:
        statement = select(MemberPosition).where(
            MemberPosition.lecturer_id == lecturer_id,
            MemberPosition.start_date <= on,
            or_(col(MemberPosition.end_date).is_(None), col(MemberPosition.end_date) > on),
        )
        return self.session.exec(statement.order_by(col(MemberPosition.position))).all()

    def find_overlapping(
        self,
        *,
        lecturer_id: UUID,
        position: PositionCode,
        start_date: date,
        end_date: date | None,
        exclude_id: UUID | None = None,
    ) -> MemberPosition | None:
        # [start, end) overlaps [other.start, other.end) when each starts before the other ends
        statement = select(MemberPosition).where(
            MemberPosition.lecturer_id == lecturer_id,
            MemberPosition.position == position,
            or_(col(MemberPosition.end_date).is_(None), col(MemberPosition.end_date) > start_date),
        )
        if end_date is not None:
            statement = statement.where(MemberPosition.start_date < end_date)
        if exclude_id is not None:
            statement = statement.where(MemberPosition.id != exclude_id)
        return self.session.exec(statement).first()

    def add(self, position: MemberPosition) -> MemberPosition:
        return self._add(position)

    def update(self, position: MemberPosition, values: Mapping[str, Any]) -> MemberPosition:
        return self._update(position, values)

    def delete(self, position: MemberPosition) -> None:
        self._delete(position)
