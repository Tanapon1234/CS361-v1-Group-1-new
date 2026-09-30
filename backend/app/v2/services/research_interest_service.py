"""Research interests: the shared master list, and each lecturer's set."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.dtos.common import ListResponse
from app.v2.dtos.research_interest_dto import (
    LecturerResearchInterestsReplaceRequest,
    LecturerResearchInterestListQuery,
    LecturerResearchInterestListResponse,
    ResearchInterestCreateRequest,
    ResearchInterestListResponse,
    ResearchInterestListQuery,
    ResearchInterestPagination,
    ResearchInterestResponse,
    ResearchInterestUpdateRequest,
)
from app.v2.models.research_interest import ResearchInterest


def _is_unique_violation(exc: IntegrityError) -> bool:
    sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    if sqlstate == "23505":
        return True
    return "unique constraint failed" in str(exc.orig).lower()


class ResearchInterestService:
    def __init__(
        self, research_interest_dao: ResearchInterestDAO, lecturer_dao: LecturerDAO
    ) -> None:
        self.research_interest_dao = research_interest_dao
        self.lecturer_dao = lecturer_dao

    # --- master list ---------------------------------------------------------------

    def list_research_interests(
        self, query: ResearchInterestListQuery
    ) -> ResearchInterestListResponse:
        offset = (query.page - 1) * query.limit
        items, total = self.research_interest_dao.find_page(
            search=query.search,
            limit=query.limit,
            offset=offset,
            sort_order=query.sort_order,
        )
        total_pages = (total + query.limit - 1) // query.limit if total else 0
        return ResearchInterestListResponse(
            data=[ResearchInterestResponse.model_validate(item) for item in items],
            pagination=ResearchInterestPagination(
                page=query.page,
                limit=query.limit,
                total=total,
                total_pages=total_pages,
            ),
        )

    def create_research_interest(
        self, data: ResearchInterestCreateRequest
    ) -> ResearchInterestResponse:
        if self.research_interest_dao.get_by_name(data.name) is not None:
            raise ConflictError("Research interest name already exists")

        try:
            research_interest = self.research_interest_dao.add(ResearchInterest(name=data.name))
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise ConflictError("Research interest name already exists") from exc
            raise

        return ResearchInterestResponse.model_validate(research_interest)

    def update_research_interest(
        self, research_interest_id: int, data: ResearchInterestUpdateRequest
    ) -> ResearchInterestResponse:
        raise NotImplementedError  # TODO

    def delete_research_interest(self, research_interest_id: int) -> None:
        raise NotImplementedError  # TODO

    # --- per lecturer ------------------------------------------------------------------

    def list_lecturer_research_interests(
        self, lecturer_id: UUID, query: LecturerResearchInterestListQuery
    ) -> LecturerResearchInterestListResponse:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

        items = self.research_interest_dao.list_by_lecturer(
            lecturer_id, search=query.search, sort_order=query.sort_order
        )
        return LecturerResearchInterestListResponse(
            data=[ResearchInterestResponse.model_validate(item) for item in items]
        )

    def replace_lecturer_research_interests(
        self, lecturer_id: UUID, data: LecturerResearchInterestsReplaceRequest
    ) -> ListResponse[ResearchInterestResponse]:
        raise NotImplementedError  # TODO: replace the whole set, return the new set

    def remove_lecturer_research_interest(
        self, lecturer_id: UUID, research_interest_id: int
    ) -> None:
        raise NotImplementedError  # TODO
