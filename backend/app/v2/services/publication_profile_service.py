from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.publication_profile_dto import (
    PublicationProfileCreateRequest,
    PublicationProfileResponse,
    PublicationProfileUpdateRequest,
)
from app.v2.models.publication_profile import PublicationProfile


def _is_unique_violation(exc: IntegrityError) -> bool:
    sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    if sqlstate == "23505":
        return True
    return "unique constraint failed" in str(exc.orig).lower()


class PublicationProfileService:
    def __init__(
        self, publication_profile_dao: PublicationProfileDAO, lecturer_dao: LecturerDAO
    ) -> None:
        self.publication_profile_dao = publication_profile_dao
        self.lecturer_dao = lecturer_dao

    def list_publication_profiles(
        self, lecturer_id: UUID
    ) -> ListResponse[PublicationProfileResponse]:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

        items = [
            PublicationProfileResponse.model_validate(item)
            for item in self.publication_profile_dao.list_by_lecturer(lecturer_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_publication_profile(
        self, lecturer_id: UUID, data: PublicationProfileCreateRequest
    ) -> PublicationProfileResponse:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

        if (
            self.publication_profile_dao.get_by_identity(
                lecturer_id=lecturer_id,
                provider=data.provider,
                url=data.url,
            )
            is not None
        ):
            raise ConflictError("Publication profile already exists")

        try:
            profile = self.publication_profile_dao.add(
                PublicationProfile(
                    lecturer_id=lecturer_id,
                    provider=data.provider,
                    url=data.url,
                )
            )
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise ConflictError("Publication profile already exists") from exc
            raise

        return PublicationProfileResponse.model_validate(profile)

    def update_publication_profile(
        self,
        lecturer_id: UUID,
        publication_profile_id: int,
        data: PublicationProfileUpdateRequest,
    ) -> PublicationProfileResponse:
        raise NotImplementedError  # TODO

    def delete_publication_profile(self, lecturer_id: UUID, publication_profile_id: int) -> None:
        raise NotImplementedError  # TODO
