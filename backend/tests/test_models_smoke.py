"""Schema smoke test: the ORM maps cleanly and round-trips on SQLite."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Base,
    Patient,
    PatientIdentity,
    Report,
    ReportVersion,
    Study,
    StudySeries,
    User,
)
from app.models.enums import (
    ExamType,
    ReportStatus,
    ReportVersionKind,
    Role,
    SeriesKind,
    StudyStatus,
)


def test_schema_creates_and_round_trips() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            email="medecin@scintia.test",
            password_hash="not-a-real-hash",
            full_name="Dr Example",
            role=Role.medecin,
        )
        patient = Patient(pseudonym="PSEUDO-0001")
        patient.identity = PatientIdentity(identity_encrypted=b"encrypted-blob")
        session.add_all([user, patient])
        session.flush()

        study = Study(
            patient_id=patient.id,
            exam_type=ExamType.bone,
            status=StudyStatus.uploaded,
            created_by=user.id,
        )
        study.series.append(StudySeries(kind=SeriesKind.ct, storage_path="/objects/ct"))
        study.series.append(StudySeries(kind=SeriesKind.spect, storage_path="/objects/spect"))
        session.add(study)
        session.flush()

        report = Report(study_id=study.id, status=ReportStatus.draft)
        report.versions.append(
            ReportVersion(
                version_no=1,
                kind=ReportVersionKind.ai_draft,
                content="Brouillon généré par IA — à valider par le médecin.",
            )
        )
        session.add(report)
        session.add(AuditLog(user_id=user.id, study_id=study.id, action="study.upload"))
        session.commit()

        # Re-read and assert relationships hold.
        stored = session.get(Study, study.id)
        assert stored is not None
        assert stored.exam_type is ExamType.bone
        assert {s.kind for s in stored.series} == {SeriesKind.ct, SeriesKind.spect}
        assert stored.patient.identity is not None
        assert report.versions[0].kind is ReportVersionKind.ai_draft
        assert session.query(AuditLog).count() == 1
        assert session.query(User).first().created_at is not None
