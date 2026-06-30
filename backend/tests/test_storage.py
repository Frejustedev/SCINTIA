"""Local object storage behavior and path-traversal safety."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.storage import LocalObjectStorage


def test_round_trip_and_delete(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path / "obj")
    key = storage.save_bytes("studies/1/ct/slice.bin", b"hello")
    assert key == "studies/1/ct/slice.bin"
    assert storage.exists(key)
    assert storage.read_bytes(key) == b"hello"
    storage.delete(key)
    assert not storage.exists(key)


def test_rejects_path_traversal(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path / "obj")
    with pytest.raises(ValueError):
        storage.save_bytes("../escape.bin", b"x")
    with pytest.raises(ValueError):
        storage.save_bytes("/abs/escape.bin", b"x")


def test_delete_prefix_removes_subtree(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path / "obj")
    storage.save_bytes("studies/1/a.bin", b"a")
    storage.save_bytes("studies/1/sub/b.bin", b"b")
    storage.save_bytes("studies/2/c.bin", b"c")

    removed = storage.delete_prefix("studies/1")
    assert removed == 2
    assert not storage.exists("studies/1/a.bin")
    assert storage.exists("studies/2/c.bin")
