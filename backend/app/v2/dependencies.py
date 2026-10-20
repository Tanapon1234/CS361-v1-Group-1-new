"""Dependency wiring (composition root): Session -> DAO -> Service.

Controllers only use the `*ServiceDep` aliases. This file is the single place that picks
the concrete DAO / storage implementations, so tests can swap any layer with
`app.dependency_overrides[get_xxx] = ...`.
"""

from datetime import date
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request

from app.core.cognito import CognitoTokenVerifier
from app.core.config import SettingsDep, get_settings
from app.core.database import SessionDep
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.v2.daos.assessment_dao import AssessmentDAO
from app.v2.daos.department_dao import DepartmentDAO
from app.v2.daos.education_dao import EducationDAO
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.expertise_dao import ExpertiseDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.lecturer_work_dao import LecturerWorkDAO
from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.daos.rubric_dao import RubricDAO
from app.v2.daos.sql.assessment_dao import SqlAssessmentDAO
from app.v2.daos.sql.department_dao import SqlDepartmentDAO
from app.v2.daos.sql.education_dao import SqlEducationDAO
from app.v2.daos.sql.evaluation_round_dao import SqlEvaluationRoundDAO
from app.v2.daos.sql.evidence_dao import SqlEvidenceDAO
from app.v2.daos.sql.expertise_dao import SqlExpertiseDAO
from app.v2.daos.sql.lecturer_dao import SqlLecturerDAO
from app.v2.daos.sql.lecturer_work_dao import SqlLecturerWorkDAO
from app.v2.daos.sql.member_position_dao import SqlMemberPositionDAO
from app.v2.daos.sql.publication_dao import SqlPublicationDAO
from app.v2.daos.sql.publication_profile_dao import SqlPublicationProfileDAO
from app.v2.daos.sql.research_interest_dao import SqlResearchInterestDAO
from app.v2.daos.sql.rubric_dao import SqlRubricDAO
from app.v2.daos.sql.submission_dao import SqlSubmissionDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.models.lecturer import Lecturer
from app.v2.permissions import rule_for
from app.v2.security import Actor, HeldPosition, Role, roles_from_names
from app.v2.services.assessment_service import AssessmentService
from app.v2.services.department_service import DepartmentService
from app.v2.services.education_service import EducationService
from app.v2.services.entry_service import EntryService
from app.v2.services.evidence_service import EvidenceService
from app.v2.services.expertise_service import ExpertiseService
from app.v2.services.lecturer_file_service import LecturerFileService
from app.v2.services.lecturer_service import LecturerService
from app.v2.services.lecturer_work_service import LecturerWorkService
from app.v2.services.me_service import MeService
from app.v2.services.position_service import PositionService
from app.v2.services.publication_profile_service import PublicationProfileService
from app.v2.services.publication_service import PublicationService
from app.v2.services.research_interest_service import ResearchInterestService
from app.v2.services.round_service import RoundService
from app.v2.services.rubric_service import RubricService
from app.v2.services.score_keeper import ScoreKeeper
from app.v2.services.submission_service import SubmissionService
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


def get_lecturer_work_dao(session: SessionDep) -> LecturerWorkDAO:
    return SqlLecturerWorkDAO(session)


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


def get_department_dao(session: SessionDep) -> DepartmentDAO:
    return SqlDepartmentDAO(session)


def get_member_position_dao(session: SessionDep) -> MemberPositionDAO:
    return SqlMemberPositionDAO(session)


def get_rubric_dao(session: SessionDep) -> RubricDAO:
    return SqlRubricDAO(session)


def get_evaluation_round_dao(session: SessionDep) -> EvaluationRoundDAO:
    return SqlEvaluationRoundDAO(session)


def get_submission_dao(session: SessionDep) -> SubmissionDAO:
    return SqlSubmissionDAO(session)


def get_assessment_dao(session: SessionDep) -> AssessmentDAO:
    return SqlAssessmentDAO(session)


def get_evidence_dao(session: SessionDep) -> EvidenceDAO:
    return SqlEvidenceDAO(session)


