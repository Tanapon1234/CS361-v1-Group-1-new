import uuid

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk


class PublicationProfile(SQLModel, table=True):
    """A lecturer's profile on an external site (e.g. Google Scholar, Scopus, ORCID)."""

    __tablename__ = "publication_profile"
    __table_args__ = (sa.Index(None, "lecturer_id", "provider", "url", unique=True),)

    publication_profile_id: int | None = identity_pk(sa.SmallInteger)
    lecturer_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id")])
    provider: str = Field(max_length=100)
    url: str = Field(sa_type=sa.Text)
