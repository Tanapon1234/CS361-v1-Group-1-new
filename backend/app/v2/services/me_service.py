from datetime import date

from app.core.exceptions import UnauthorizedError
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.me_dto import MeResponse
from app.v2.dtos.position_dto import PositionResponse
from app.v2.dtos.round_dto import RoundResponse
from app.v2.models.enums import PositionCode, SignerRole
from app.v2.security import Actor, Role

# Positions that let their holder sign submissions; `receiver` comes from the staff role
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

    def get_me(self, actor: Actor) -> MeResponse:
        if actor.lecturer_id is None:
            raise UnauthorizedError("Sign in as a lecturer")
        lecturer = self.lecturer_dao.get_by_id(actor.lecturer_id)
        if lecturer is None or not lecturer.is_active:
            raise UnauthorizedError("Unknown or inactive lecturer")

        positions = self.position_dao.list_active(actor.lecturer_id, date.today())
        signer_roles = {SignerRole.PERFORMER}
        signer_roles |= {
            _SIGNER_ROLE_OF[p.position] for p in positions if p.position in _SIGNER_ROLE_OF
        }
        if actor.has_any(Role.STAFF):
            signer_roles.add(SignerRole.RECEIVER)
        rounds, _ = self.round_dao.find_page(is_open=True, limit=_OPEN_ROUNDS_LIMIT, offset=0)
        return MeResponse(
            lecturer=LecturerResponse.model_validate(lecturer),
            roles=sorted(actor.roles),
            positions=[PositionResponse.model_validate(p) for p in positions],
            signer_roles=[role for role in SignerRole if role in signer_roles],
            open_rounds=[RoundResponse.model_validate(r) for r in rounds],
        )