LecturerDAODep = Annotated[LecturerDAO, Depends(get_lecturer_dao)]
LecturerWorkDAODep = Annotated[LecturerWorkDAO, Depends(get_lecturer_work_dao)]
EducationDAODep = Annotated[EducationDAO, Depends(get_education_dao)]
ResearchInterestDAODep = Annotated[ResearchInterestDAO, Depends(get_research_interest_dao)]
ExpertiseDAODep = Annotated[ExpertiseDAO, Depends(get_expertise_dao)]
PublicationProfileDAODep = Annotated[PublicationProfileDAO, Depends(get_publication_profile_dao)]
PublicationDAODep = Annotated[PublicationDAO, Depends(get_publication_dao)]
DepartmentDAODep = Annotated[DepartmentDAO, Depends(get_department_dao)]
MemberPositionDAODep = Annotated[MemberPositionDAO, Depends(get_member_position_dao)]
RubricDAODep = Annotated[RubricDAO, Depends(get_rubric_dao)]
EvaluationRoundDAODep = Annotated[EvaluationRoundDAO, Depends(get_evaluation_round_dao)]
SubmissionDAODep = Annotated[SubmissionDAO, Depends(get_submission_dao)]
AssessmentDAODep = Annotated[AssessmentDAO, Depends(get_assessment_dao)]
EvidenceDAODep = Annotated[EvidenceDAO, Depends(get_evidence_dao)]

# --- Caller (docs/v2/permissions.md) ------------------------------------------------


@lru_cache
def get_token_verifier() -> CognitoTokenVerifier | None:
    settings = get_settings()
    if not (settings.cognito_user_pool_id and settings.cognito_client_id):
        return None
    return CognitoTokenVerifier(
        issuer=settings.cognito_issuer,
        client_id=settings.cognito_client_id,
        jwks_json=settings.cognito_jwks_json,
    )


TokenVerifierDep = Annotated[CognitoTokenVerifier | None, Depends(get_token_verifier)]


def get_actor(
    settings: SettingsDep,
    verifier: TokenVerifierDep,
    lecturer_dao: LecturerDAODep,
    position_dao: MemberPositionDAODep,
    authorization: Annotated[str | None, Header()] = None,
    x_lecturer_id: Annotated[
        UUID | None, Header(description="Dev only (not prod): act as this lecturer_id")
    ] = None,
    x_dev_roles: Annotated[
        str | None, Header(description="Dev only (not prod): extra roles, e.g. staff,admin")
    ] = None,
) -> Actor:
    """The caller, from the Cognito ID token, or from the dev headers outside prod."""
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise UnauthorizedError("Use `Authorization: Bearer <ID token>`")
        if verifier is None:
            raise UnauthorizedError("Sign-in is not configured on this server")
        claims = verifier.verify(token)
        lecturer = lecturer_dao.get_by_cognito_sub(claims["sub"]) or _link_by_email(
            lecturer_dao, claims
        )
        if not lecturer.is_active:
            raise ForbiddenError("This lecturer account is deactivated")
        groups = claims.get("cognito:groups") or []
        return Actor(
            lecturer.lecturer_id,
            roles_from_names(groups) | {Role.LECTURER},
            _positions_held(position_dao, lecturer.lecturer_id),
        )

    if settings.allows_dev_auth_header and (x_lecturer_id or x_dev_roles):
        roles = roles_from_names((x_dev_roles or "").split(","))
        if x_lecturer_id is None:
            return Actor(None, roles)
        return Actor(
            x_lecturer_id, roles | {Role.LECTURER}, _positions_held(position_dao, x_lecturer_id)
        )

    raise UnauthorizedError("Sign-in required")


def _positions_held(position_dao: MemberPositionDAO, lecturer_id: UUID) -> frozenset[HeldPosition]:
    return frozenset(
        HeldPosition(held.position, held.department_id)
        for held in position_dao.list_active(lecturer_id, date.today())
    )


def _link_by_email(lecturer_dao: LecturerDAO, claims: dict) -> Lecturer:
    """First sign-in: the lecturer record with the account's verified email gets its `sub`."""
    email = claims.get("email")
    if not email or claims.get("email_verified") not in (True, "true"):
        raise ForbiddenError("This account is not linked to a lecturer record")
    lecturer = lecturer_dao.get_by_email(email)
    if lecturer is None:
        raise ForbiddenError(f"No lecturer record has the email {email}; ask staff to add one")
    if lecturer.cognito_sub is not None:
        raise ForbiddenError("This lecturer is already linked to another account")
    return lecturer_dao.update(lecturer, {"cognito_sub": claims["sub"]})


CurrentActorDep = Annotated[Actor, Depends(get_actor)]


def authorize(request: Request, actor: CurrentActorDep) -> None:
    """Router-level check of docs/v2/permissions.md (ROUTE_RULES) for every /api/v2 call."""
    route = request.scope.get("route")
    rule = rule_for(request.method, getattr(route, "path", ""))
    if rule is None or not rule.allows(actor, request.path_params):
        raise ForbiddenError("You do not have permission to do this")


def get_current_lecturer_id(actor: CurrentActorDep) -> UUID:
    """The calling lecturer, for endpoints that act as a person (submissions, assessments)."""
    if actor.lecturer_id is None:
        raise UnauthorizedError("Sign in as a lecturer")
    return actor.lecturer_id


