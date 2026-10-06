"""Keeps stored scores in step with the data: entry.score / weight_applied, the
submission's raw_total / capped_total / teaching_credits, and (once sent) the frozen
submission_category_total rows. Shared by the entry, approval and assessment services.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.v2.daos.assessment_dao import AssessmentDAO
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.rubric_dao import RubricDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection, RubricVersion
from app.v2.models.submission import Submission, SubmissionCategoryTotal, SubmissionEntry
from app.v2.services.scoring import (
    EntryScore,
    ScoredEntry,
    Totals,
    compute_totals,
    needs_assessment,
    score_entry,
)


@dataclass(frozen=True, slots=True)
class Rubric:
    """The rubric version a submission is scored with (the one of its round)."""

    version: RubricVersion
    categories: Sequence[RubricCategory]
    sections: Sequence[RubricSection]
    items: dict[int, RubricItem]


class ScoreKeeper:
    def __init__(
        self,
        rubric_dao: RubricDAO,
        round_dao: EvaluationRoundDAO,
        submission_dao: SubmissionDAO,
        assessment_dao: AssessmentDAO,
    ) -> None:
        self.rubric_dao = rubric_dao
        self.round_dao = round_dao
        self.submission_dao = submission_dao
        self.assessment_dao = assessment_dao

    def rubric_of(self, submission: Submission) -> Rubric:
        evaluation_round = self.round_dao.get_by_id(submission.round_id)
        if evaluation_round is None:
            raise NotFoundError("Evaluation round not found")
        version = self.rubric_dao.get_version(evaluation_round.rubric_version_id)
        if version is None:
            raise NotFoundError("Rubric version not found")
        return Rubric(
            version=version,
            categories=self.rubric_dao.list_categories(version.id),
            sections=self.rubric_dao.list_sections_of_version(version.id),
            items={item.id: item for item in self.rubric_dao.list_items_of_version(version.id)},
        )

    def score(self, entry: SubmissionEntry, item: RubricItem, rubric: Rubric) -> EntryScore:
        values = []
        if needs_assessment(item) and entry.id is not None:
            values = [a.value_given for a in self.assessment_dao.list_by_entry(entry.id)]
        return score_entry(
            item=item,
            quantity=entry.quantity,
            participation_pct=entry.participation_pct,
            base_points=rubric.version.base_points,
            assessed_values=values,
        )

    def rescore_entry(self, entry: SubmissionEntry, rubric: Rubric) -> SubmissionEntry:
        result = self.score(entry, rubric.items[entry.item_id], rubric)
        if (entry.weight_applied, entry.score) == (result.weight_applied, result.score):
            return entry
        return self.submission_dao.update(
            entry, {"weight_applied": result.weight_applied, "score": result.score}
        )

    def totals(self, submission: Submission, rubric: Rubric) -> Totals:
        entries = self.submission_dao.list_entries(submission.id)
        return compute_totals(
            categories=rubric.categories,
            sections=rubric.sections,
            entries=[
                ScoredEntry(item=rubric.items[e.item_id], score=e.score, credits=e.credits)
                for e in entries
            ],
            overall_cap=rubric.version.overall_cap,
        )

    def pending_assessments(self, submission_id: UUID, rubric: Rubric) -> int:
        entries = [
            e
            for e in self.submission_dao.list_entries(submission_id)
            if needs_assessment(rubric.items[e.item_id])
        ]
        assessed = {
            a.entry_id for a in self.assessment_dao.list_by_entries([e.id for e in entries])
        }
        return sum(1 for e in entries if e.id not in assessed)

    def refresh(self, submission: Submission, rubric: Rubric, *, freeze: bool) -> Totals:
        """Store the submission's totals; `freeze` also rewrites submission_category_total."""
        totals = self.totals(submission, rubric)
        self.submission_dao.update(
            submission,
            {
                "raw_total": totals.raw_total,
                "capped_total": totals.capped_total,
                "teaching_credits": totals.teaching_credits,
            },
        )
        if freeze:
            self.submission_dao.replace_category_totals(
                submission.id,
                [
                    SubmissionCategoryTotal(
                        submission_id=submission.id,
                        category_id=category_id,
                        raw_score=raw,
                        capped_score=capped,
                    )
                    for category_id, (raw, capped) in totals.categories.items()
                ],
            )
        return totals
