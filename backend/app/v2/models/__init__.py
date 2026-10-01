"""Table models (the "M" in MVC), mirroring database/migrations/002_lecturer_profile.sql.

Every table module is imported here so `SQLModel.metadata` knows about all tables.
"""

from app.v2.models.education import Education
from app.v2.models.expertise import Expertise, FacultyExpertise
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication import FacultyPublication, Publication
from app.v2.models.publication_profile import PublicationProfile
from app.v2.models.research_interest import FacultyResearchInterest, ResearchInterest

__all__ = [
    "Education",
    "Expertise",
    "FacultyExpertise",
    "FacultyPublication",
    "FacultyResearchInterest",
    "Lecturer",
    "Publication",
    "PublicationProfile",
    "ResearchInterest",
]
