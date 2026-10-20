from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.exceptions import NotFoundError
from app.v2.models.education import Education
from app.v2.models.lecturer import Lecturer
from app.v3.daos.education_dao import EducationDAO
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.dtos.education_dto import EducationCreateRequest, EducationUpdateRequest
from app.v3.services.education_service import EducationService

LECTURER_ID = uuid4()


@pytest.fixture
def education_dao() -> MagicMock:
    return create_autospec(EducationDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    dao = create_autospec(LecturerDAO, instance=True)
    dao.get_by_id.return_value = Lecturer(
        lecturer_id=LECTURER_ID, name_th="สมชาย", email="somchai@example.ac.th"
    )
    return dao


@pytest.fixture
def service(education_dao: MagicMock, lecturer_dao: MagicMock) -> EducationService:
    return EducationService(education_dao, lecturer_dao)


def education(education_id: int = 1, lecturer_id=LECTURER_ID) -> Education:
    return Education(
        education_id=education_id, lecturer_id=lecturer_id, degree="Ph.D.", graduation_year="2555"
    )


def test_list_for_unknown_lecturer_raises_not_found(
    service: EducationService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.list_educations(uuid4())


def test_list_returns_the_lecturers_rows(
    service: EducationService, education_dao: MagicMock
) -> None:
    education_dao.list_by_lecturer.return_value = [education(1), education(2)]

    result = service.list_educations(LECTURER_ID)

    assert [item.education_id for item in result.items] == [1, 2]
    assert result.meta.count == 2


def test_create_saves_under_the_lecturer(
    service: EducationService, education_dao: MagicMock
) -> None:
    education_dao.add.side_effect = lambda row: row.model_copy(update={"education_id": 7})

    result = service.create_education(
        LECTURER_ID, EducationCreateRequest(degree="Ph.D.", institution="  TU  ")
    )

    saved = education_dao.add.call_args.args[0]
    assert saved.lecturer_id == LECTURER_ID
    assert saved.institution == "TU"
    assert result.education_id == 7


def test_update_another_lecturers_row_is_not_found(
    service: EducationService, education_dao: MagicMock
) -> None:
    education_dao.get_by_id.return_value = education(lecturer_id=uuid4())

    with pytest.raises(NotFoundError):
        service.update_education(LECTURER_ID, 1, EducationUpdateRequest(degree="M.Sc."))
    education_dao.update.assert_not_called()


def test_update_passes_only_the_sent_fields(
    service: EducationService, education_dao: MagicMock
) -> None:
    row = education()
    education_dao.get_by_id.return_value = row
    education_dao.update.return_value = row

    service.update_education(LECTURER_ID, 1, EducationUpdateRequest(country="Japan"))

    education_dao.update.assert_called_once_with(row, {"country": "Japan"})


def test_delete_unknown_row_is_not_found(
    service: EducationService, education_dao: MagicMock
) -> None:
    education_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.delete_education(LECTURER_ID, 99)


def test_create_needs_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        EducationCreateRequest(degree="  ", institution=None)


def test_update_needs_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        EducationUpdateRequest()
