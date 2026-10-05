"""PostgreSQL enum types from 003_faculty_workload.sql.

Values are what the database stores; use them with `pg_enum(EnumClass, "type_name")`.
"""

from enum import StrEnum


class AcademicRank(StrEnum):
    """Only for `submission.rank_snapshot`; `lecturer.rank` stays free text."""

    LECTURER = "lecturer"
    ASST_PROF = "asst_prof"
    ASSOC_PROF = "assoc_prof"
    PROF = "prof"


class PositionCode(StrEnum):
    DEAN = "dean"
    VICE_DEAN = "vice_dean"
    ASST_DEAN = "asst_dean"
    EXEC_COMMITTEE = "exec_committee"
    DEPT_CHAIR = "dept_chair"
    DEPT_DEPUTY = "dept_deputy"
    DEPT_SECRETARY = "dept_secretary"
    DEPT_COMMITTEE = "dept_committee"


class SubmissionStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ASSESSING = "assessing"
    DEPT_REVIEW = "dept_review"
    RETURNED = "returned"
    DEPT_APPROVED = "dept_approved"
    SENT_TO_FACULTY = "sent_to_faculty"


class SignerRole(StrEnum):
    PERFORMER = "performer"
    RECEIVER = "receiver"
    DEPT_CHAIR = "dept_chair"
    DEPT_COMMITTEE = "dept_committee"


class ApprovalDecision(StrEnum):
    APPROVED = "approved"
    RETURNED = "returned"


class WeightMode(StrEnum):
    FIXED = "fixed"
    RANGED = "ranged"


class RangeBasis(StrEnum):
    WEIGHT = "weight"
    POINTS = "points"


class AssessmentAgg(StrEnum):
    NONE = "none"
    SINGLE = "single"
    AVERAGE = "average"


class QuantityUnit(StrEnum):
    CREDIT = "credit"
    TOPIC = "topic"
    COURSE = "course"
    HOUR = "hour"
    PERSON = "person"
    TERM = "term"


class DataSource(StrEnum):
    MANUAL = "manual"
    REGISTRAR = "registrar"
    REGISTRAR_EDITED = "registrar_edited"


class EvidenceStatus(StrEnum):
    PENDING = "pending"
    UPLOADED = "uploaded"
