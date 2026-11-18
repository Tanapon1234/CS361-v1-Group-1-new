"""Roles an admin grants from the app (013_user_role.sql)."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, timestamp_field


class UserRole(SQLModel, table=True):
    __tablename__ = "user_role"

    lecturer_id: uuid.UUID = Field(primary_key=True, sa_column_args=[fk("lecturer.lecturer_id")])
    role: str = Field(primary_key=True, max_length=20)
    granted_by: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    created_at: datetime = timestamp_field()
