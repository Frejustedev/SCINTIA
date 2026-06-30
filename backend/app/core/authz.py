"""Per-study access control (RBAC scoping).

A study carries personal (pseudonymized) clinical data, so visibility is scoped:
the supervising clinicians (``medecin``) and the system ``admin`` see every study,
while a ``manipulateur`` or ``physicien`` sees only the studies they created. This
is a deliberately simple, mono-centre default; a finer policy (per service / per
site) can replace :func:`study_visibility_clause` without touching callers.

Endpoints use 404 (not 403) when a user may not see a study, so the existence of
another user's exam is never disclosed.
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, true

from app.models.enums import Role
from app.models.study import Study
from app.models.user import User

# Roles that may see every study (the validating physician and the administrator).
_FULL_VISIBILITY: frozenset[Role] = frozenset({Role.admin, Role.medecin})


def has_full_visibility(user: User) -> bool:
    """True if the user's role grants access to every study."""
    return user.role in _FULL_VISIBILITY


def can_view_study(user: User, study: Study) -> bool:
    """Whether ``user`` is allowed to see ``study``."""
    return has_full_visibility(user) or study.created_by == user.id


def study_visibility_clause(user: User) -> ColumnElement[bool]:
    """SQLAlchemy filter restricting a ``Study`` query to what ``user`` may see."""
    if has_full_visibility(user):
        return true()
    return Study.created_by == user.id
