"""One lecturer's work for a year: workload entries grouped by rubric category, plus the
publications they authored.

Years are Buddhist Era like `evaluation_round.academic_year`; `publication.publication_year`
is C.E., so a publication counts for academic year `publication_year + 543`.
Publications belong to the academic-work category (code 2 in rubric version 1), so they are
left out when another category is asked for.
"""

from uuid import UUID

from app.core.exceptions import ForbiddenError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.lecturer_work_dao import LecturerWorkDAO, WorkEntryRow
from app.v2.dtos.lecturer_work_dto import (
    LecturerWorkFilters,
    LecturerWorkQuery,
    LecturerWorkResponse,
    WorkCategoryGroup,
    WorkEntryResponse,
    WorkPublicationResponse,
)
from app.v2.security import Actor
from app.v2.services.access import signer_departments

BUDDHIST_ERA_OFFSET = 543
PUBLICATION_CATEGORY_CODE = "2"


class LecturerWorkService:
    def __init__(self, work_dao: LecturerWorkDAO, lecturer_dao: LecturerDAO) -> None:
        self.work_dao = work_dao
        self.lecturer_dao = lecturer_dao

    def get_work(
        self, lecturer_id: UUID, actor: Actor, query: LecturerWorkQuery
    ) -> LecturerWorkResponse:
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer not found")
        # The route lets in self, viewers and department signers; signers only for their own
        if not (
            actor.is_lecturer(lecturer_id)
            or actor.views_all
            or lecturer.department_id in signer_departments(actor)
        ):
            raise ForbiddenError("You may only see the work of lecturers in your department")

        rows = self.work_dao.list_entries(
            lecturer_id, academic_year=query.academic_year, category_code=query.category
        )
        groups: dict[str, WorkCategoryGroup] = {}
        for row in rows:
            group = groups.setdefault(
                row.category.code,
                WorkCategoryGroup(code=row.category.code, name_th=row.category.name_th, entries=[]),
            )
            group.entries.append(_entry(row))

        publications: list[WorkPublicationResponse] = []
        if query.category in (None, PUBLICATION_CATEGORY_CODE):
            year = query.academic_year
            publications = [
                WorkPublicationResponse(
                    publication_id=publication.publication_id,
                    title=publication.title,
                    publication_year=publication.publication_year,
                    academic_year=_to_buddhist_era(publication.publication_year),
                    venue=publication.venue,
                    doi=publication.doi,
                    author_order=author_order,
                )
                for publication, author_order in self.work_dao.list_publications(
                    lecturer_id,
                    publication_year=None if year is None else year - BUDDHIST_ERA_OFFSET,
                )
            ]

        years = set(self.work_dao.list_entry_years(lecturer_id)) | {
            year + BUDDHIST_ERA_OFFSET for year in self.work_dao.list_publication_years(lecturer_id)
        }
        category_name = (
            None if query.category is None else self.work_dao.get_category_name(query.category)
        )
        return LecturerWorkResponse(
            lecturer_id=lecturer.lecturer_id,
            lecturer_name_th=lecturer.name_th,
            filters=LecturerWorkFilters(
                academic_year=query.academic_year,
                category=query.category,
                category_name_th=category_name,
            ),
            categories=list(groups.values()),
            publications=publications,
            total=len(rows) + len(publications),
            available_years=sorted(years, reverse=True),
        )


def _entry(row: WorkEntryRow) -> WorkEntryResponse:
    return WorkEntryResponse(
        entry_id=row.entry.id,
        submission_id=row.submission.id,
        submission_status=row.submission.status,
        round_id=row.round.id,
        round_name_th=row.round.name_th,
        academic_year=row.round.academic_year,
        semester=row.round.semester,
        section_code=row.section.code,
        section_name_th=row.section.name_th,
        item_label_th=row.item.label_th,
        title=row.entry.title,
        course_code=row.entry.course_code,
        quantity=row.entry.quantity,
        score=row.entry.score,
    )


def _to_buddhist_era(year: int | None) -> int | None:
    return None if year is None else year + BUDDHIST_ERA_OFFSET
