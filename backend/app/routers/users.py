"""User management (admin) and first-admin bootstrap."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.db import get_db
from app.core.security import hash_password, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


def _email_taken(db: Session, email: str) -> bool:
    count = db.scalar(select(func.count()).select_from(User).where(User.email == email)) or 0
    return count > 0


@router.post("/bootstrap-admin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    """Create the very first admin (only allowed when no user exists yet)."""
    total = db.scalar(select(func.count()).select_from(User)) or 0
    if total > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Des comptes existent déjà ; demandez à un administrateur.",
        )
    if payload.role is not Role.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le premier compte doit être administrateur.",
        )
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()
    record_audit(db, action="user.bootstrap", user_id=user.id)
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, require_roles(Role.admin)],
) -> User:
    if _email_taken(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé.")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()
    record_audit(db, action="user.create", user_id=admin.id, details={"created_user": str(user.id)})
    return user


@router.get("", response_model=list[UserRead])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, require_roles(Role.admin)],
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)))
