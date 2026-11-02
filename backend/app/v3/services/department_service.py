from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.v2.models.department import Department
from app.v3.daos.department_dao import DepartmentDAO
from app.v3.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.submission_dao import SubmissionDAO
from app.v3.dtos.common import PageMeta, PageResponse
from app.v3.dtos.department_dto import (
    DepartmentCreateRequest,
    DepartmentListQuery,
    DepartmentReportCategoryRow,
    DepartmentReportMissingRow,
    DepartmentReportQuery,
    DepartmentReportResponse,
    DepartmentResponse,
    DepartmentUpdateRequest,
)
from app.v3.security import Actor
from app.v3.services.access import require_department_report_access
from app.v3.services.db_errors import is_unique_violation

MAX_REPORT_LECTURERS = 500


class DepartmentService:
    def __init__(
        self,
        department_dao: DepartmentDAO,
        lecturer_dao: LecturerDAO,
        submission_dao: SubmissionDAO,
        round_dao: EvaluationRoundDAO,
    ) -> None:
        self.department_dao = department_dao
        self.lecturer_dao = lecturer_dao
        self.submission_dao = submission_dao
        self.round_dao = round_dao

    def list_departments(self, query: DepartmentListQuery) -> PageResponse[DepartmentResponse]:
        items, total = self.department_dao.find_page(
            is_active=query.is_active, limit=query.limit, offset=query.offset
        )
        return PageResponse(
            items=[DepartmentResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def create_department(self, data: DepartmentCreateRequest) -> DepartmentResponse:
        if self.department_dao.get_by_code(data.code) is not None:
            raise ConflictError("Department code already used")
        try:
            department = self.department_dao.add(Department(**data.model_dump()))
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("Department code already used") from exc
            raise
        return DepartmentResponse.model_validate(department)

    def update_department(
        self, department_id: int, data: DepartmentUpdateRequest
    ) -> DepartmentResponse:
        department = self.department_dao.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found")

        values = data.model_dump(exclude_unset=True)
        code = values.get("code")
        if (
            code is not None
            and code != department.code
            and self.department_dao.get_by_code(code) is not None
        ):
            raise ConflictError("Department code already used")
        try:
            department = self.department_dao.update(department, values)
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("Department code already used") from exc
            raise
        return DepartmentResponse.model_validate(department)

    def get_report(
        self, department_id: int, actor: Actor, query: DepartmentReportQuery
    ) -> DepartmentReportResponse:
        """V4 FR7/FR8: every lecturer's frozen category totals in the department for the
        year range, plus active lecturers with no data yet (so a report can't silently
        drop someone who hasn't submitted)."""
        department = self._require_department(department_id)
        if query.academic_year_to < query.academic_year_from:
            raise BadRequestError("academic_year_to must not be before academic_year_from")
        require_department_report_access(actor, department_id, self._caller_department_id(actor))

        rows = [
            DepartmentReportCategoryRow(
                lecturer_id=lecturer.lecturer_id,
                name_th=lecturer.name_th,
                academic_year=academic_year,
                category_code=category_code,
                category_name_th=category_name_th,
                raw_score=total.raw_score,
                capped_score=total.capped_score,
            )
            for total, lecturer, academic_year, category_code, category_name_th in (
                self.submission_dao.list_department_category_totals(
                    department_id,
                    academic_year_from=query.academic_year_from,
                    academic_year_to=query.academic_year_to,
                )
            )
        ]

        lecturers, _ = self.lecturer_dao.find_page(
            q=None,
            is_active=True,
            department_id=department_id,
            limit=MAX_REPORT_LECTURERS,
            offset=0,
        )
        years = self.round_dao.list_academic_years(query.academic_year_from, query.academic_year_to)
        missing: list[DepartmentReportMissingRow] = []
        for year in sorted(years, reverse=True):
            present = set(
                self.submission_dao.find_lecturers_with_department_data(department_id, year)
            )
            missing.extend(
                DepartmentReportMissingRow(
                    lecturer_id=lecturer.lecturer_id, name_th=lecturer.name_th, academic_year=year
                )
                for lecturer in lecturers
                if lecturer.lecturer_id not in present
            )

        return DepartmentReportResponse(
            department=DepartmentResponse.model_validate(department),
            academic_year_from=query.academic_year_from,
            academic_year_to=query.academic_year_to,
            rows=rows,
            missing=missing,
        )

    # --- helpers ------------------------------------------------------------------

    def _require_department(self, department_id: int) -> Department:
        department = self.department_dao.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found")
        return department

    def _caller_department_id(self, actor: Actor) -> int | None:
        if actor.lecturer_id is None:
            return None
        lecturer = self.lecturer_dao.get_by_id(actor.lecturer_id)
        return lecturer.department_id if lecturer is not None else None
