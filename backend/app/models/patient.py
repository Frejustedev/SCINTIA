"""Pseudonymized patient and its isolated, encrypted real identity.

Clinical data is attached to a non-significant ``pseudonym``. The real identity
(name, birth date, ID) lives encrypted in a separate, access-restricted table and
is only decrypted locally at export time (docs/05_CONTRAINTES_SECURITE.md).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models._types import TimestampMixin
from app.models.base import Base


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pseudonym: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # Keyed HMAC of the source identity: links repeat exams of the same patient
    # without storing any plaintext identifier (app.core.crypto.linkage_digest).
    linkage_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    identity: Mapped[PatientIdentity | None] = relationship(
        back_populates="patient", uselist=False, cascade="all, delete-orphan"
    )


class PatientIdentity(TimestampMixin, Base):
    """Encrypted real identity. NEVER exposed by the analysis API or sent externally."""

    __tablename__ = "patient_identities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Encrypted blob (name + birth date + ID) — see app.core.crypto.
    identity_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="identity")
