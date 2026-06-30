"""Centralized enumerations shared across the data model.

Mirrors docs/04_MODELE_DONNEES.md §4. Values are the canonical strings stored in
the database (see ``pg_enum``).
"""

from __future__ import annotations

import enum


class Role(str, enum.Enum):
    """Application roles (RBAC, docs/05_CONTRAINTES_SECURITE.md)."""

    medecin = "medecin"
    physicien = "physicien"
    manipulateur = "manipulateur"
    admin = "admin"


class ExamType(str, enum.Enum):
    """The six covered exam types."""

    bone = "bone"
    myocardial_spect = "myocardial_spect"
    mibg = "mibg"
    octreotide = "octreotide"
    parathyroid = "parathyroid"
    lung_vq = "lung_vq"


class StudyStatus(str, enum.Enum):
    """Pipeline state machine for a study (docs/02_ARCHITECTURE.md)."""

    uploaded = "uploaded"
    anonymizing = "anonymizing"
    separating = "separating"
    converting = "converting"
    segmenting = "segmenting"
    registering = "registering"
    quantifying = "quantifying"
    dosimetry = "dosimetry"
    analyzing = "analyzing"
    generating_report = "generating_report"
    ready = "ready"
    error = "error"


class SeriesKind(str, enum.Enum):
    ct = "ct"
    spect = "spect"


class Isotope(str, enum.Enum):
    tc_99m = "Tc-99m"
    i_123 = "I-123"
    i_131 = "I-131"
    in_111 = "In-111"
    lu_177 = "Lu-177"


class ScoreType(str, enum.Enum):
    krenning = "krenning"
    curie = "curie"
    siopen = "siopen"
    pioped = "pioped"
    bsi = "bsi"
    lvef = "lvef"
    sss = "sss"
    srs = "srs"
    sds = "sds"
    tid = "tid"


class DosimetryMethod(str, enum.Enum):
    multi_timepoint = "multi_timepoint"
    single_timepoint = "single_timepoint"


class ReportStatus(str, enum.Enum):
    draft = "draft"
    edited = "edited"
    validated = "validated"


class ReportVersionKind(str, enum.Enum):
    ai_draft = "ai_draft"
    edited = "edited"
    validated = "validated"
