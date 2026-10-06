"""Dependency wiring (composition root): Session -> DAO -> Service.

Controllers only use the `*ServiceDep` aliases. This file is the single place that picks
the concrete DAO / storage implementations, so tests can swap any layer with
`app.dependency_overrides[get_xxx] = ...`.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import SettingsDep, get_settings
from app.core.database import SessionDep
from app.v2.daos.education_dao import EducationDAO
from app.v2.daos.expertise_dao import ExpertiseDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.daos.sql.education_dao import SqlEducationDAO
from app.v2.daos.sql.expertise_dao import SqlExpertiseDAO
from app.v2.daos.sql.lecturer_dao import SqlLecturerDAO
from app.v2.daos.sql.publication_dao import SqlPublicationDAO
from app.v2.daos.sql.publication_profile_dao import SqlPublicationProfileDAO
from app.v2.daos.sql.research_interest_dao import SqlResearchInterestDAO
from app.v2.services.education_service import EducationService
from app.v2.services.expertise_service import ExpertiseService
from app.v2.services.lecturer_file_service import LecturerFileService
from app.v2.services.lecturer_service import LecturerService
from app.v2.services.publication_profile_service import PublicationProfileService
from app.v2.services.publication_service import PublicationService
from app.v2.services.research_interest_service import ResearchInterestService
from app.v2.storage.object_storage import ObjectStorage
from app.v2.storage.s3_object_storage import S3ObjectStorage

# --- Infrastructure (SessionDep / SettingsDep are shared, from app.core) ------------


@lru_cache
def get_object_storage() -> ObjectStorage:
    settings = get_settings()
    return S3ObjectStorage(bucket_name=settings.data_bucket_name, region=settings.aws_region)


ObjectStorageDep = Annotated[ObjectStorage, Depends(get_object_storage)]

# --- DAOs -------------------------------------------------------------------------


def get_lecturer_dao(session: SessionDep) -> LecturerDAO:
    return SqlLecturerDAO(session)


def get_education_dao(session: SessionDep) -> EducationDAO:
    return SqlEducationDAO(session)


def get_research_interest_dao(session: SessionDep) -> ResearchInterestDAO:
    return SqlResearchInterestDAO(session)


def get_expertise_dao(session: SessionDep) -> ExpertiseDAO:
    return SqlExpertiseDAO(session)


def get_publication_profile_dao(session: SessionDep) -> PublicationProfileDAO:
    return SqlPublicationProfileDAO(session)


def get_publication_dao(session: SessionDep) -> PublicationDAO:
    return SqlPublicationDAO(session)


LecturerDAODep = Annotated[LecturerDAO, Depends(get_lecturer_dao)]
EducationDAODep = Annotated[EducationDAO, Depends(get_education_dao)]
ResearchInterestDAODep = Annotated[ResearchInterestDAO, Depends(get_research_interest_dao)]
ExpertiseDAODep = Annotated[ExpertiseDAO, Depends(get_expertise_dao)]
PublicationProfileDAODep = Annotated[PublicationProfileDAO, Depends(get_publication_profile_dao)]
PublicationDAODep = Annotated[PublicationDAO, Depends(get_publication_dao)]

# --- Services ---------------------------------------------------------------------


def get_lecturer_service(lecturer_dao: LecturerDAODep) -> LecturerService:
    return LecturerService(lecturer_dao)


def get_lecturer_file_service(
    lecturer_dao: LecturerDAODep, storage: ObjectStorageDep, settings: SettingsDep
) -> LecturerFileService:
    return LecturerFileService(lecturer_dao, storage, settings)


def get_education_service(
    education_dao: EducationDAODep, lecturer_dao: LecturerDAODep
) -> EducationService:
    return EducationService(education_dao, lecturer_dao)


def get_research_interest_service(
    research_interest_dao: ResearchInterestDAODep, lecturer_dao: LecturerDAODep
) -> ResearchInterestService:
    return ResearchInterestService(research_interest_dao, lecturer_dao)


def get_expertise_service(
    expertise_dao: ExpertiseDAODep, lecturer_dao: LecturerDAODep
) -> ExpertiseService:
    return ExpertiseService(expertise_dao, lecturer_dao)


def get_publication_profile_service(
    publication_profile_dao: PublicationProfileDAODep, lecturer_dao: LecturerDAODep
) -> PublicationProfileService:
    return PublicationProfileService(publication_profile_dao, lecturer_dao)


def get_publication_service(
    publication_dao: PublicationDAODep, lecturer_dao: LecturerDAODep
) -> PublicationService:
    return PublicationService(publication_dao, lecturer_dao)


LecturerServiceDep = Annotated[LecturerService, Depends(get_lecturer_service)]
LecturerFileServiceDep = Annotated[LecturerFileService, Depends(get_lecturer_file_service)]
EducationServiceDep = Annotated[EducationService, Depends(get_education_service)]
ResearchInterestServiceDep = Annotated[
    ResearchInterestService, Depends(get_research_interest_service)
]
ExpertiseServiceDep = Annotated[ExpertiseService, Depends(get_expertise_service)]
PublicationProfileServiceDep = Annotated[
    PublicationProfileService, Depends(get_publication_profile_service)
]
PublicationServiceDep = Annotated[PublicationService, Depends(get_publication_service)]
