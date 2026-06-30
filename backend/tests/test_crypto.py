"""Identity encryption round-trip and key handling (app.core.crypto)."""

from __future__ import annotations

import pytest

from app.core.crypto import decrypt_identity, encrypt_identity

_KEY = "a-sufficiently-random-local-secret-0123456789"


def test_round_trip_recovers_identity() -> None:
    identity = {"PatientName": "DOE^JOHN", "PatientID": "12345", "PatientBirthDate": "19800101"}
    token = encrypt_identity(identity, _KEY)
    assert isinstance(token, bytes)
    assert decrypt_identity(token, _KEY) == identity


def test_ciphertext_hides_plaintext() -> None:
    token = encrypt_identity({"PatientName": "DOE^JOHN"}, _KEY)
    assert b"DOE" not in token


def test_wrong_key_fails() -> None:
    token = encrypt_identity({"PatientID": "12345"}, _KEY)
    with pytest.raises(ValueError):
        decrypt_identity(token, "another-key-entirely")


def test_empty_key_is_rejected() -> None:
    with pytest.raises(ValueError):
        encrypt_identity({"PatientID": "1"}, "")
    with pytest.raises(ValueError):
        decrypt_identity(b"whatever", "")
