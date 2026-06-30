"""Append-only audit trail helper (docs/05_CONTRAINTES_SECURITE.md).

Sensitive actions are recorded here and never updated or deleted. All writers go
through :func:`record_audit` so no sensitive action bypasses the log.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    study_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Insert one audit entry (caller controls the surrounding transaction)."""
    entry = AuditLog(
        action=action,
        user_id=user_id,
        study_id=study_id,
        details=details,
        ip=ip,
    )
    db.add(entry)
    db.flush()
    return entry
