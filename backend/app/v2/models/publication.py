import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk, timestamp_field


class Publication(SQLModel, table=True):
    __tablename__ = "publication"

    publication_id: int | None = identity_pk()
    title: str = Field(sa_type=sa.Text)
    publication_year: int | None = Field(default=None, sa_type=sa.SmallInteger)
    venue: str | None = Field(default=None, sa_type=sa.Text)
    volume: str | None = Field(default=None, max_length=50)
    pages: str | None = Field(default=None, max_length=50)
    doi: str | None = Field(default=None, max_length=255, unique=True)
    citation_text: str | None = Field(default=None, sa_type=sa.Text)
    created_at: datetime | None = timestamp_field()


class FacultyPublication(SQLModel, table=True):
    """Link table: authorship between lecturers and publications."""

    __tablename__ = "faculty_publication"

    lecturer_id: uuid.UUID = Field(primary_key=True, sa_column_args=[fk("lecturer.lecturer_id")])
    publication_id: int = Field(primary_key=True, sa_column_args=[fk("publication.publication_id")])
    author_order: int | None = Field(default=None, sa_type=sa.SmallInteger)
