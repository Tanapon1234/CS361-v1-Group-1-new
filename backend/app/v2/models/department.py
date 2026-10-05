import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import identity_pk


class Department(SQLModel, table=True):
    """Master list of departments (สาขาวิชา), shared by lecturers and workload submissions."""

    __tablename__ = "department"

    id: int | None = identity_pk(sa.SmallInteger)
    code: str = Field(max_length=10, unique=True)
    name_th: str = Field(max_length=150)
    is_active: bool = True
