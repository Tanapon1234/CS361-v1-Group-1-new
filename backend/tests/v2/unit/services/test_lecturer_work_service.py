from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.lecturer_work_dao import LecturerWorkDAO, WorkEntryRow
from app.v2.dtos.lecturer_work_dto import LecturerWorkQuery
from app.v2.models.enums import AcademicRank, SubmissionStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication import Publication
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection
from app.v2.models.submission import EvaluationRound, Submission, SubmissionEntry
from app.v2.services.lecturer_work_service import LecturerWorkService

LECTURER_ID = uuid4()


@pytest.fixture
def work_dao() -> MagicMock:
    dao = create_autospec(LecturerWorkDAO, instance=True)
    dao.list_entries.return_value = []
    dao.list_publications.return_value = []
    dao.list_entry_years.return_value = []
    dao.list_publication_years.return_value = []
    dao.get_category_name.return_value = None
    return dao


@pytest.fixture
def lecturer_dao() -> MagicMock:
    dao = create_autospec(LecturerDAO, instance=True)
    dao.get_by_id.return_value = Lecturer(
        lecturer_id=LECTURER_ID, name_th="สมชาย", email="somchai@example.ac.th"
    )
    return dao


@pytest.fixture
def service(work_dao: MagicMock, lecturer_dao: MagicMock) -> LecturerWorkService:
    return LecturerWorkService(work_dao, lecturer_dao)


def row(category_code: str, title: str, year: int = 2567) -> WorkEntryRow:
    category = RubricCategory(
        id=int(category_code),
        version_id=1,
        code=category_code,
        name_th=f"หมวด {category_code}",
        cap=Decimal(900),
        sort_order=10,
    )
    section = RubricSection(
        id=1, category_id=category.id, code=f"{category_code}.1", name_th="ข้อ", sort_order=10
    )
    item = RubricItem(id=1, section_id=1, label_th="รายการ", weight=Decimal(1), unit="topic")
    rnd = EvaluationRound(
        id=1,
        rubric_version_id=1,
        name_th=f"รอบ {year}",
        period_start=date(2024, 8, 1),
        period_end=date(2025, 7, 31),
        salary_effective_on=date(2025, 10, 1),
        academic_year=year,
    )
    submission = Submission(
        id=uuid4(),
        round_id=1,
        lecturer_id=LECTURER_ID,
        status=SubmissionStatus.SUBMITTED,
        rank_snapshot=AcademicRank.LECTURER,
        department_snapshot=1,
    )
    entry = SubmissionEntry(
        id=uuid4(), submission_id=submission.id, item_id=1, title=title, score=Decimal(10)
    )
    return WorkEntryRow(entry, item, section, category, submission, rnd)


def test_unknown_lecturer_is_not_found(
    service: LecturerWorkService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_work(uuid4(), LecturerWorkQuery())


def test_entries_are_grouped_by_category_in_dao_order(
    service: LecturerWorkService, work_dao: MagicMock
) -> None:
    work_dao.list_entries.return_value = [row("1", "a"), row("1", "b"), row("4", "c")]

    result = service.get_work(LECTURER_ID, LecturerWorkQuery(academic_year=2567))

    assert [(g.code, [e.title for e in g.entries]) for g in result.categories] == [
        ("1", ["a", "b"]),
        ("4", ["c"]),
    ]
    assert result.total == 3
    work_dao.list_entries.assert_called_once_with(
        LECTURER_ID, academic_year=2567, category_code=None
    )


def test_publications_use_the_ce_year_and_report_be(
    service: LecturerWorkService, work_dao: MagicMock
) -> None:
    work_dao.list_publications.return_value = [
        (Publication(publication_id=1, title="Paper", publication_year=2024), 1)
    ]

    result = service.get_work(LECTURER_ID, LecturerWorkQuery(academic_year=2567))

    work_dao.list_publications.assert_called_once_with(LECTURER_ID, publication_year=2024)
    assert result.publications[0].academic_year == 2567


def test_publications_are_left_out_for_other_categories(
    service: LecturerWorkService, work_dao: MagicMock
) -> None:
    result = service.get_work(LECTURER_ID, LecturerWorkQuery(category="1"))

    work_dao.list_publications.assert_not_called()
    assert result.publications == []


def test_empty_result_still_describes_the_search(
    service: LecturerWorkService, work_dao: MagicMock
) -> None:
    work_dao.get_category_name.return_value = "งานวิชาการ"
    work_dao.list_entry_years.return_value = [2566, 2568]
    work_dao.list_publication_years.return_value = [2023]

    result = service.get_work(LECTURER_ID, LecturerWorkQuery(academic_year=2567, category="2"))

    assert result.total == 0
    assert result.filters.model_dump() == {
        "academic_year": 2567,
        "category": "2",
        "category_name_th": "งานวิชาการ",
    }
    assert result.available_years == [2568, 2566]
