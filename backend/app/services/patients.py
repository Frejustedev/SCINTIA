"""Patient pseudonymization.

Clinical data is attached to a non-significant pseudonym; the real identity is
encrypted into the isolated ``patient_identities`` table (docs/04, docs/05).
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_identity, linkage_digest
from app.models.patient import Patient, PatientIdentity


def generate_pseudonym() -> str:
    """A non-significant internal patient code."""
    return f"SC-{secrets.token_hex(6)}"


def create_pseudonymous_patient(
    db: Session,
    *,
    identity: Mapping[str, str],
    identity_key: str,
) -> Patient:
    """Create (or reuse) a pseudonymous patient and store its identity encrypted.

    When the identity carries a linkable identifier, repeat exams of the same
    person reuse the existing patient (longitudinal follow-up) instead of creating
    a duplicate.
    """
    digest = linkage_digest(identity, identity_key) if identity else None
    if digest is not None:
        existing = db.scalar(select(Patient).where(Patient.linkage_hash == digest))
        if existing is not None:
            return existing  # same patient across exams; identity already stored

    patient = Patient(pseudonym=generate_pseudonym(), linkage_hash=digest)
    db.add(patient)
    db.flush()
    if identity:
        db.add(
            PatientIdentity(
                patient_id=patient.id,
                identity_encrypted=encrypt_identity(identity, identity_key),
            )
        )
        db.flush()
    return patient
