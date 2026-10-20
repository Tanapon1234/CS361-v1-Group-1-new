"""Public faculty directory for the website. No sign-in; see PublicFacultyService."""

from fastapi import APIRouter

from app.v3.controllers.params import LecturerId
from app.v3.dependencies import PublicFacultyServiceDep
from app.v3.dtos.public_faculty_dto import PublicFacultyDetailResponse, PublicFacultyList

router = APIRouter(prefix="/faculties", tags=["public"])


@router.get("")
def public_list_faculties(service: PublicFacultyServiceDep) -> PublicFacultyList:
    """Active lecturers: name, position, image and research interests."""
    return service.list_faculties()


@router.get("/{lecturer_id}")
def public_get_faculty(
    lecturer_id: LecturerId, service: PublicFacultyServiceDep
) -> PublicFacultyDetailResponse:
    """One active lecturer's public profile. Inactive or unknown ids are 404."""
    return PublicFacultyDetailResponse(data=service.get_faculty(lecturer_id))
