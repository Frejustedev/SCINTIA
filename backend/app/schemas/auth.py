"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    """OAuth2 bearer token (plus a refresh token) returned by login/refresh."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=10)
