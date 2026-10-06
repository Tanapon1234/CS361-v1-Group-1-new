"""Reusable path parameters. Invalid IDs are rejected with 422 before any code runs."""

from typing import Annotated
from uuid import UUID

from fastapi import Path

# le=32767: these IDs are SMALLINT in the schema
LecturerId = Annotated[UUID, Path(description="Lecturer ID")]
EducationId = Annotated[int, Path(ge=1, le=32767, description="Education ID")]
ResearchInterestId = Annotated[int, Path(ge=1, le=32767, description="Research interest ID")]
ExpertiseId = Annotated[int, Path(ge=1, le=32767, description="Expertise ID")]
PublicationProfileId = Annotated[int, Path(ge=1, le=32767, description="Publication profile ID")]
PublicationId = Annotated[int, Path(ge=1, description="Publication ID")]
