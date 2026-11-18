"""Who reviews whom (011/012_reviewer_assignment*.sql, V4 #293)."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import model_validator

from app.v3.dtos.base import QueryDTO, RequestDTO, ResponseDTO


class ReviewerAssignmentListQuery(QueryDTO):
    round_id: int | None = None
    reviewer_id: UUID | None = None
    reviewee_id: UUID | None = None


class ReviewerAssignmentCreateRequest(RequestDTO):
    round_id: int
    reviewer_id: UUID
    reviewee_id: UUID

    @model_validator(mode="after")
    def not_self(self) -> Self:
        if self.reviewer_id == self.reviewee_id:
            raise ValueError("reviewer_id and reviewee_id must not be the same lecturer")
        return self


class ReviewerAssignmentResponse(ResponseDTO):
    id: UUID
    round_id: int
    round_name_th: str
    reviewer_id: UUID
    reviewer_name_th: str
    reviewee_id: UUID
    reviewee_name_th: str
    assigned_by: UUID
    created_at: datetime
