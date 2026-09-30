"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication_profile import PublicationProfile
from app.v2.services.publication_profile_service import PublicationProfileService


@pytest.fixture
def publication_profile_dao() -> MagicMock:
    return create_autospec(PublicationProfileDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(
    publication_profile_dao: MagicMock, lecturer_dao: MagicMock
) -> PublicationProfileService:
    return PublicationProfileService(publication_profile_dao, lecturer_dao)


@pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement GET publication profiles")
def test_list_for_unknown_lecturer_raises_not_found(
    service: PublicationProfileService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.list_publication_profiles(uuid4())


def make_profile(lecturer_id: object, publication_profile_id: int = 1) -> PublicationProfile:
    return PublicationProfile(
        publication_profile_id=publication_profile_id,
        lecturer_id=lecturer_id,
        provider="ORCID",
        url="https://orcid.org/0000-0002-1825-0097",
    )


def test_delete_publication_profile_success(
    service: PublicationProfileService,
    publication_profile_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
    )
    profile = make_profile(lecturer_id)
    publication_profile_dao.get_by_id.return_value = profile

    result = service.delete_publication_profile(lecturer_id, 1)

    assert result is None
    lecturer_dao.get_by_id.assert_called_once_with(lecturer_id)
    publication_profile_dao.get_by_id.assert_called_once_with(1)
    publication_profile_dao.delete.assert_called_once_with(profile)


def test_delete_publication_profile_for_unknown_lecturer_raises_not_found(
    service: PublicationProfileService,
    publication_profile_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.delete_publication_profile(uuid4(), 1)

    publication_profile_dao.get_by_id.assert_not_called()
    publication_profile_dao.delete.assert_not_called()


@pytest.mark.parametrize("profile", [None, "wrong-owner"], ids=["missing", "wrong-owner"])
def test_delete_missing_or_cross_owner_profile_raises_not_found(
    service: PublicationProfileService,
    publication_profile_dao: MagicMock,
    lecturer_dao: MagicMock,
    profile: str | None,
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
    )
    publication_profile_dao.get_by_id.return_value = (
        None if profile is None else make_profile(uuid4())
    )

    with pytest.raises(NotFoundError, match="Publication profile not found"):
        service.delete_publication_profile(lecturer_id, 1)

    publication_profile_dao.delete.assert_not_called()


def test_delete_publication_profile_propagates_delete_error(
    service: PublicationProfileService,
    publication_profile_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="สมชาย",
        email="somchai@example.ac.th",
    )
    publication_profile_dao.get_by_id.return_value = make_profile(lecturer_id)
    publication_profile_dao.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        service.delete_publication_profile(lecturer_id, 1)
