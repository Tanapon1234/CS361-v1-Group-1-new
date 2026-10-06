"""Table models (the "M" in MVC), mirroring database/migrations/
(002_lecturer_profile.sql + 003_faculty_workload.sql).

Every table module is imported here so `SQLModel.metadata` knows about all tables.
"""

from app.v2.models.department import Department
from app.v2.models.education import Education
from app.v2.models.expertise import Expertise, FacultyExpertise
from app.v2.models.lecturer import Lecturer
from app.v2.models.member_position import MemberPosition
from app.v2.models.publication import FacultyPublication, Publication
from app.v2.models.publication_profile import PublicationProfile
from app.v2.models.research_interest import FacultyResearchInterest, ResearchInterest
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection, RubricVersion
from app.v2.models.submission import (
    EntryAssessment,
    EntryEvidence,
    EvaluationRound,
    Submission,
    SubmissionApproval,
    SubmissionCategoryTotal,
    SubmissionEntry,
)

__all__ = [
    "Department",
    "Education",
    "EntryAssessment",
    "EntryEvidence",
    "EvaluationRound",
    "Expertise",
    "FacultyExpertise",
    "FacultyPublication",
    "FacultyResearchInterest",
    "Lecturer",
    "MemberPosition",
    "Publication",
    "PublicationProfile",
    "ResearchInterest",
    "RubricCategory",
    "RubricItem",
    "RubricSection",
    "RubricVersion",
    "Submission",
    "SubmissionApproval",
    "SubmissionCategoryTotal",
    "SubmissionEntry",
]
