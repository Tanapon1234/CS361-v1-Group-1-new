"""Department CRUD and the V4 department report, with mocked DAOs."""

from decimal import Decimal
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.v2.models.department import Department
from app.v2.models.enums import PositionCode
from app.v2.models.lecturer import Lecturer
from app.v2.models.submission import SubmissionCategoryTotal
from app.v3.daos.department_dao import DepartmentDAO
from app.v3.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.submission_dao import SubmissionDAO
from app.v3.dtos.department_dto import DepartmentReportQuery
from app.v3.security import Actor, HeldPosition, Role
from app.v3.services.department_service import DepartmentService


@pytest.fixture
def daos() -> dict[str, MagicMock]:
    return {
        "department": create_autospec(DepartmentDAO, instance=True),
        "lecturer": create_autospec(LecturerDAO, instance=True),
        "submission": create_autospec(SubmissionDAO, instance=True),
        "round": create_autospec(EvaluationRoundDAO, instance=True),
    }


@pytest.fixture
def service(daos: dict[str, MagicMock]) -> DepartmentService:
    return DepartmentService(
        daos["department"], daos["lecturer"], daos["submission"], daos["round"]
    )


def lecturer(**values: object) -> Lecturer:
    defaults = {
        "lecturer_id": uuid4(),
        "name_th": "สมชาย",
        "email": "a@x.th",
        "department_id": 1,
    }
    return Lecturer(**(defaults | values))


def category_total(**values: object) -> SubmissionCategoryTotal:
    defaults = {
        "submission_id": uuid4(),
        "category_id": 1,
        "raw_score": Decimal("10"),
        "capped_score": Decimal("10"),
    }
    return SubmissionCategoryTotal(**(defaults | values))


def query(**values: object) -> DepartmentReportQuery:
    defaults = {"academic_year_from": 2566, "academic_year_to": 2568}
    return DepartmentReportQuery(**(defaults | values))


ADMIN = Actor(uuid4(), frozenset({Role.ADMIN}))
EXECUTIVE = Actor(uuid4(), frozenset({Role.EXECUTIVE}))
STAFF = Actor(uuid4(), frozenset({Role.STAFF}))


class TestGetReport:
    def test_unknown_department_is_not_found(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            service.get_report(1, ADMIN, query())

    def test_year_range_backwards_is_a_bad_request(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=1, code="CS", name_th="CS")
        with pytest.raises(BadRequestError):
            service.get_report(1, ADMIN, query(academic_year_from=2568, academic_year_to=2566))

    def test_executive_sees_a_department_that_is_not_their_own(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=2, code="EE", name_th="EE")
        daos["lecturer"].get_by_id.return_value = lecturer(department_id=1)
        daos["submission"].list_department_category_totals.return_value = []
        daos["lecturer"].find_page.return_value = ([], 0)
        daos["round"].list_academic_years.return_value = []

        service.get_report(2, EXECUTIVE, query())  # does not raise

    def test_staff_of_another_department_is_forbidden(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=2, code="EE", name_th="EE")
        daos["lecturer"].get_by_id.return_value = lecturer(department_id=1)  # staff's own dept
        with pytest.raises(ForbiddenError):
            service.get_report(2, STAFF, query())

    def test_staff_of_the_same_department_is_allowed(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=1, code="CS", name_th="CS")
        daos["lecturer"].get_by_id.return_value = lecturer(department_id=1)
        daos["submission"].list_department_category_totals.return_value = []
        daos["lecturer"].find_page.return_value = ([], 0)
        daos["round"].list_academic_years.return_value = []

        service.get_report(1, STAFF, query())  # does not raise

    def test_dept_chair_of_the_department_is_allowed_without_the_staff_role(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=1, code="CS", name_th="CS")
        daos["submission"].list_department_category_totals.return_value = []
        daos["lecturer"].find_page.return_value = ([], 0)
        daos["round"].list_academic_years.return_value = []
        chair = Actor(uuid4(), frozenset(), frozenset({HeldPosition(PositionCode.DEPT_CHAIR, 1)}))

        service.get_report(1, chair, query())  # does not raise
        daos["lecturer"].get_by_id.assert_called_once()  # only to resolve caller_department_id

    def test_rows_come_from_category_totals_joined_with_lecturer_and_round(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=1, code="CS", name_th="CS")
        prapaporn = lecturer(name_th="ปราภาพร")
        daos["submission"].list_department_category_totals.return_value = [
            (
                category_total(raw_score=Decimal("90"), capped_score=Decimal("80")),
                prapaporn,
                2567,
                "1",
                "งานสอน",
            )
        ]
        daos["lecturer"].find_page.return_value = ([], 0)
        daos["round"].list_academic_years.return_value = []

        result = service.get_report(1, ADMIN, query())

        assert len(result.rows) == 1
        row = result.rows[0]
        assert row.lecturer_id == prapaporn.lecturer_id
        assert row.academic_year == 2567
        assert row.category_code == "1"
        assert row.capped_score == Decimal("80")

    def test_active_lecturer_with_no_data_that_year_is_missing(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=1, code="CS", name_th="CS")
        thapana = lecturer(name_th="ฐาปนา")
        kasidit = lecturer(name_th="กษิดิศ")
        daos["submission"].list_department_category_totals.return_value = []
        daos["lecturer"].find_page.return_value = ([thapana, kasidit], 2)
        daos["round"].list_academic_years.return_value = [2567]
        # kasidit has data this year; thapana does not
        daos["submission"].find_lecturers_with_department_data.return_value = [kasidit.lecturer_id]

        result = service.get_report(1, ADMIN, query())

        assert len(result.missing) == 1
        assert result.missing[0].lecturer_id == thapana.lecturer_id
        assert result.missing[0].academic_year == 2567

    def test_lecturer_with_data_every_year_is_not_missing(
        self, service: DepartmentService, daos: dict[str, MagicMock]
    ) -> None:
        daos["department"].get_by_id.return_value = Department(id=1, code="CS", name_th="CS")
        prapaporn = lecturer(name_th="ปราภาพร")
        daos["submission"].list_department_category_totals.return_value = []
        daos["lecturer"].find_page.return_value = ([prapaporn], 1)
        daos["round"].list_academic_years.return_value = [2566, 2567]
        daos["submission"].find_lecturers_with_department_data.return_value = [
            prapaporn.lecturer_id
        ]

        result = service.get_report(1, ADMIN, query())

        assert result.missing == []
