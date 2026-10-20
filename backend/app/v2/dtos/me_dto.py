from pydantic import BaseModel

from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.position_dto import PositionResponse
from app.v2.dtos.round_dto import RoundResponse
from app.v2.models.enums import SignerRole
from app.v2.security import Role


class MeResponse(BaseModel):
    lecturer: LecturerResponse
    # docs/v2/permissions.md; the UI shows only what these allow, the API still checks
    roles: list[Role]
    # Positions held today
    positions: list[PositionResponse]
    # Roles the caller can sign submissions as, based on `positions`
    signer_roles: list[SignerRole]
    open_rounds: list[RoundResponse]
