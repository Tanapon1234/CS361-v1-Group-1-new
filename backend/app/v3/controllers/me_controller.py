from fastapi import APIRouter

from app.v3.dependencies import CurrentActorDep, MeServiceDep
from app.v3.dtos.me_dto import MeResponse

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
def get_me(actor: CurrentActorDep, service: MeServiceDep) -> MeResponse:
    """The caller's profile, roles, current positions, signer roles and open rounds."""
    return service.get_me(actor)
