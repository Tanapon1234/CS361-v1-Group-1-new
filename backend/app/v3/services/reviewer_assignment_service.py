"""Who reviews whom (V4 #293): an executive assigns a reviewer to a lecturer; the
verification queue (VerificationService) narrows a plain reviewer to their reviewees.
"""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.v2.models.reviewer_assignment import ReviewerAssignment
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.reviewer_assignment_dao import ReviewerAssignmentDAO
from app.v3.dtos.common import ListMeta, ListResponse
from app.v3.dtos.reviewer_assignment_dto import (
    ReviewerAssignmentCreateRequest,
    ReviewerAssignmentListQuery,
    ReviewerAssignmentResponse,
)
from app.v3.security import Actor, Role
from app.v3.services.db_errors import is_unique_violation


class ReviewerAssignmentService:
    def __init__(self, assignment_dao: ReviewerAssignmentDAO, lecturer_dao: LecturerDAO) -> None:
        self.assignment_dao = assignment_dao
        self.lecturer_dao = lecturer_dao

    def create_assignment(
        self, actor: Actor, data: ReviewerAssignmentCreateRequest
    ) -> ReviewerAssignmentResponse:
        if actor.lecturer_id is None:
            raise ForbiddenError("Sign in as a person: an assignment records who made it")
        self._require_lecturer(data.reviewer_id)
        self._require_lecturer(data.reviewee_id)
        try:
            assignment = self.assignment_dao.add(
                ReviewerAssignment(
                    reviewer_id=data.reviewer_id,
                    reviewee_id=data.reviewee_id,
                    assigned_by=actor.lecturer_id,
                )
            )
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("This reviewer is already assigned to this lecturer") from exc
            raise
        return self._to_response(assignment)

    def list_assignments(
        self, actor: Actor, query: ReviewerAssignmentListQuery
    ) -> ListResponse[ReviewerAssignmentResponse]:
        if actor.has_any(Role.EXECUTIVE):  # admin counts as every role (Actor.has_any)
            assignments = self.assignment_dao.list_all(
                reviewer_id=query.reviewer_id, reviewee_id=query.reviewee_id
            )
        elif actor.has_any(Role.REVIEWER):
            if actor.lecturer_id is None:
                raise ForbiddenError("Sign in as a person to see your assignments")
            assignments = self.assignment_dao.list_by_reviewer(actor.lecturer_id)
        else:
            raise ForbiddenError("Only an executive or a reviewer sees assignments")
        items = [self._to_response(assignment) for assignment in assignments]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def delete_assignment(self, assignment_id: UUID) -> None:
        assignment = self.assignment_dao.get_by_id(assignment_id)
        if assignment is None:
            raise NotFoundError("Assignment not found")
        self.assignment_dao.delete(assignment)

    # --- helpers ------------------------------------------------------------------

    def _require_lecturer(self, lecturer_id: UUID) -> None:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError(f"Lecturer {lecturer_id} not found")

    def _to_response(self, assignment: ReviewerAssignment) -> ReviewerAssignmentResponse:
        reviewer = self.lecturer_dao.get_by_id(assignment.reviewer_id)
        reviewee = self.lecturer_dao.get_by_id(assignment.reviewee_id)
        return ReviewerAssignmentResponse(
            id=assignment.id,
            reviewer_id=assignment.reviewer_id,
            reviewer_name_th=reviewer.name_th if reviewer else "",
            reviewee_id=assignment.reviewee_id,
            reviewee_name_th=reviewee.name_th if reviewee else "",
            assigned_by=assignment.assigned_by,
            created_at=assignment.created_at,
        )
