import uuid

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk


class ResearchInterest(SQLModel, table=True):
    """Master list of research interests, shared by all lecturers."""

    __tablename__ = "research_interest"

    research_interest_id: int | None = identity_pk(sa.SmallInteger)
    name: str = Field(max_length=255, unique=True)


class FacultyResearchInterest(SQLModel, table=True):
    """Link table: which research interests a lecturer has."""

    __tablename__ = "faculty_research_interest"

    lecturer_id: uuid.UUID = Field(primary_key=True, sa_column_args=[fk("lecturer.lecturer_id")])
    research_interest_id: int = Field(
        primary_key=True,
        sa_type=sa.SmallInteger,
        sa_column_args=[fk("research_interest.research_interest_id")],
    )
