from fastapi import APIRouter

from app.v2.dependencies import CurrentLecturerIdDep, MeServiceDep
from app.v2.dtos.me_dto import MeResponse

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
def get_me(actor_id: CurrentLecturerIdDep, service: MeServiceDep) -> MeResponse:
    """The caller's profile, current positions, signer roles and open rounds."""
    return service.get_me(actor_id)
