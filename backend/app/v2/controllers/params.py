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
DepartmentId = Annotated[int, Path(ge=1, le=32767, description="Department ID")]
PositionId = Annotated[UUID, Path(description="Member position ID")]
RubricVersionId = Annotated[int, Path(ge=1, le=32767, description="Rubric version ID")]
RubricCategoryId = Annotated[int, Path(ge=1, le=32767, description="Rubric category ID")]
RubricSectionId = Annotated[int, Path(ge=1, le=32767, description="Rubric section ID")]
RubricItemId = Annotated[int, Path(ge=1, le=32767, description="Rubric item ID")]
RoundId = Annotated[int, Path(ge=1, le=32767, description="Evaluation round ID")]
SubmissionId = Annotated[UUID, Path(description="Submission ID")]
EntryId = Annotated[UUID, Path(description="Submission entry ID")]
EvidenceId = Annotated[UUID, Path(description="Evidence ID")]
