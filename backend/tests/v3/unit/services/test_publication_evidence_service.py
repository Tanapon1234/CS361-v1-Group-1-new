"""Attaching evidence to a publication (V4 FR4), with mocked DAOs and storage."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.v2.models.enums import EvidenceStatus, VerificationStatus
from app.v2.models.publication import Publication, PublicationEvidence
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.publication_evidence_dao import PublicationEvidenceDAO
from app.v3.dtos.publication_evidence_dto import (
    PublicationEvidenceCreateRequest,
    PublicationEvidenceUpdateRequest,
)
from app.v3.security import Actor, Role
from app.v3.services.publication_evidence_service import PublicationEvidenceService
from app.v3.storage.object_storage import (
    ObjectStorage,
    PresignedDownload,
    PresignedUpload,
    StoredObject,
)

AUTHOR = uuid4()
OTHER_LECTURER = uuid4()
AUTHOR_ACTOR = Actor(AUTHOR, frozenset({Role.LECTURER}))
OTHER_ACTOR = Actor(OTHER_LECTURER, frozenset({Role.LECTURER}))
STAFF_ACTOR = Actor(uuid4(), frozenset({Role.LECTURER, Role.STAFF}))
ROLE_ONLY_ACTOR = Actor(None, frozenset({Role.ADMIN}))


@pytest.fixture
def daos() -> dict[str, MagicMock]:
    return {
        "evidence": create_autospec(PublicationEvidenceDAO, instance=True),
        "publication": create_autospec(PublicationDAO, instance=True),
        "storage": create_autospec(ObjectStorage, instance=True),
    }


@pytest.fixture
def service(daos: dict[str, MagicMock]) -> PublicationEvidenceService:
    daos["evidence"].add.side_effect = lambda entity: entity
    daos["evidence"].update.side_effect = lambda entity, values: (
        entity.sqlmodel_update(values) or entity
    )
    return PublicationEvidenceService(
        daos["evidence"], daos["publication"], daos["storage"], Settings(_env_file=None)
    )


def publication(**values: object) -> Publication:
    defaults = {
        "publication_id": 1,
        "title": "A Paper",
        "verification_status": VerificationStatus.PENDING,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    return Publication(**(defaults | values))


def evidence(**values: object) -> PublicationEvidence:
    defaults = {
        "id": uuid4(),
        "publication_id": 1,
        "s3_key": "publications/1/abc.pdf",
        "file_name": "reprint.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1024,
        "status": EvidenceStatus.PENDING,
        "uploaded_by": AUTHOR,
    }
    return PublicationEvidence(**(defaults | values))


def create_request(**values: object) -> PublicationEvidenceCreateRequest:
    defaults = {"file_name": "reprint.pdf", "mime_type": "application/pdf", "size_bytes": 1024}
    return PublicationEvidenceCreateRequest(**(defaults | values))


class TestCreateEvidence:
    def test_unknown_publication_is_not_found(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            service.create_evidence(1, AUTHOR_ACTOR, create_request())

    def test_author_can_attach(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        daos["storage"].create_presigned_upload.return_value = PresignedUpload(
            url="https://s3", fields={}, expires_at=datetime(2026, 1, 1, tzinfo=UTC)
        )
        result = service.create_evidence(1, AUTHOR_ACTOR, create_request())
        assert result.evidence.uploaded_by == AUTHOR

    def test_non_author_non_staff_is_forbidden(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        with pytest.raises(ForbiddenError):
            service.create_evidence(1, OTHER_ACTOR, create_request())

    def test_staff_can_attach_without_being_an_author(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        daos["storage"].create_presigned_upload.return_value = PresignedUpload(
            url="https://s3", fields={}, expires_at=datetime(2026, 1, 1, tzinfo=UTC)
        )
        service.create_evidence(1, STAFF_ACTOR, create_request())  # does not raise

    def test_author_cannot_attach_once_verified(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication(
            verification_status=VerificationStatus.VERIFIED
        )
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        with pytest.raises(ForbiddenError):
            service.create_evidence(1, AUTHOR_ACTOR, create_request())

    def test_staff_can_attach_even_when_verified(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication(
            verification_status=VerificationStatus.VERIFIED
        )
        daos["storage"].create_presigned_upload.return_value = PresignedUpload(
            url="https://s3", fields={}, expires_at=datetime(2026, 1, 1, tzinfo=UTC)
        )
        service.create_evidence(1, STAFF_ACTOR, create_request())  # does not raise

    def test_role_only_caller_with_no_lecturer_id_is_unauthorized(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        with pytest.raises(UnauthorizedError):
            service.create_evidence(1, ROLE_ONLY_ACTOR, create_request())

    def test_disallowed_mime_type_is_a_bad_request(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        with pytest.raises(BadRequestError):
            service.create_evidence(
                1, AUTHOR_ACTOR, create_request(mime_type="application/x-msdownload")
            )

    def test_oversized_file_is_a_bad_request(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        huge = Settings(_env_file=None).evidence_max_bytes + 1
        with pytest.raises(BadRequestError):
            service.create_evidence(1, AUTHOR_ACTOR, create_request(size_bytes=huge))


class TestUpdateEvidence:
    def test_confirming_upload_requires_the_file_in_storage(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        daos["evidence"].get_by_id.return_value = evidence()
        daos["storage"].head_object.return_value = None
        with pytest.raises(BadRequestError):
            service.update_evidence(
                1,
                evidence().id,
                AUTHOR_ACTOR,
                PublicationEvidenceUpdateRequest(status=EvidenceStatus.UPLOADED),
                None,
            )

    def test_confirming_upload_uses_the_stored_size(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        row = evidence()
        daos["evidence"].get_by_id.return_value = row
        daos["storage"].head_object.return_value = StoredObject(
            key=row.s3_key, size_bytes=2048, content_type="application/pdf"
        )
        result = service.update_evidence(
            1,
            row.id,
            AUTHOR_ACTOR,
            PublicationEvidenceUpdateRequest(status=EvidenceStatus.UPLOADED),
            None,
        )
        assert result.size_bytes == 2048
        assert result.status is EvidenceStatus.UPLOADED

    def test_wrong_etag_is_precondition_failed(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        row = evidence()
        daos["evidence"].get_by_id.return_value = row
        from app.core.exceptions import PreconditionFailedError

        with pytest.raises(PreconditionFailedError):
            service.update_evidence(
                1, row.id, AUTHOR_ACTOR, PublicationEvidenceUpdateRequest(label="x"), '"stale-etag"'
            )

    def test_another_lecturers_evidence_id_on_this_publication_is_not_found(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["evidence"].get_by_id.return_value = evidence(publication_id=2)
        with pytest.raises(NotFoundError):
            service.update_evidence(
                1, uuid4(), AUTHOR_ACTOR, PublicationEvidenceUpdateRequest(label="x"), None
            )


class TestGetDownload:
    def test_not_uploaded_yet_is_a_conflict(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["evidence"].get_by_id.return_value = evidence(status=EvidenceStatus.PENDING)
        with pytest.raises(ConflictError):
            service.get_download(1, uuid4())

    def test_uploaded_file_gives_a_presigned_url(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["evidence"].get_by_id.return_value = evidence(status=EvidenceStatus.UPLOADED)
        daos["storage"].create_presigned_download.return_value = PresignedDownload(
            url="https://s3/download", expires_at=datetime(2026, 1, 1, tzinfo=UTC)
        )
        download = service.get_download(1, uuid4())
        assert download.url == "https://s3/download"


class TestDeleteEvidence:
    def test_deletes_the_row_and_the_s3_object(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        row = evidence()
        daos["evidence"].get_by_id.return_value = row

        service.delete_evidence(1, row.id, AUTHOR_ACTOR)

        daos["evidence"].delete.assert_called_once_with(row)
        daos["storage"].delete_object.assert_called_once_with(row.s3_key)

    def test_non_author_non_staff_cannot_delete(
        self, service: PublicationEvidenceService, daos: dict[str, MagicMock]
    ) -> None:
        daos["publication"].get_by_id.return_value = publication()
        daos["publication"].get_author_ids.return_value = [AUTHOR]
        daos["evidence"].get_by_id.return_value = evidence()
        with pytest.raises(ForbiddenError):
            service.delete_evidence(1, uuid4(), OTHER_ACTOR)
