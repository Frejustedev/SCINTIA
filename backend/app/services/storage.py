"""Object storage abstraction.

Heavy artifacts (raw DICOM, NIfTI, masks, annotated images, PDF) live in object
storage, not the database (docs/02_ARCHITECTURE.md). Phase 1 ships a local
volume-backed implementation behind an interface so MinIO/S3 can be added later
without touching callers.

Storage keys are forward-slash POSIX-style paths (e.g. ``studies/<id>/ct/...``);
they are sanitized so a key can never escape the storage root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath


class ObjectStorage(ABC):
    """Minimal content-addressable-ish blob store keyed by string paths."""

    @abstractmethod
    def save_bytes(self, key: str, data: bytes) -> str: ...

    @abstractmethod
    def read_bytes(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def delete_prefix(self, prefix: str) -> int: ...


def _safe_relative(key: str) -> PurePosixPath:
    """Normalize a key and refuse path traversal (``..`` / absolute)."""
    posix = PurePosixPath(key)
    if posix.is_absolute() or any(part == ".." for part in posix.parts):
        raise ValueError(f"Unsafe storage key: {key!r}")
    return posix


class LocalObjectStorage(ObjectStorage):
    """Stores blobs under a local root directory (one file per key)."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / Path(*_safe_relative(key).parts)

    def save_bytes(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def delete_prefix(self, prefix: str) -> int:
        base = self._path(prefix)
        if not base.exists():
            return 0
        count = 0
        for item in sorted(base.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
                count += 1
            elif item.is_dir():
                item.rmdir()
        if base.is_dir():
            base.rmdir()
        return count


def get_storage() -> ObjectStorage:
    """Return the configured object storage (local volume in Phase 1)."""
    from app.core.config import get_settings

    return LocalObjectStorage(get_settings().storage_dir)
