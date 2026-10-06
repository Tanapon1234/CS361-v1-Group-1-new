"""Lines of a submission (submission_entry). The server always computes `score`; the
client never sends it, so the formula lives in one place (app/v2/services/scoring.py).
"""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    PreconditionFailedError,
    UnauthorizedError,
)
from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.rubric_dao import RubricDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.submission_dto import (
    EntryCreateRequest,
    EntryListQuery,
    EntryResponse,
    EntryUpdateRequest,
    entry_etag,
)
from app.v2.models.rubric import RubricItem
from app.v2.models.submission import Submission, SubmissionEntry
from app.v2.services.score_keeper import Rubric, ScoreKeeper
from app.v2.services.scoring import ENTRY_COLUMNS, validate_entry
from app.v2.services.workflow import EDITABLE_STATUSES
from app.v2.storage.object_storage import ObjectStorage


class EntryService:
    def __init__(
        self,
        submission_dao: SubmissionDAO,
        rubric_dao: RubricDAO,
        lecturer_dao: LecturerDAO,
        evidence_dao: EvidenceDAO,
        storage: ObjectStorage,
        score_keeper: ScoreKeeper,
    ) -> None:
        self.submission_dao = submission_dao
        self.rubric_dao = rubric_dao
        self.lecturer_dao = lecturer_dao
        self.evidence_dao = evidence_dao
        self.storage = storage
        self.score_keeper = score_keeper

    def list_entries(
        self, submission_id: UUID, query: EntryListQuery
    ) -> ListResponse[EntryResponse]:
        submission = self._require_submission(submission_id)
        section_id = None
        if query.section is not None:
            version_id = self.score_keeper.rubric_of(submission).version.id
            section = self.rubric_dao.get_section_by_code(version_id, query.section)
            if section is None:
                raise BadRequestError(f"Section {query.section} is not in this rubric")
            section_id = section.id
        items = [
            EntryResponse.model_validate(entry)
            for entry in self.submission_dao.list_entries(submission_id, section_id=section_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_entry(
        self, submission_id: UUID, actor_id: UUID, data: EntryCreateRequest
    ) -> EntryResponse:
        submission = self._require_editable(self._require_submission(submission_id), actor_id)
        rubric = self.score_keeper.rubric_of(submission)
        values = data.model_dump()
        item = self._check(submission, rubric, values, entry_id=None)

        entry = SubmissionEntry(submission_id=submission_id, **values)
        result = self.score_keeper.score(entry, item, rubric)
        entry.weight_applied, entry.score = result.weight_applied, result.score
        entry = self.submission_dao.add(entry)
        self.score_keeper.refresh(submission, rubric, freeze=False)
        return EntryResponse.model_validate(entry)

    def get_entry(self, entry_id: UUID) -> EntryResponse:
        return EntryResponse.model_validate(self._require_entry(entry_id))

    def update_entry(
        self, entry_id: UUID, actor_id: UUID, data: EntryUpdateRequest, if_match: str | None
    ) -> EntryResponse:
        entry = self._require_entry(entry_id)
        if if_match is not None and if_match != entry_etag(EntryResponse.model_validate(entry)):
            raise PreconditionFailedError("The entry was changed by someone else; reload it")
        submission = self._require_editable(self._require_submission(entry.submission_id), actor_id)
        rubric = self.score_keeper.rubric_of(submission)
        values = data.model_dump(exclude_unset=True)
        merged = entry.model_dump() | values
        item = self._check(submission, rubric, merged, entry_id=entry.id)

        result = self.score_keeper.score(SubmissionEntry.model_validate(merged), item, rubric)
        values |= {"weight_applied": result.weight_applied, "score": result.score}
        entry = self.submission_dao.update(entry, values)
        self.score_keeper.refresh(submission, rubric, freeze=False)
        return EntryResponse.model_validate(entry)

    def delete_entry(self, entry_id: UUID, actor_id: UUID) -> None:
        entry = self._require_entry(entry_id)
        submission = self._require_editable(self._require_submission(entry.submission_id), actor_id)
        keys = [evidence.s3_key for evidence in self.evidence_dao.list_by_entry(entry_id)]
        self.submission_dao.delete(entry)
        self.score_keeper.refresh(submission, self.score_keeper.rubric_of(submission), freeze=False)
        for key in keys:
            self.storage.delete_object(key)

    # --- helpers ------------------------------------------------------------------

    def _check(
        self,
        submission: Submission,
        rubric: Rubric,
        values: Mapping[str, Any],
        *,
        entry_id: UUID | None,
    ) -> RubricItem:
        """The item exists in this submission's rubric and the values fit it."""
        item = rubric.items.get(values["item_id"])
        if item is None:
            raise BadRequestError("item_id is not an item of this round's rubric")
        if not item.is_active:
            raise BadRequestError("This item is no longer in use")

        errors = validate_entry(
            item,
            student_count=values.get("student_count"),
            participation_pct=values["participation_pct"],
            details=values.get("details"),
            columns={name: values.get(name) for name in ENTRY_COLUMNS},
        )
        if errors:
            raise BadRequestError("; ".join(errors))

        if item.once_per_round and self.submission_dao.count_entries(
            submission.id, item_id=item.id, exclude_entry_id=entry_id
        ):
            raise BadRequestError("This item can be claimed only once per round")
        section = next(s for s in rubric.sections if s.id == item.section_id)
        if section.max_entries is not None and (
            self.submission_dao.count_entries(
                submission.id, section_id=section.id, exclude_entry_id=entry_id
            )
            >= section.max_entries
        ):
            raise BadRequestError(
                f"Section {section.code} allows at most {section.max_entries} entries"
            )
        return item

    def _require_submission(self, submission_id: UUID) -> Submission:
        submission = self.submission_dao.get_by_id(submission_id)
        if submission is None:
            raise NotFoundError("Submission not found")
        return submission

    def _require_entry(self, entry_id: UUID) -> SubmissionEntry:
        entry = self.submission_dao.get_entry(entry_id)
        if entry is None:
            raise NotFoundError("Entry not found")
        return entry

    def _require_editable(self, submission: Submission, actor_id: UUID) -> Submission:
        actor = self.lecturer_dao.get_by_id(actor_id)
        if actor is None or not actor.is_active:
            raise UnauthorizedError("Unknown or inactive lecturer")
        # TODO(auth): only the owner (submission.lecturer_id == actor_id)
        if submission.status not in EDITABLE_STATUSES:
            raise ConflictError(f"The submission is {submission.status} and can no longer change")
        return submission
