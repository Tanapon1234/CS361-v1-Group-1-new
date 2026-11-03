"""Public faculty directory (no sign-in): active lecturers and their openly shown profile.

Read only. It never returns phone, email, department or anything about workload.
"""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.v2.models.lecturer import Lecturer
from app.v3.daos.education_dao import EducationDAO
from app.v3.daos.expertise_dao import ExpertiseDAO
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.publication_profile_dao import PublicationProfileDAO
from app.v3.daos.research_interest_dao import ResearchInterestDAO
from app.v3.dtos.public_faculty_dto import (
    PublicContact,
    PublicCv,
    PublicEducation,
    PublicFacultyDetail,
    PublicFacultyList,
    PublicFacultySummary,
    PublicImage,
    PublicName,
    PublicProfileLink,
    PublicPublication,
)
from app.v3.services.lecturer_file_service import LecturerFileService

LIST_LIMIT = 500
SELECTED_PUBLICATIONS = 20


class PublicFacultyService:
    def __init__(
        self,
        lecturer_dao: LecturerDAO,
        education_dao: EducationDAO,
        research_interest_dao: ResearchInterestDAO,
        expertise_dao: ExpertiseDAO,
        publication_dao: PublicationDAO,
        publication_profile_dao: PublicationProfileDAO,
        file_service: LecturerFileService,
    ) -> None:
        self.lecturer_dao = lecturer_dao
        self.education_dao = education_dao
        self.research_interest_dao = research_interest_dao
        self.expertise_dao = expertise_dao
        self.publication_dao = publication_dao
        self.publication_profile_dao = publication_profile_dao
        self.file_service = file_service

    def list_faculties(self) -> PublicFacultyList:
        lecturers, _ = self.lecturer_dao.find_page(
            q=None, is_active=True, limit=LIST_LIMIT, offset=0
        )
        return PublicFacultyList(data=[self._summary(lecturer) for lecturer in lecturers])

    def get_faculty(self, lecturer_id: UUID) -> PublicFacultyDetail:
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None or not lecturer.is_active:
            raise NotFoundError("Faculty not found")

        publications, _ = self.publication_dao.find_lecturer_page(
            lecturer_id, q=None, publication_year=None, limit=SELECTED_PUBLICATIONS, offset=0
        )
        cv_url = self._file_url(lecturer.cv_url, lecturer.lecturer_id, cv=True)
        summary = self._summary(lecturer)
        return PublicFacultyDetail(
            id=summary.id,
            name=summary.name,
            academic_position=summary.academic_position,
            profile_image=summary.profile_image,
            cv=PublicCv(url=cv_url) if cv_url else None,
            contact=PublicContact(office=lecturer.office, extension=lecturer.phone_extension),
            education=[
                PublicEducation(
                    degree=item.degree,
                    field=item.field,
                    institution=item.institution,
                    country=item.country,
                    graduation_year=item.graduation_year,
                )
                for item in self.education_dao.list_by_lecturer(lecturer_id)
            ],
            research_interests=summary.research_interests,
            expertise=[
                item.description for item in self.expertise_dao.list_by_lecturer(lecturer_id)
            ],
            selected_publications=[
                PublicPublication(
                    title=publication.title,
                    year=publication.publication_year,
                    venue=publication.venue,
                    volume=publication.volume,
                    pages=publication.pages,
                    doi=publication.doi,
                    citation_text=publication.citation_text,
                )
                for publication, _order in publications
            ],
            publication_profiles=[
                PublicProfileLink(provider=item.provider, url=item.url)
                for item in self.publication_profile_dao.list_by_lecturer(lecturer_id)
            ],
        )

    def _summary(self, lecturer: Lecturer) -> PublicFacultySummary:
        image_url = self._file_url(lecturer.profile_image_url, lecturer.lecturer_id, cv=False)
        return PublicFacultySummary(
            id=lecturer.lecturer_id,
            name=PublicName(th=lecturer.name_th, en=lecturer.name_en),
            academic_position=lecturer.rank,
            profile_image=PublicImage(url=image_url, alt=lecturer.name_th) if image_url else None,
            research_interests=[
                item.name
                for item in self.research_interest_dao.list_by_lecturer(lecturer.lecturer_id)
            ],
        )

    def _file_url(self, value: str | None, lecturer_id: UUID, *, cv: bool) -> str | None:
        if not value:
            return None
        download = (
            self.file_service.get_cv(lecturer_id)
            if cv
            else self.file_service.get_profile_image(lecturer_id)
        )
        return download.download_url
