import uuid

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk


class Expertise(SQLModel, table=True):
    """Master list of expertise, shared by all lecturers."""

    __tablename__ = "expertise"

    expertise_id: int | None = identity_pk(sa.SmallInteger)
    description: str = Field(sa_type=sa.Text)


class FacultyExpertise(SQLModel, table=True):
    """Link table: which expertise a lecturer has."""

    __tablename__ = "faculty_expertise"

    lecturer_id: uuid.UUID = Field(primary_key=True, sa_column_args=[fk("lecturer.lecturer_id")])
    expertise_id: int = Field(
        primary_key=True,
        sa_type=sa.SmallInteger,
        sa_column_args=[fk("expertise.expertise_id")],
    )
