"""Public faculty directory: only what the website may show to anyone without signing in.

Phone and email are left out on purpose; contact is the office and extension.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from app.v3.dtos.base import ResponseDTO


class PublicImage(BaseModel):
    url: str
    alt: str | None = None


class PublicName(BaseModel):
    th: str
    en: str | None = None


class PublicCv(BaseModel):
    url: str


class PublicFacultySummary(ResponseDTO):
    id: UUID
    name: PublicName
    academic_position: str | None = None
    profile_image: PublicImage | None = None
    research_interests: list[str] = Field(default_factory=list)


class PublicFacultyList(ResponseDTO):
    data: list[PublicFacultySummary]


class PublicContact(BaseModel):
    office: str | None = None
    phone: str | None = None
    extension: str | None = None
    email: str | None = None


class PublicEducation(BaseModel):
    degree: str | None = None
    field: str | None = None
    institution: str | None = None
    country: str | None = None
    graduation_year: str | None = None
    additional_information: str | None = None


class PublicPublication(BaseModel):
    authors: list[str] | None = None
    title: str
    year: int | None = None
    venue: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    citation_text: str | None = None


class PublicProfileLink(BaseModel):
    provider: str
    url: str


class PublicFacultyDetail(ResponseDTO):
    id: UUID
    name: PublicName
    academic_position: str | None = None
    profile_image: PublicImage | None = None
    badges: list[PublicImage] = Field(default_factory=list)
    cv: PublicCv | None = None
    contact: PublicContact | None = None
    education: list[PublicEducation] = Field(default_factory=list)
    research_interests: list[str] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    selected_publications: list[PublicPublication] = Field(default_factory=list)
    publication_profiles: list[PublicProfileLink] = Field(default_factory=list)


class PublicFacultyDetailResponse(ResponseDTO):
    data: PublicFacultyDetail
