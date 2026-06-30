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
import hmac
import json
from collections.abc import Mapping
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


def _fernet(key: str) -> Fernet:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def linkage_digest(identity: Mapping[str, Any], key: str) -> str | None:
    """A deterministic, keyed digest linking exams of the same patient.

    HMAC-SHA256 over the source patient ID (or name + birth date), keyed by the
    identity secret. It is not reversible without the key and lets repeat exams of
    the same person reuse one pseudonymous patient — without storing any plaintext
    identifier. Returns ``None`` when there is nothing to link on.
    """
    if not key:
        return None
    patient_id = identity.get("PatientID")
    if patient_id:
        source = f"id:{patient_id}"
    elif identity.get("PatientName"):
        source = f"nb:{identity.get('PatientName')}|{identity.get('PatientBirthDate') or ''}"
    else:
        return None
    return hmac.new(key.encode("utf-8"), source.encode("utf-8"), hashlib.sha256).hexdigest()


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
