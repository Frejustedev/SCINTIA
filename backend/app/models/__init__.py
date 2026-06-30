"""ORM models. Importing this package registers every table on ``Base.metadata``.

The data model (15 tables, built around patient pseudonymization and audit) is
defined in docs/04_MODELE_DONNEES.md.
"""

from __future__ import annotations

from app.models.audit import AuditLog
from app.models.base import Base
from app.models.clinical import (
    DosimetryResult,
    ExamScore,
    Lesion,
    OrganMeasurement,
    Treatment,
)
from app.models.device import CalibrationFactor, Device
from app.models.patient import Patient, PatientIdentity
from app.models.report import Report, ReportVersion
from app.models.study import Study, StudySeries
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Patient",
    "PatientIdentity",
    "Device",
    "CalibrationFactor",
    "Study",
    "StudySeries",
    "OrganMeasurement",
    "Lesion",
    "ExamScore",
    "DosimetryResult",
    "Treatment",
    "Report",
    "ReportVersion",
    "AuditLog",
]
