"""Authentication endpoints: login (rate-limited, optional MFA), refresh, MFA mgmt."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import mfa
from app.core.audit import record_audit
from app.core.db import get_db
from app.core.ratelimit import rate_limit_login
from app.core.security import (
    CurrentUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import MfaCodeRequest, MfaSetupResponse, RefreshRequest, Token
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> Token:
    return Token(
        access_token=create_access_token(subject=str(user.id), role=user.role.value),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_login)])
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    otp: Annotated[str | None, Form()] = None,
) -> Token:
    user = db.scalar(select(User).where(User.email == form_data.username))
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.mfa_enabled and not mfa.verify(user.totp_secret or "", otp or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code MFA requis ou invalide."
        )
    record_audit(db, action="user.login", user_id=user.id)
    return _issue_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
    claims = decode_token(payload.refresh_token)
    if claims.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton de rafraîchissement invalide."
        )
    try:
        user_id = uuid.UUID(str(claims.get("sub")))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton invalide."
        ) from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inconnu.")
    return _issue_tokens(user)


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser) -> User:
    return current_user


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> MfaSetupResponse:
    """Generate a TOTP secret (inactive until a code is confirmed via /mfa/enable)."""
    secret = mfa.generate_secret()
    current_user.totp_secret = secret
    current_user.mfa_enabled = False
    db.flush()
    record_audit(db, action="mfa.setup", user_id=current_user.id)
    return MfaSetupResponse(
        secret=secret, otpauth_uri=mfa.provisioning_uri(secret, current_user.email)
    )


@router.post("/mfa/enable", response_model=UserRead)
def mfa_enable(
    payload: MfaCodeRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> User:
    if not current_user.totp_secret or not mfa.verify(current_user.totp_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code MFA invalide. Lancez d'abord la configuration.",
        )
    current_user.mfa_enabled = True
    db.flush()
    record_audit(db, action="mfa.enable", user_id=current_user.id)
    return current_user


@router.post("/mfa/disable", response_model=UserRead)
def mfa_disable(
    payload: MfaCodeRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> User:
    if not current_user.mfa_enabled or not mfa.verify(current_user.totp_secret or "", payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code MFA invalide.")
    current_user.mfa_enabled = False
    current_user.totp_secret = None
    db.flush()
    record_audit(db, action="mfa.disable", user_id=current_user.id)
    return current_user
