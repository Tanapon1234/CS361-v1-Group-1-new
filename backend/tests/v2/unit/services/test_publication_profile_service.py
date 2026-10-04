from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.dtos.publication_profile_dto import PublicationProfileCreateRequest
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


def test_list_publication_profiles_success(
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
    publication_profile_dao.list_by_lecturer.return_value = [
        PublicationProfile(
            publication_profile_id=1,
            lecturer_id=lecturer_id,
            provider="Google Scholar",
            url="https://scholar.google.com/citations?user=abc",
        ),
        PublicationProfile(
            publication_profile_id=2,
            lecturer_id=lecturer_id,
            provider="ORCID",
            url="https://orcid.org/0000-0002-1825-0097",
        ),
    ]

    result = service.list_publication_profiles(lecturer_id)

    assert [item.provider for item in result.items] == ["Google Scholar", "ORCID"]
    assert result.meta.count == 2
    lecturer_dao.get_by_id.assert_called_once_with(lecturer_id)
    publication_profile_dao.list_by_lecturer.assert_called_once_with(lecturer_id)


def test_list_publication_profiles_returns_empty_list(
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
    publication_profile_dao.list_by_lecturer.return_value = []

    result = service.list_publication_profiles(lecturer_id)

    assert result.items == []
    assert result.meta.count == 0


def test_list_for_unknown_lecturer_raises_not_found(
    service: PublicationProfileService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    lecturer_id = uuid4()
    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.list_publication_profiles(lecturer_id)

    lecturer_dao.get_by_id.assert_called_once_with(lecturer_id)
    service.publication_profile_dao.list_by_lecturer.assert_not_called()


def test_list_publication_profiles_propagates_query_error(
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
    publication_profile_dao.list_by_lecturer.side_effect = RuntimeError("query failed")

    with pytest.raises(RuntimeError, match="query failed"):
        service.list_publication_profiles(lecturer_id)


def test_create_publication_profile_success(
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
    publication_profile_dao.get_by_identity.return_value = None

    def add(profile: PublicationProfile) -> PublicationProfile:
        profile.publication_profile_id = 1
        return profile

    publication_profile_dao.add.side_effect = add
    data = PublicationProfileCreateRequest(
        provider="ORCID",
        url="https://orcid.org/0000-0002-1825-0097",
    )

    result = service.create_publication_profile(lecturer_id, data)

    assert result.publication_profile_id == 1
    assert result.lecturer_id == lecturer_id
    assert result.provider == "ORCID"
    publication_profile_dao.get_by_identity.assert_called_once_with(
        lecturer_id=lecturer_id,
        provider="ORCID",
        url="https://orcid.org/0000-0002-1825-0097",
    )
    added = publication_profile_dao.add.call_args.args[0]
    assert isinstance(added, PublicationProfile)
    assert added.url == "https://orcid.org/0000-0002-1825-0097"


def test_create_publication_profile_for_unknown_lecturer_raises_not_found(
    service: PublicationProfileService,
    publication_profile_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.create_publication_profile(
            uuid4(),
            PublicationProfileCreateRequest(
                provider="ORCID",
                url="https://orcid.org/0000-0002-1825-0097",
            ),
        )

    publication_profile_dao.get_by_identity.assert_not_called()
    publication_profile_dao.add.assert_not_called()


def test_create_duplicate_publication_profile_raises_conflict(
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
    publication_profile_dao.get_by_identity.return_value = PublicationProfile(
        publication_profile_id=1,
        lecturer_id=lecturer_id,
        provider="ORCID",
        url="https://orcid.org/0000-0002-1825-0097",
    )

    with pytest.raises(ConflictError, match="Publication profile already exists"):
        service.create_publication_profile(
            lecturer_id,
            PublicationProfileCreateRequest(
                provider="ORCID",
                url="https://orcid.org/0000-0002-1825-0097",
            ),
        )

    publication_profile_dao.add.assert_not_called()


def test_create_publication_profile_unique_race_raises_conflict(
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
    publication_profile_dao.get_by_identity.return_value = None
    unique_violation = Exception("duplicate")
    unique_violation.sqlstate = "23505"  # type: ignore[attr-defined]
    publication_profile_dao.add.side_effect = IntegrityError(
        "INSERT INTO publication_profile", {}, unique_violation
    )

    with pytest.raises(ConflictError, match="Publication profile already exists"):
        service.create_publication_profile(
            lecturer_id,
            PublicationProfileCreateRequest(
                provider="ORCID",
                url="https://orcid.org/0000-0002-1825-0097",
            ),
        )


def test_create_publication_profile_propagates_unexpected_write_error(
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
    publication_profile_dao.get_by_identity.return_value = None
    publication_profile_dao.add.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.create_publication_profile(
            lecturer_id,
            PublicationProfileCreateRequest(
                provider="ORCID",
                url="https://orcid.org/0000-0002-1825-0097",
            ),
        )