CurrentLecturerIdDep = Annotated[UUID, Depends(get_current_lecturer_id)]

# --- Services ---------------------------------------------------------------------


def get_lecturer_service(
    lecturer_dao: LecturerDAODep, department_dao: DepartmentDAODep
) -> LecturerService:
    return LecturerService(lecturer_dao, department_dao)


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


def get_lecturer_work_service(
    work_dao: LecturerWorkDAODep, lecturer_dao: LecturerDAODep
) -> LecturerWorkService:
    return LecturerWorkService(work_dao, lecturer_dao)


LecturerServiceDep = Annotated[LecturerService, Depends(get_lecturer_service)]
LecturerWorkServiceDep = Annotated[LecturerWorkService, Depends(get_lecturer_work_service)]
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


# --- Workload (SemesterReport) services --------------------------------------------


def get_score_keeper(
    rubric_dao: RubricDAODep,
    round_dao: EvaluationRoundDAODep,
    submission_dao: SubmissionDAODep,
    assessment_dao: AssessmentDAODep,
) -> ScoreKeeper:
    return ScoreKeeper(rubric_dao, round_dao, submission_dao, assessment_dao)


ScoreKeeperDep = Annotated[ScoreKeeper, Depends(get_score_keeper)]


def get_me_service(
    lecturer_dao: LecturerDAODep,
    position_dao: MemberPositionDAODep,
    round_dao: EvaluationRoundDAODep,
) -> MeService:
    return MeService(lecturer_dao, position_dao, round_dao)


def get_department_service(department_dao: DepartmentDAODep) -> DepartmentService:
    return DepartmentService(department_dao)


def get_position_service(
    position_dao: MemberPositionDAODep,
    lecturer_dao: LecturerDAODep,
    department_dao: DepartmentDAODep,
) -> PositionService:
    return PositionService(position_dao, lecturer_dao, department_dao)


def get_rubric_service(rubric_dao: RubricDAODep) -> RubricService:
    return RubricService(rubric_dao)


def get_round_service(
    round_dao: EvaluationRoundDAODep, rubric_dao: RubricDAODep, submission_dao: SubmissionDAODep
) -> RoundService:
    return RoundService(round_dao, rubric_dao, submission_dao)


def get_submission_service(
    submission_dao: SubmissionDAODep,
    round_dao: EvaluationRoundDAODep,
    lecturer_dao: LecturerDAODep,
    evidence_dao: EvidenceDAODep,
    storage: ObjectStorageDep,
    score_keeper: ScoreKeeperDep,
) -> SubmissionService:
    return SubmissionService(
        submission_dao, round_dao, lecturer_dao, evidence_dao, storage, score_keeper
    )


def get_entry_service(
    submission_dao: SubmissionDAODep,
    rubric_dao: RubricDAODep,
    lecturer_dao: LecturerDAODep,
    evidence_dao: EvidenceDAODep,
    storage: ObjectStorageDep,
    score_keeper: ScoreKeeperDep,
) -> EntryService:
    return EntryService(
        submission_dao, rubric_dao, lecturer_dao, evidence_dao, storage, score_keeper
    )


def get_assessment_service(
    assessment_dao: AssessmentDAODep,
    submission_dao: SubmissionDAODep,
    position_dao: MemberPositionDAODep,
    lecturer_dao: LecturerDAODep,
    score_keeper: ScoreKeeperDep,
) -> AssessmentService:
    return AssessmentService(
        assessment_dao, submission_dao, position_dao, lecturer_dao, score_keeper
    )


def get_evidence_service(
    evidence_dao: EvidenceDAODep,
    submission_dao: SubmissionDAODep,
    lecturer_dao: LecturerDAODep,
    storage: ObjectStorageDep,
    settings: SettingsDep,
) -> EvidenceService:
    return EvidenceService(evidence_dao, submission_dao, lecturer_dao, storage, settings)


MeServiceDep = Annotated[MeService, Depends(get_me_service)]
DepartmentServiceDep = Annotated[DepartmentService, Depends(get_department_service)]
PositionServiceDep = Annotated[PositionService, Depends(get_position_service)]
RubricServiceDep = Annotated[RubricService, Depends(get_rubric_service)]
RoundServiceDep = Annotated[RoundService, Depends(get_round_service)]
SubmissionServiceDep = Annotated[SubmissionService, Depends(get_submission_service)]
EntryServiceDep = Annotated[EntryService, Depends(get_entry_service)]
AssessmentServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]
EvidenceServiceDep = Annotated[EvidenceService, Depends(get_evidence_service)]
