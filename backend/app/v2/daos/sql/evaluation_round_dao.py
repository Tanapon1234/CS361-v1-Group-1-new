from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import exists, func
from sqlmodel import col, select

from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.submission import EvaluationRound, Submission


class SqlEvaluationRoundDAO(SqlDAO, EvaluationRoundDAO):
    def get_by_id(self, round_id: int) -> EvaluationRound | None:
        return self.session.get(EvaluationRound, round_id)

    def find_page(
        self, *, is_open: bool | None, limit: int, offset: int
    ) -> tuple[Sequence[EvaluationRound], int]:
        statement = select(EvaluationRound)
        if is_open is not None:
            statement = statement.where(EvaluationRound.is_open == is_open)
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = self.session.exec(
            statement.order_by(
                col(EvaluationRound.period_start).desc(), col(EvaluationRound.id).desc()
            )
            .offset(offset)
            .limit(limit)
        ).all()
        return items, total

    def has_submissions(self, round_id: int) -> bool:
        return bool(
            self.session.exec(select(exists().where(Submission.round_id == round_id))).one()
        )

    def add(self, evaluation_round: EvaluationRound) -> EvaluationRound:
        return self._add(evaluation_round)

    def update(
        self, evaluation_round: EvaluationRound, values: Mapping[str, Any]
    ) -> EvaluationRound:
        return self._update(evaluation_round, values)
