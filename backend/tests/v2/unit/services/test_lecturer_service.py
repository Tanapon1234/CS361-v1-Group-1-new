"""Service tests with a mocked DAO. One example to start from; add tests for your own rules.

While the service raises NotImplementedError the test reports XFAIL. Once it passes it
reports XPASS and fails the run on purpose: delete the `pytestmark` line then.
"""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.lecturer_dto import LecturerCreateRequest, LecturerListQuery
from app.v2.models.lecturer import Lecturer
from app.v2.services.lecturer_service import LecturerService


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(lecturer_dao: MagicMock) -> LecturerService:
    return LecturerService(lecturer_dao)


def test_create_lecturer_success(service: LecturerService, lecturer_dao: MagicMock) -> None:
    lecturer_dao.get_by_email.return_value = None
    lecturer_dao.add.side_effect = lambda lecturer: lecturer

    result = service.create_lecturer(
        LecturerCreateRequest(
            name_th="ผศ.ดร.สมชาย ใจดี",
            name_en="Asst. Prof. Somchai Jaidee",
            email="somchai@example.ac.th",
        )
    )

    assert result.name_th == "ผศ.ดร.สมชาย ใจดี"
    assert result.email == "somchai@example.ac.th"
    assert result.is_active is True
    lecturer_dao.get_by_email.assert_called_once_with("somchai@example.ac.th")
    added = lecturer_dao.add.call_args.args[0]
    assert isinstance(added, Lecturer)
    assert added.name_en == "Asst. Prof. Somchai Jaidee"


def test_create_lecturer_duplicate_email_raises_conflict(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_email.return_value = Lecturer(
        name_th="Existing Lecturer", email="somchai@example.ac.th"
    )

    with pytest.raises(ConflictError, match="Email already used"):
        service.create_lecturer(
            LecturerCreateRequest(name_th="สมชาย", email="somchai@example.ac.th")
        )

    lecturer_dao.add.assert_not_called()


def test_create_lecturer_unique_race_raises_conflict(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_email.return_value = None
    unique_violation = Exception("duplicate")
    unique_violation.sqlstate = "23505"  # type: ignore[attr-defined]
    lecturer_dao.add.side_effect = IntegrityError("INSERT INTO lecturer", {}, unique_violation)

    with pytest.raises(ConflictError, match="Email already used"):
        service.create_lecturer(
            LecturerCreateRequest(name_th="สมชาย", email="somchai@example.ac.th")
        )


def test_create_lecturer_propagates_unexpected_write_error(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_email.return_value = None
    lecturer_dao.add.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.create_lecturer(
            LecturerCreateRequest(name_th="สมชาย", email="somchai@example.ac.th")
        )


def test_list_lecturers_success(service: LecturerService, lecturer_dao: MagicMock) -> None:
    lecturers = [
        Lecturer(name_th="Alpha", email="alpha@example.ac.th"),
        Lecturer(name_th="Beta", email="beta@example.ac.th", is_active=False),
    ]
    lecturer_dao.find_page.return_value = (lecturers, 5)
    query = LecturerListQuery(q="a", is_active=True, limit=2, offset=1)

    result = service.list_lecturers(query)

    assert [item.name_th for item in result.items] == ["Alpha", "Beta"]
    assert result.meta.model_dump() == {"total": 5, "limit": 2, "offset": 1}
    lecturer_dao.find_page.assert_called_once_with(q="a", is_active=True, limit=2, offset=1)


def test_list_lecturers_propagates_query_error(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.find_page.side_effect = RuntimeError("query failed")

    with pytest.raises(RuntimeError, match="query failed"):
        service.list_lecturers(LecturerListQuery())


def test_activate_lecturer_success(service: LecturerService, lecturer_dao: MagicMock) -> None:
    lecturer_id = uuid4()
    lecturer = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
        is_active=False,
    )
    lecturer_dao.get_by_id.return_value = lecturer

    def update(entity: Lecturer, values: dict[str, bool]) -> Lecturer:
        entity.sqlmodel_update(values)
        return entity

    lecturer_dao.update.side_effect = update

    result = service.activate_lecturer(lecturer_id)

    assert result.is_active is True
    lecturer_dao.update.assert_called_once_with(lecturer, {"is_active": True})


def test_activate_already_active_lecturer_is_idempotent(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
        is_active=True,
    )

    result = service.activate_lecturer(lecturer_id)

    assert result.is_active is True
    lecturer_dao.update.assert_not_called()


def test_activate_unknown_lecturer_raises_not_found(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.activate_lecturer(uuid4())

    lecturer_dao.update.assert_not_called()


def test_activate_lecturer_propagates_update_error(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
        is_active=False,
    )
    lecturer_dao.update.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.activate_lecturer(lecturer_id)


def test_deactivate_lecturer_success(service: LecturerService, lecturer_dao: MagicMock) -> None:
    lecturer_id = uuid4()
    lecturer = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
        is_active=True,
    )
    lecturer_dao.get_by_id.return_value = lecturer

    def update(entity: Lecturer, values: dict[str, bool]) -> Lecturer:
        entity.sqlmodel_update(values)
        return entity

    lecturer_dao.update.side_effect = update

    result = service.deactivate_lecturer(lecturer_id)

    assert result.is_active is False
    lecturer_dao.update.assert_called_once_with(lecturer, {"is_active": False})


def test_deactivate_inactive_lecturer_is_idempotent(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
        is_active=False,
    )

    result = service.deactivate_lecturer(lecturer_id)

    assert result.is_active is False
    lecturer_dao.update.assert_not_called()


def test_deactivate_unknown_lecturer_raises_not_found(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.deactivate_lecturer(uuid4())

    lecturer_dao.update.assert_not_called()


def test_deactivate_lecturer_propagates_update_error(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
        is_active=True,
    )
    lecturer_dao.update.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.deactivate_lecturer(lecturer_id)


def test_get_lecturer_success(service: LecturerService, lecturer_dao: MagicMock) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
        is_active=False,
    )

    result = service.get_lecturer(lecturer_id)

    assert result.lecturer_id == lecturer_id
    assert result.name_th == "สมชาย"
    assert result.is_active is False
    lecturer_dao.get_by_id.assert_called_once_with(lecturer_id)


def test_get_unknown_lecturer_raises_not_found(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    lecturer_id = uuid4()
    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.get_lecturer(lecturer_id)

    lecturer_dao.get_by_id.assert_called_once_with(lecturer_id)


def test_get_lecturer_propagates_query_error(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.side_effect = RuntimeError("query failed")

    with pytest.raises(RuntimeError, match="query failed"):
        service.get_lecturer(uuid4())
