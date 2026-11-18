from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.v3.dependencies import CurrentActorDep, UserRoleServiceDep
from app.v3.dtos.common import ListResponse
from app.v3.dtos.user_role_dto import UserRoleGrantRequest, UserRoleListQuery, UserRoleResponse
from app.v3.security import Role

router = APIRouter(prefix="/user-roles", tags=["user-roles"])


@router.get("")
def list_user_roles(
    query: Annotated[UserRoleListQuery, Query()], service: UserRoleServiceDep
) -> ListResponse[UserRoleResponse]:
    """Admin only (ROUTE_RULES): roles granted from the app. Cognito groups are not listed."""
    return service.list_roles(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def grant_user_role(
    data: UserRoleGrantRequest, actor: CurrentActorDep, service: UserRoleServiceDep
) -> UserRoleResponse:
    return service.grant(actor, data)


@router.delete("/{lecturer_id}/{role}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_user_role(
    lecturer_id: UUID, role: Role, actor: CurrentActorDep, service: UserRoleServiceDep
) -> None:
    service.revoke(actor, lecturer_id, role)
