"""Time-based one-time passwords (TOTP, RFC 6238) for optional MFA.

Self-contained (no third-party dependency): standard HMAC-SHA1 TOTP compatible with
authenticator apps. Secrets are base32, stored per user and only used to verify codes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse

_DIGITS = 6
_STEP = 30


def generate_secret() -> str:
    """A random base32 TOTP secret (no padding), suitable for authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _hotp(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**_DIGITS)
    return str(code).zfill(_DIGITS)


def totp_now(secret: str) -> str:
    """The current TOTP code for ``secret`` (used by tests / setup verification)."""
    return _hotp(secret, int(time.time() // _STEP))


def verify(secret: str, code: str, *, window: int = 1) -> bool:
    """Constant-time check of ``code`` against ``secret`` (±``window`` steps of drift)."""
    if not secret or not code:
        return False
    counter = int(time.time() // _STEP)
    return any(
        hmac.compare_digest(_hotp(secret, counter + drift), code)
        for drift in range(-window, window + 1)
    )


def provisioning_uri(secret: str, email: str, issuer: str = "Scintia") -> str:
    """An otpauth:// URI to enroll the secret in an authenticator app."""
    label = urllib.parse.quote(f"{issuer}:{email}")
    query = urllib.parse.urlencode({"secret": secret, "issuer": issuer})
    return f"otpauth://totp/{label}?{query}"
