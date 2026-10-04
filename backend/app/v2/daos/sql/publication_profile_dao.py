from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlmodel import select

from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.publication_profile import PublicationProfile


class SqlPublicationProfileDAO(SqlDAO, PublicationProfileDAO):
    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[PublicationProfile]:
        statement = (
            select(PublicationProfile)
            .where(PublicationProfile.lecturer_id == lecturer_id)
            .order_by(
                PublicationProfile.provider.asc(),
                PublicationProfile.publication_profile_id.asc(),
            )
        )
        return self.session.exec(statement).all()

    def get_by_id(self, publication_profile_id: int) -> PublicationProfile | None:
        raise NotImplementedError

    def add(self, profile: PublicationProfile) -> PublicationProfile:
        raise NotImplementedError

    def update(self, profile: PublicationProfile, values: Mapping[str, Any]) -> PublicationProfile:
        raise NotImplementedError

    def delete(self, profile: PublicationProfile) -> None:
        raise NotImplementedError
