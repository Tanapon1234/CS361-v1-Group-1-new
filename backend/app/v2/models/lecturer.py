import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, timestamp_field


class Lecturer(SQLModel, table=True):
    __tablename__ = "lecturer"

    lecturer_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": sa.text("gen_random_uuid()")},
    )
    # Both nullable for now (added in 003): lecturers without a Cognito account / department yet
    cognito_sub: str | None = Field(default=None, max_length=64, unique=True)
    department_id: int | None = Field(
        default=None, sa_type=sa.SmallInteger, sa_column_args=[fk("department.id", cascade=False)]
    )
    name_th: str = Field(max_length=255)
    name_en: str | None = Field(default=None, max_length=255)
    rank: str | None = Field(default=None, max_length=100)
    profile_image_url: str | None = Field(default=None, sa_type=sa.Text)
    office: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    phone_extension: str | None = Field(default=None, max_length=50)
    email: str = Field(max_length=255, unique=True)
    cv_url: str | None = Field(default=None, sa_type=sa.Text)
    created_at: datetime | None = timestamp_field()
    updated_at: datetime | None = timestamp_field(auto_update=True)
    is_active: bool = Field(default=True, sa_column_kwargs={"server_default": sa.true()})
