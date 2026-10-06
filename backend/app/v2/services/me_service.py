from datetime import date
from uuid import UUID

from app.core.exceptions import UnauthorizedError
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.me_dto import MeResponse
from app.v2.dtos.position_dto import PositionResponse
from app.v2.dtos.round_dto import RoundResponse
from app.v2.models.enums import PositionCode, SignerRole

# Positions that let their holder sign submissions. `receiver` (faculty staff) is not a
# position in the schema, so nobody gets it from here yet.
_SIGNER_ROLE_OF = {
    PositionCode.DEPT_CHAIR: SignerRole.DEPT_CHAIR,
    PositionCode.DEPT_COMMITTEE: SignerRole.DEPT_COMMITTEE,
}
_OPEN_ROUNDS_LIMIT = 20


class MeService:
    def __init__(
        self,
        lecturer_dao: LecturerDAO,
        position_dao: MemberPositionDAO,
        round_dao: EvaluationRoundDAO,
    ) -> None:
        self.lecturer_dao = lecturer_dao
        self.position_dao = position_dao
        self.round_dao = round_dao

    def get_me(self, actor_id: UUID) -> MeResponse:
        lecturer = self.lecturer_dao.get_by_id(actor_id)
        if lecturer is None or not lecturer.is_active:
            raise UnauthorizedError("Unknown or inactive lecturer")

        positions = self.position_dao.list_active(actor_id, date.today())
        roles = [SignerRole.PERFORMER]
        roles += sorted(
            {_SIGNER_ROLE_OF[p.position] for p in positions if p.position in _SIGNER_ROLE_OF}
        )
        rounds, _ = self.round_dao.find_page(is_open=True, limit=_OPEN_ROUNDS_LIMIT, offset=0)
        return MeResponse(
            lecturer=LecturerResponse.model_validate(lecturer),
            positions=[PositionResponse.model_validate(p) for p in positions],
            signer_roles=roles,
            open_rounds=[RoundResponse.model_validate(r) for r in rounds],
        )
