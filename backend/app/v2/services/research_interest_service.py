"""Research interests: the shared master list, and each lecturer's set."""

from uuid import UUID

from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.dtos.common import ListResponse, PageResponse
from app.v2.dtos.research_interest_dto import (
    LecturerResearchInterestsReplaceRequest,
    ResearchInterestCreateRequest,
    ResearchInterestListQuery,
    ResearchInterestResponse,
    ResearchInterestUpdateRequest,
)


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
        raise NotImplementedError  # TODO

    def create_research_interest(
        self, data: ResearchInterestCreateRequest
    ) -> ResearchInterestResponse:
        raise NotImplementedError  # TODO

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
        raise NotImplementedError  # TODO

    def replace_lecturer_research_interests(
        self, lecturer_id: UUID, data: LecturerResearchInterestsReplaceRequest
    ) -> ListResponse[ResearchInterestResponse]:
        raise NotImplementedError  # TODO: replace the whole set, return the new set

    def remove_lecturer_research_interest(
        self, lecturer_id: UUID, research_interest_id: int
    ) -> None:
        raise NotImplementedError  # TODO
