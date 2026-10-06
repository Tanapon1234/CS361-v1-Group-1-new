from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_
from sqlmodel import select

from app.v2.daos.publication_dao import PublicationDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.publication import FacultyPublication, Publication


class SqlPublicationDAO(SqlDAO, PublicationDAO):
    def get_by_id(self, publication_id: int) -> Publication | None:
        return self.session.get(Publication, publication_id)

    def get_by_doi(self, doi: str) -> Publication | None:
        statement = select(Publication).where(Publication.doi == doi)
        return self.session.exec(statement).first()

    def find_page(
        self,
        *,
        q: str | None,
        publication_year: int | None,
        lecturer_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Publication], int]:
        statement = select(Publication)
        count_statement = select(func.count()).select_from(Publication)

        if lecturer_id is not None:
            statement = statement.join(FacultyPublication).where(
                FacultyPublication.lecturer_id == lecturer_id
            )
            count_statement = count_statement.join(FacultyPublication).where(
                FacultyPublication.lecturer_id == lecturer_id
            )

        if q:
            pattern = f"%{q}%"
            search_filter = or_(
                Publication.title.ilike(pattern),
                Publication.venue.ilike(pattern),
                Publication.doi.ilike(pattern),
            )
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        if publication_year is not None:
            statement = statement.where(Publication.publication_year == publication_year)
            count_statement = count_statement.where(
                Publication.publication_year == publication_year
            )

        total = self.session.exec(count_statement).one()
        publications = self.session.exec(
            statement.order_by(Publication.publication_id.asc()).offset(offset).limit(limit)
        ).all()
        return publications, total

    def add(self, publication: Publication) -> Publication:
        self.session.add(publication)
        self.session.flush()
        self.session.refresh(publication)
        return publication

    def find_lecturer_page(
        self,
        lecturer_id: UUID,
        *,
        q: str | None,
        publication_year: int | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[tuple[Publication, int | None]], int]:
        statement = (
            select(Publication, FacultyPublication.author_order)
            .join(FacultyPublication)
            .where(FacultyPublication.lecturer_id == lecturer_id)
        )
        count_statement = (
            select(func.count())
            .select_from(FacultyPublication)
            .join(Publication)
            .where(FacultyPublication.lecturer_id == lecturer_id)
        )

        if q:
            pattern = f"%{q}%"
            search_filter = or_(
                Publication.title.ilike(pattern),
                Publication.venue.ilike(pattern),
                Publication.doi.ilike(pattern),
            )
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        if publication_year is not None:
            statement = statement.where(Publication.publication_year == publication_year)
            count_statement = count_statement.where(
                Publication.publication_year == publication_year
            )

        total = self.session.exec(count_statement).one()
        rows = self.session.exec(
            statement.order_by(
                FacultyPublication.author_order.asc(),
                Publication.publication_id.asc(),
            )
            .offset(offset)
            .limit(limit)
        ).all()
        return rows, total

    def update(self, publication: Publication, values: Mapping[str, Any]) -> Publication:
        publication.sqlmodel_update(values)
        self.session.flush()
        self.session.refresh(publication)
        return publication

    def delete(self, publication: Publication) -> None:
        self.session.delete(publication)
        self.session.flush()

    def get_author_ids(self, publication_id: int) -> list[UUID]:
        raise NotImplementedError

    def set_authors(self, publication_id: int, lecturer_ids: Sequence[UUID]) -> None:
        raise NotImplementedError
