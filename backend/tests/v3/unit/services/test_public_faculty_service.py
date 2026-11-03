from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.v2.models.education import Education
from app.v2.models.lecturer import Lecturer
from app.v2.models.research_interest import ResearchInterest
from app.v3.daos.education_dao import EducationDAO
from app.v3.daos.expertise_dao import ExpertiseDAO
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.publication_profile_dao import PublicationProfileDAO
from app.v3.daos.research_interest_dao import ResearchInterestDAO
from app.v3.dtos.lecturer_file_dto import FileDownloadResponse
from app.v3.services.lecturer_file_service import LecturerFileService
from app.v3.services.public_faculty_service import PublicFacultyService


def make_lecturer(**values: object) -> Lecturer:
    base = {
        "lecturer_id": uuid4(),
        "name_th": "สมชาย ใจดี",
        "name_en": "Somchai Jaidee",
        "rank": "ผู้ช่วยศาสตราจารย์",
        "office": "SC1-301",
        "phone": "0812345678",
        "phone_extension": "1234",
        "email": "somchai@example.com",
        "is_active": True,
    }
    return Lecturer(**{**base, **values})


@pytest.fixture
def daos() -> dict[str, MagicMock]:
    daos = {
        "lecturer_dao": create_autospec(LecturerDAO, instance=True),
        "education_dao": create_autospec(EducationDAO, instance=True),
        "research_interest_dao": create_autospec(ResearchInterestDAO, instance=True),
        "expertise_dao": create_autospec(ExpertiseDAO, instance=True),
        "publication_dao": create_autospec(PublicationDAO, instance=True),
        "publication_profile_dao": create_autospec(PublicationProfileDAO, instance=True),
        "file_service": create_autospec(LecturerFileService, instance=True),
    }
    daos["research_interest_dao"].list_by_lecturer.return_value = [ResearchInterest(name="AI")]
    daos["education_dao"].list_by_lecturer.return_value = [
        Education(lecturer_id=uuid4(), degree="Ph.D.", graduation_year="2555")
    ]
    daos["expertise_dao"].list_by_lecturer.return_value = []
    daos["publication_dao"].find_lecturer_page.return_value = ([], 0)
    daos["publication_profile_dao"].list_by_lecturer.return_value = []
    return daos


def test_list_has_names_position_and_interests_only(daos: dict[str, MagicMock]) -> None:
    lecturer = make_lecturer()
    daos["lecturer_dao"].find_page.return_value = ([lecturer], 1)

    result = PublicFacultyService(**daos).list_faculties()

    assert daos["lecturer_dao"].find_page.call_args.kwargs["is_active"] is True
    [item] = result.data
    assert item.name.th == "สมชาย ใจดี"
    assert item.academic_position == "ผู้ช่วยศาสตราจารย์"
    assert item.research_interests == ["AI"]
    assert item.profile_image is None


def test_detail_never_exposes_phone_or_email(daos: dict[str, MagicMock]) -> None:
    lecturer = make_lecturer(
        cv_url="https://example.com/cv.pdf", profile_image_url="https://example.com/me.jpg"
    )
    daos["lecturer_dao"].get_by_id.return_value = lecturer
    download = FileDownloadResponse(
        download_url="https://example.com/file", expires_at=datetime.now(UTC)
    )
    daos["file_service"].get_cv.return_value = download
    daos["file_service"].get_profile_image.return_value = download

    detail = PublicFacultyService(**daos).get_faculty(lecturer.lecturer_id)

    assert detail.contact is not None
    assert detail.contact.office == "SC1-301"
    assert detail.contact.extension == "1234"
    assert detail.contact.phone is None
    assert detail.contact.email is None
    assert detail.cv is not None
    assert detail.education[0].degree == "Ph.D."
    assert "0812345678" not in detail.model_dump_json()
    assert "somchai@example.com" not in detail.model_dump_json()


@pytest.mark.parametrize("found", [None, make_lecturer(is_active=False)])
def test_unknown_or_inactive_lecturer_is_not_found(
    daos: dict[str, MagicMock], found: Lecturer | None
) -> None:
    daos["lecturer_dao"].get_by_id.return_value = found

    with pytest.raises(NotFoundError):
        PublicFacultyService(**daos).get_faculty(uuid4())
