"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2 bearer token returned by the login endpoint."""

    access_token: str
    token_type: str = "bearer"
