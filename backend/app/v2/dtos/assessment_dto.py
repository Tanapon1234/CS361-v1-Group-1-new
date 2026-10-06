from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import Number, PageQuery
from app.v2.dtos.submission_dto import EntryResponse
from app.v2.models.enums import PositionCode, RangeBasis


class AssessmentPutRequest(RequestDTO):
    # Must be within the item's weight_min..weight_max
    value_given: Decimal = Field(ge=0, max_digits=8, decimal_places=4, examples=[1.5])
    comment: str | None = Field(default=None, max_length=2000)


class AssessmentResponse(ResponseDTO):
    id: UUID
    entry_id: UUID
    assessor_id: UUID
    position_used: PositionCode
    value_given: Number
    comment: str | None
    assessed_at: datetime


class AssessmentQueueQuery(PageQuery):
    round_id: int | None = Field(default=None, ge=1, le=32767)
    # pending = I have not given a value yet, done = I have
    status: Literal["pending", "done"] | None = None


class AssessmentQueueItem(BaseModel):
    entry: EntryResponse
    lecturer_id: UUID
    lecturer_name_th: str
    department_id: int
    item_label_th: str
    assessor_position: PositionCode
    range_basis: RangeBasis | None
    weight_min: Number | None
    weight_max: Number | None
    my_assessment: AssessmentResponse | None
