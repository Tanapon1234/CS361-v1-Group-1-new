"""Expertise: the shared master list, and each lecturer's set."""

from uuid import UUID

from app.v2.daos.expertise_dao import ExpertiseDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.common import ListResponse, PageResponse
from app.v2.dtos.expertise_dto import (
    ExpertiseCreateRequest,
    ExpertiseListQuery,
    ExpertiseResponse,
    ExpertiseUpdateRequest,
    LecturerExpertiseReplaceRequest,
)


class ExpertiseService:
    def __init__(self, expertise_dao: ExpertiseDAO, lecturer_dao: LecturerDAO) -> None:
        self.expertise_dao = expertise_dao
        self.lecturer_dao = lecturer_dao

    # --- master list ---------------------------------------------------------------

    def list_expertise(self, query: ExpertiseListQuery) -> PageResponse[ExpertiseResponse]:
        raise NotImplementedError  # TODO

    def create_expertise(self, data: ExpertiseCreateRequest) -> ExpertiseResponse:
        raise NotImplementedError  # TODO

    def get_expertise(self, expertise_id: int) -> ExpertiseResponse:
        raise NotImplementedError  # TODO

    def update_expertise(
        self, expertise_id: int, data: ExpertiseUpdateRequest
    ) -> ExpertiseResponse:
        raise NotImplementedError  # TODO

    def delete_expertise(self, expertise_id: int) -> None:
        raise NotImplementedError  # TODO

    # --- per lecturer ------------------------------------------------------------------

    def list_lecturer_expertise(self, lecturer_id: UUID) -> ListResponse[ExpertiseResponse]:
        raise NotImplementedError  # TODO

    def replace_lecturer_expertise(
        self, lecturer_id: UUID, data: LecturerExpertiseReplaceRequest
    ) -> ListResponse[ExpertiseResponse]:
        raise NotImplementedError  # TODO: replace the whole set, return the new set

    def remove_lecturer_expertise(self, lecturer_id: UUID, expertise_id: int) -> None:
        raise NotImplementedError  # TODO
