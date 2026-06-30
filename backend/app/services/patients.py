"""Patient pseudonymization.

Clinical data is attached to a non-significant pseudonym; the real identity is
encrypted into the isolated ``patient_identities`` table (docs/04, docs/05).
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.core.crypto import encrypt_identity
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
    """Create a patient and, if an identity is given, store it encrypted."""
    patient = Patient(pseudonym=generate_pseudonym())
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
