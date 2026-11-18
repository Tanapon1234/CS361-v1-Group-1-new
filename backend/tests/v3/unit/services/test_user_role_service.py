"""UserRoleService rules with mocked DAOs (admin grants roles from the app)."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.v2.models.lecturer import Lecturer
from app.v2.models.user_role import UserRole
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.user_role_dao import UserRoleDAO
from app.v3.dtos.user_role_dto import UserRoleGrantRequest
from app.v3.security import Actor, Role
from app.v3.services.user_role_service import UserRoleService

ADMIN = Actor(uuid4(), frozenset({Role.LECTURER, Role.ADMIN}))


@pytest.fixture
def daos() -> dict[str, MagicMock]:
    lecturer_dao = create_autospec(LecturerDAO, instance=True)
    lecturer_dao.get_by_id.side_effect = lambda lecturer_id: Lecturer(
        lecturer_id=lecturer_id, name_th="ก", email=f"{lecturer_id}@x.th"
    )
    return {"role": create_autospec(UserRoleDAO, instance=True), "lecturer": lecturer_dao}


@pytest.fixture
def service(daos: dict[str, MagicMock]) -> UserRoleService:
    return UserRoleService(daos["role"], daos["lecturer"])


def row(lecturer_id, role: Role) -> UserRole:
    return UserRole(lecturer_id=lecturer_id, role=role.value, granted_by=ADMIN.lecturer_id)


def test_admin_grants_a_role(service: UserRoleService, daos: dict[str, MagicMock]) -> None:
    target = uuid4()
    daos["role"].add.side_effect = lambda r: r

    result = service.grant(ADMIN, UserRoleGrantRequest(lecturer_id=target, role=Role.STAFF))

    assert result.lecturer_id == target
    assert result.role is Role.STAFF
    assert result.granted_by == ADMIN.lecturer_id


@pytest.mark.parametrize("role", [Role.REVIEWER, Role.LECTURER])
def test_reviewer_and_lecturer_cannot_be_granted(
    service: UserRoleService, daos: dict[str, MagicMock], role: Role
) -> None:
    with pytest.raises(BadRequestError):
        service.grant(ADMIN, UserRoleGrantRequest(lecturer_id=uuid4(), role=role))
    daos["role"].add.assert_not_called()


def test_granting_to_an_unknown_lecturer_is_not_found(
    service: UserRoleService, daos: dict[str, MagicMock]
) -> None:
    daos["lecturer"].get_by_id.side_effect = None
    daos["lecturer"].get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.grant(ADMIN, UserRoleGrantRequest(lecturer_id=uuid4(), role=Role.STAFF))


def test_granting_twice_is_a_conflict(service: UserRoleService, daos: dict[str, MagicMock]) -> None:
    violation = Exception("duplicate")
    violation.sqlstate = "23505"  # type: ignore[attr-defined]
    daos["role"].add.side_effect = IntegrityError("INSERT", {}, violation)

    with pytest.raises(ConflictError):
        service.grant(ADMIN, UserRoleGrantRequest(lecturer_id=uuid4(), role=Role.STAFF))


def test_a_grant_needs_a_person_to_record(service: UserRoleService) -> None:
    script = Actor(None, frozenset({Role.ADMIN}))

    with pytest.raises(ForbiddenError):
        service.grant(script, UserRoleGrantRequest(lecturer_id=uuid4(), role=Role.STAFF))


def test_admin_revokes_a_role(service: UserRoleService, daos: dict[str, MagicMock]) -> None:
    target = uuid4()
    daos["role"].get.return_value = row(target, Role.STAFF)

    service.revoke(ADMIN, target, Role.STAFF)

    daos["role"].delete.assert_called_once()


def test_revoking_a_role_that_is_not_held_is_not_found(
    service: UserRoleService, daos: dict[str, MagicMock]
) -> None:
    daos["role"].get.return_value = None

    with pytest.raises(NotFoundError):
        service.revoke(ADMIN, uuid4(), Role.STAFF)


def test_an_admin_cannot_revoke_their_own_admin_role(
    service: UserRoleService, daos: dict[str, MagicMock]
) -> None:
    daos["role"].get.return_value = row(ADMIN.lecturer_id, Role.ADMIN)
    daos["role"].count_with_role.return_value = 2

    with pytest.raises(ConflictError):
        service.revoke(ADMIN, ADMIN.lecturer_id, Role.ADMIN)
    daos["role"].delete.assert_not_called()


def test_the_last_admin_cannot_be_revoked(
    service: UserRoleService, daos: dict[str, MagicMock]
) -> None:
    target = uuid4()
    daos["role"].get.return_value = row(target, Role.ADMIN)
    daos["role"].count_with_role.return_value = 1

    with pytest.raises(ConflictError):
        service.revoke(ADMIN, target, Role.ADMIN)
    daos["role"].delete.assert_not_called()


def test_another_admin_can_be_revoked_when_more_remain(
    service: UserRoleService, daos: dict[str, MagicMock]
) -> None:
    target = uuid4()
    daos["role"].get.return_value = row(target, Role.ADMIN)
    daos["role"].count_with_role.return_value = 2

    service.revoke(ADMIN, target, Role.ADMIN)

    daos["role"].delete.assert_called_once()
