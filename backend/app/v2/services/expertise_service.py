"""Expertise: the shared master list, and each lecturer's set."""

from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.expertise_dao import ExpertiseDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageResponse
from app.v2.dtos.expertise_dto import (
    ExpertiseCreateRequest,
    ExpertiseListQuery,
    ExpertiseResponse,
    ExpertiseUpdateRequest,
    LecturerExpertiseReplaceRequest,
)
from app.v2.models.expertise import Expertise


class ExpertiseService:
    def __init__(self, expertise_dao: ExpertiseDAO, lecturer_dao: LecturerDAO) -> None:
        self.expertise_dao = expertise_dao
        self.lecturer_dao = lecturer_dao

    # --- master list ---------------------------------------------------------------

    def list_expertise(self, query: ExpertiseListQuery) -> PageResponse[ExpertiseResponse]:
        items, total = self.expertise_dao.find_page(
            q=query.q, limit=query.limit, offset=query.offset
        )
        return PageResponse(
            items=[ExpertiseResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def create_expertise(self, data: ExpertiseCreateRequest) -> ExpertiseResponse:
        self._reject_duplicate(data.description)
        expertise = self.expertise_dao.add(Expertise(description=data.description))
        return ExpertiseResponse.model_validate(expertise)

    def get_expertise(self, expertise_id: int) -> ExpertiseResponse:
        return ExpertiseResponse.model_validate(self._require_expertise(expertise_id))

    def update_expertise(
        self, expertise_id: int, data: ExpertiseUpdateRequest
    ) -> ExpertiseResponse:
        expertise = self._require_expertise(expertise_id)
        values = data.model_dump(exclude_unset=True, exclude_none=True)
        if "description" in values:
            self._reject_duplicate(values["description"], ignore_id=expertise_id)
        return ExpertiseResponse.model_validate(self.expertise_dao.update(expertise, values))

    def delete_expertise(self, expertise_id: int) -> None:
        # faculty_expertise rows go with it (ON DELETE CASCADE)
        self.expertise_dao.delete(self._require_expertise(expertise_id))

    # --- per lecturer ------------------------------------------------------------------

    def list_lecturer_expertise(self, lecturer_id: UUID) -> ListResponse[ExpertiseResponse]:
        self._require_lecturer(lecturer_id)
        items = [
            ExpertiseResponse.model_validate(item)
            for item in self.expertise_dao.list_by_lecturer(lecturer_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def replace_lecturer_expertise(
        self, lecturer_id: UUID, data: LecturerExpertiseReplaceRequest
    ) -> ListResponse[ExpertiseResponse]:
        self._require_lecturer(lecturer_id)
        for expertise_id in data.expertise_ids:
            if self.expertise_dao.get_by_id(expertise_id) is None:
                raise NotFoundError(f"Expertise {expertise_id} not found")

        self.expertise_dao.replace_for_lecturer(lecturer_id, data.expertise_ids)
        return self.list_lecturer_expertise(lecturer_id)

    def remove_lecturer_expertise(self, lecturer_id: UUID, expertise_id: int) -> None:
        self._require_lecturer(lecturer_id)
        self._require_expertise(expertise_id)
        if not self.expertise_dao.remove_from_lecturer(lecturer_id, expertise_id):
            raise NotFoundError("Lecturer does not have this expertise")

    # --- helpers -------------------------------------------------------------------------

    def _require_lecturer(self, lecturer_id: UUID) -> None:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

    def _require_expertise(self, expertise_id: int) -> Expertise:
        expertise = self.expertise_dao.get_by_id(expertise_id)
        if expertise is None:
            raise NotFoundError("Expertise not found")
        return expertise

    def _reject_duplicate(self, description: str, ignore_id: int | None = None) -> None:
        existing = self.expertise_dao.get_by_description(description)
        if existing is not None and existing.expertise_id != ignore_id:
            raise ConflictError("Expertise already exists")
