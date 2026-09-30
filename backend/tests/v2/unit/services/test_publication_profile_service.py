"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.dtos.publication_profile_dto import PublicationProfileUpdateRequest
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


def test_update_publication_profile_success(
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
    publication_profile_dao.get_by_identity.return_value = None

    def update(entity: PublicationProfile, values: dict[str, object]) -> PublicationProfile:
        entity.sqlmodel_update(values)
        return entity

    publication_profile_dao.update.side_effect = update

    result = service.update_publication_profile(
        lecturer_id,
        1,
        PublicationProfileUpdateRequest(provider="OpenAlex"),
    )

    assert result.provider == "OpenAlex"
    assert result.url == "https://orcid.org/0000-0002-1825-0097"
    publication_profile_dao.get_by_identity.assert_called_once_with(
        lecturer_id=lecturer_id,
        provider="OpenAlex",
        url="https://orcid.org/0000-0002-1825-0097",
    )
    publication_profile_dao.update.assert_called_once_with(profile, {"provider": "OpenAlex"})


def test_update_publication_profile_empty_body_is_noop(
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

    result = service.update_publication_profile(
        lecturer_id,
        1,
        PublicationProfileUpdateRequest(),
    )

    assert result.provider == "ORCID"
    publication_profile_dao.get_by_identity.assert_not_called()
    publication_profile_dao.update.assert_not_called()


def test_update_publication_profile_for_unknown_lecturer_raises_not_found(
    service: PublicationProfileService,
    publication_profile_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.update_publication_profile(
            uuid4(),
            1,
            PublicationProfileUpdateRequest(provider="OpenAlex"),
        )

    publication_profile_dao.get_by_id.assert_not_called()
    publication_profile_dao.update.assert_not_called()


@pytest.mark.parametrize("profile", [None, "wrong-owner"], ids=["missing", "wrong-owner"])
def test_update_missing_or_cross_owner_profile_raises_not_found(
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
        service.update_publication_profile(
            lecturer_id,
            1,
            PublicationProfileUpdateRequest(provider="OpenAlex"),
        )

    publication_profile_dao.update.assert_not_called()


def test_update_duplicate_publication_profile_raises_conflict(
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
    publication_profile_dao.get_by_identity.return_value = PublicationProfile(
        publication_profile_id=2,
        lecturer_id=lecturer_id,
        provider="Scopus",
        url="https://www.scopus.com/authid/detail.uri?authorId=123",
    )

    with pytest.raises(ConflictError, match="Publication profile already exists"):
        service.update_publication_profile(
            lecturer_id,
            1,
            PublicationProfileUpdateRequest(
                provider="Scopus",
                url="https://www.scopus.com/authid/detail.uri?authorId=123",
            ),
        )

    publication_profile_dao.update.assert_not_called()


def test_update_publication_profile_unique_race_raises_conflict(
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
    publication_profile_dao.get_by_identity.return_value = None
    unique_violation = Exception("duplicate")
    unique_violation.sqlstate = "23505"  # type: ignore[attr-defined]
    publication_profile_dao.update.side_effect = IntegrityError(
        "UPDATE publication_profile", {}, unique_violation
    )

    with pytest.raises(ConflictError, match="Publication profile already exists"):
        service.update_publication_profile(
            lecturer_id,
            1,
            PublicationProfileUpdateRequest(provider="OpenAlex"),
        )


def test_update_publication_profile_propagates_unexpected_write_error(
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
    publication_profile_dao.get_by_identity.return_value = None
    publication_profile_dao.update.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.update_publication_profile(
            lecturer_id,
            1,
            PublicationProfileUpdateRequest(provider="OpenAlex"),
        )
