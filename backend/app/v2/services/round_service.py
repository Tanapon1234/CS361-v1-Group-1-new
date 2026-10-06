"""Evaluation rounds, the submissions in a round, and the round report (dashboard)."""

from collections import Counter

from pydantic import ValidationError

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.rubric_dao import RubricDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.round_dto import (
    RoundCreateRequest,
    RoundFields,
    RoundListQuery,
    RoundReportQuery,
    RoundReportResponse,
    RoundReportRow,
    RoundReportSummary,
    RoundResponse,
    RoundSubmissionsQuery,
    RoundUpdateRequest,
)
from app.v2.dtos.submission_dto import SubmissionResponse
from app.v2.models.rubric import RubricVersion
from app.v2.models.submission import EvaluationRound
from app.v2.services.scoring import ZERO, round_score


class RoundService:
    def __init__(
        self,
        round_dao: EvaluationRoundDAO,
        rubric_dao: RubricDAO,
        submission_dao: SubmissionDAO,
    ) -> None:
        self.round_dao = round_dao
        self.rubric_dao = rubric_dao
        self.submission_dao = submission_dao

    def list_rounds(self, query: RoundListQuery) -> PageResponse[RoundResponse]:
        items, total = self.round_dao.find_page(
            is_open=query.is_open, limit=query.limit, offset=query.offset
        )
        return PageResponse(
            items=[RoundResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def create_round(self, data: RoundCreateRequest) -> RoundResponse:
        self._require_usable_version(data.rubric_version_id)
        evaluation_round = self.round_dao.add(EvaluationRound(**data.model_dump()))
        return RoundResponse.model_validate(evaluation_round)

    def get_round(self, round_id: int) -> RoundResponse:
        return RoundResponse.model_validate(self._require_round(round_id))

    def update_round(self, round_id: int, data: RoundUpdateRequest) -> RoundResponse:
        evaluation_round = self._require_round(round_id)
        values = data.model_dump(exclude_unset=True)
        merged = evaluation_round.model_dump(include=set(RoundFields.model_fields)) | values
        try:
            RoundFields.model_validate(merged)
        except ValidationError as exc:
            raise BadRequestError(
                "; ".join(e["msg"].removeprefix("Value error, ") for e in exc.errors())
            ) from exc

        version_id = values.get("rubric_version_id")
        if version_id is not None and version_id != evaluation_round.rubric_version_id:
            if self.round_dao.has_submissions(round_id):
                raise ConflictError("The round already has submissions; its rubric is locked")
            self._require_usable_version(version_id)
        return RoundResponse.model_validate(self.round_dao.update(evaluation_round, values))

    def list_round_submissions(
        self, round_id: int, query: RoundSubmissionsQuery
    ) -> PageResponse[SubmissionResponse]:
        self._require_round(round_id)
        # TODO(auth): dept chair / committee see their department, the faculty sees all
        items, total = self.submission_dao.find_page(
            round_id=round_id,
            lecturer_id=None,
            department_id=query.department_id,
            status=query.status,
            limit=query.limit,
            offset=query.offset,
        )
        return PageResponse(
            items=[SubmissionResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def get_report(self, round_id: int, query: RoundReportQuery) -> RoundReportResponse:
        """Scores of every submission in the round (stored totals, kept up to date)."""
        evaluation_round = self._require_round(round_id)
        version = self.rubric_dao.get_version(evaluation_round.rubric_version_id)
        if version is None:
            raise NotFoundError("Rubric version not found")

        rows = [
            RoundReportRow(
                submission_id=submission.id,
                lecturer_id=lecturer.lecturer_id,
                name_th=lecturer.name_th,
                department_id=submission.department_snapshot,
                status=submission.status,
                teaching_credits=submission.teaching_credits,
                raw_total=submission.raw_total,
                capped_total=submission.capped_total,
                meets_min_teaching_credits=submission.teaching_credits
                >= version.min_teaching_credits,
                meets_min_required=submission.capped_total >= version.min_required,
            )
            for submission, lecturer in self.submission_dao.list_with_lecturer(
                round_id, query.department_id
            )
        ]
        average = (
            round_score(sum((row.capped_total for row in rows), ZERO) / len(rows)) if rows else ZERO
        )
        return RoundReportResponse(
            round=RoundResponse.model_validate(evaluation_round),
            min_required=version.min_required,
            min_teaching_credits=version.min_teaching_credits,
            summary=RoundReportSummary(
                submissions=len(rows),
                by_status=dict(Counter(row.status for row in rows)),
                meeting_min_required=sum(1 for row in rows if row.meets_min_required),
                average_capped_total=average,
            ),
            rows=rows,
        )

    # --- helpers ------------------------------------------------------------------

    def _require_round(self, round_id: int) -> EvaluationRound:
        evaluation_round = self.round_dao.get_by_id(round_id)
        if evaluation_round is None:
            raise NotFoundError("Evaluation round not found")
        return evaluation_round

    def _require_usable_version(self, version_id: int) -> RubricVersion:
        version = self.rubric_dao.get_version(version_id)
        if version is None:
            raise BadRequestError("Rubric version not found")
        if not version.is_active:
            raise BadRequestError("Rubric version is not active")
        return version
