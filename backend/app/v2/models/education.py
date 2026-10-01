import uuid

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk


class Education(SQLModel, table=True):
    __tablename__ = "education"

    education_id: int | None = identity_pk(sa.SmallInteger)
    lecturer_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id")])
    degree: str | None = Field(default=None, max_length=100)
    field: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    graduation_year: str | None = Field(default=None, max_length=10)
