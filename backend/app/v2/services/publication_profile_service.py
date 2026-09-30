from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.dtos.common import ListResponse
from app.v2.dtos.publication_profile_dto import (
    PublicationProfileCreateRequest,
    PublicationProfileResponse,
    PublicationProfileUpdateRequest,
)


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
        raise NotImplementedError  # TODO

    def create_publication_profile(
        self, lecturer_id: UUID, data: PublicationProfileCreateRequest
    ) -> PublicationProfileResponse:
        raise NotImplementedError  # TODO

    def update_publication_profile(
        self,
        lecturer_id: UUID,
        publication_profile_id: int,
        data: PublicationProfileUpdateRequest,
    ) -> PublicationProfileResponse:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

        profile = self.publication_profile_dao.get_by_id(publication_profile_id)
        if profile is None or profile.lecturer_id != lecturer_id:
            raise NotFoundError("Publication profile not found")

        values = data.model_dump(exclude_unset=True)
        if not values:
            return PublicationProfileResponse.model_validate(profile)

        provider = values.get("provider", profile.provider)
        url = values.get("url", profile.url)
        if (provider, url) != (profile.provider, profile.url):
            duplicate = self.publication_profile_dao.get_by_identity(
                lecturer_id=lecturer_id,
                provider=provider,
                url=url,
            )
            if duplicate is not None and duplicate.publication_profile_id != publication_profile_id:
                raise ConflictError("Publication profile already exists")

        try:
            updated = self.publication_profile_dao.update(profile, values)
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise ConflictError("Publication profile already exists") from exc
            raise

        return PublicationProfileResponse.model_validate(updated)

    def delete_publication_profile(self, lecturer_id: UUID, publication_profile_id: int) -> None:
        raise NotImplementedError  # TODO
