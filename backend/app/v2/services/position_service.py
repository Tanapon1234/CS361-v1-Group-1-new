"""Administrative positions (member_position) of a lecturer."""

from datetime import date
from uuid import UUID

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.v2.daos.department_dao import DepartmentDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.position_dto import (
    PositionCreateRequest,
    PositionResponse,
    PositionUpdateRequest,
)
from app.v2.models.enums import PositionCode
from app.v2.models.member_position import MemberPosition

# Held inside one department; the others are faculty-level (department_id is NULL).
DEPARTMENT_POSITIONS = frozenset(
    {
        PositionCode.DEPT_CHAIR,
        PositionCode.DEPT_DEPUTY,
        PositionCode.DEPT_SECRETARY,
        PositionCode.DEPT_COMMITTEE,
    }
)


class PositionService:
    def __init__(
        self,
        position_dao: MemberPositionDAO,
        lecturer_dao: LecturerDAO,
        department_dao: DepartmentDAO,
    ) -> None:
        self.position_dao = position_dao
        self.lecturer_dao = lecturer_dao
        self.department_dao = department_dao

    def list_positions(self, lecturer_id: UUID) -> ListResponse[PositionResponse]:
        self._require_lecturer(lecturer_id)
        items = [
            PositionResponse.model_validate(item)
            for item in self.position_dao.list_by_lecturer(lecturer_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_position(self, lecturer_id: UUID, data: PositionCreateRequest) -> PositionResponse:
        self._require_lecturer(lecturer_id)
        if data.position in DEPARTMENT_POSITIONS:
            if data.department_id is None:
                raise BadRequestError(f"{data.position} needs a department_id")
            if self.department_dao.get_by_id(data.department_id) is None:
                raise BadRequestError("Department not found")
        elif data.department_id is not None:
            raise BadRequestError(f"{data.position} is a faculty-level position: no department_id")

        self._reject_overlap(lecturer_id, data.position, data.start_date, data.end_date)
        position = self.position_dao.add(
            MemberPosition(lecturer_id=lecturer_id, **data.model_dump())
        )
        return PositionResponse.model_validate(position)

    def update_position(
        self, lecturer_id: UUID, position_id: UUID, data: PositionUpdateRequest
    ) -> PositionResponse:
        position = self._require_position(lecturer_id, position_id)
        values = data.model_dump(exclude_unset=True)
        if values.get("start_date", position.start_date) is None:
            raise BadRequestError("start_date must not be null")

        start_date = values.get("start_date", position.start_date)
        end_date = values.get("end_date", position.end_date)
        if end_date is not None and end_date <= start_date:
            raise BadRequestError("end_date must be after start_date")
        self._reject_overlap(
            lecturer_id, position.position, start_date, end_date, exclude_id=position.id
        )
        return PositionResponse.model_validate(self.position_dao.update(position, values))

    def delete_position(self, lecturer_id: UUID, position_id: UUID) -> None:
        self.position_dao.delete(self._require_position(lecturer_id, position_id))

    # --- helpers ---

    def _require_lecturer(self, lecturer_id: UUID) -> None:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

    def _require_position(self, lecturer_id: UUID, position_id: UUID) -> MemberPosition:
        position = self.position_dao.get_by_id(position_id)
        if position is None or position.lecturer_id != lecturer_id:
            raise NotFoundError("Position not found")
        return position

    def _reject_overlap(
        self,
        lecturer_id: UUID,
        position: PositionCode,
        start_date: date,
        end_date: date | None,
        exclude_id: UUID | None = None,
    ) -> None:
        overlapping = self.position_dao.find_overlapping(
            lecturer_id=lecturer_id,
            position=position,
            start_date=start_date,
            end_date=end_date,
            exclude_id=exclude_id,
        )
        if overlapping is not None:
            raise ConflictError(
                f"The lecturer already holds {position} from {overlapping.start_date}"
            )
