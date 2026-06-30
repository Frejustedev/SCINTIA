"""Application-level encryption for the patient re-identification table.

The real identity (name, birth date, ID) is stored encrypted in
``patient_identities`` and only ever decrypted locally at export time
(docs/05_CONTRAINTES_SECURITE.md). The key lives outside the database, in the
``IDENTITY_ENCRYPTION_KEY`` environment variable.

A valid 32-byte Fernet key is *derived* from that secret (SHA-256 → urlsafe
base64), so the env-var format is decoupled from Fernet's strict requirement and
any sufficiently random secret works.
"""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


def _fernet(key: str) -> Fernet:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_identity(identity: Mapping[str, Any], key: str) -> bytes:
    """Encrypt a patient identity mapping into an opaque token."""
    if not key:
        raise ValueError("IDENTITY_ENCRYPTION_KEY is required to encrypt identities.")
    payload = json.dumps(dict(identity), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return _fernet(key).encrypt(payload)


def decrypt_identity(token: bytes, key: str) -> dict[str, Any]:
    """Decrypt a token produced by :func:`encrypt_identity`."""
    if not key:
        raise ValueError("IDENTITY_ENCRYPTION_KEY is required to decrypt identities.")
    try:
        payload = _fernet(key).decrypt(token)
    except InvalidToken as exc:
        raise ValueError("Cannot decrypt identity: invalid key or corrupted data.") from exc
    result: dict[str, Any] = json.loads(payload)
    return result
