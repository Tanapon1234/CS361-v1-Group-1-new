"""Research interests: the shared master list, and each lecturer's set."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageResponse
from app.v2.dtos.research_interest_dto import (
    LecturerResearchInterestsReplaceRequest,
    ResearchInterestCreateRequest,
    ResearchInterestListQuery,
    ResearchInterestResponse,
    ResearchInterestUpdateRequest,
)
from app.v2.models.research_interest import ResearchInterest


class ResearchInterestService:
    def __init__(
        self, research_interest_dao: ResearchInterestDAO, lecturer_dao: LecturerDAO
    ) -> None:
        self.research_interest_dao = research_interest_dao
        self.lecturer_dao = lecturer_dao

    # --- master list ---------------------------------------------------------------

    def list_research_interests(
        self, query: ResearchInterestListQuery
    ) -> PageResponse[ResearchInterestResponse]:
        items, total = self.research_interest_dao.find_page(
            q=query.q,
            limit=query.limit,
            offset=query.offset,
        )
        return PageResponse(
            items=[ResearchInterestResponse.model_validate(item) for item in items],
            meta=PageMeta(
                total=total,
                limit=query.limit,
                offset=query.offset,
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
            raise ConflictError("Research interest name already exists") from exc

        return ResearchInterestResponse.model_validate(research_interest)

    def update_research_interest(
        self, research_interest_id: int, data: ResearchInterestUpdateRequest
    ) -> ResearchInterestResponse:
        raise NotImplementedError  # TODO

    def delete_research_interest(self, research_interest_id: int) -> None:
        raise NotImplementedError  # TODO

    # --- per lecturer ------------------------------------------------------------------

    def list_lecturer_research_interests(
        self, lecturer_id: UUID
    ) -> ListResponse[ResearchInterestResponse]:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

        items = [
            ResearchInterestResponse.model_validate(item)
            for item in self.research_interest_dao.list_by_lecturer(lecturer_id)
        ]
        return ListResponse(
            items=items,
            meta=ListMeta(count=len(items)),
        )

    def replace_lecturer_research_interests(
        self, lecturer_id: UUID, data: LecturerResearchInterestsReplaceRequest
    ) -> ListResponse[ResearchInterestResponse]:
        raise NotImplementedError  # TODO: replace the whole set, return the new set

    def remove_lecturer_research_interest(
        self, lecturer_id: UUID, research_interest_id: int
    ) -> None:
        raise NotImplementedError  # TODO
