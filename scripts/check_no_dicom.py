#!/usr/bin/env python3
"""Pre-commit guard: refuse to commit DICOM / medical image files.

Patient imaging is a red line (docs/05_CONTRAINTES_SECURITE.md). Real SPECT/CT
exports are often *extensionless* or use vendor extensions (.IMA), so matching on
the file name alone is not enough — we also sniff the DICOM magic bytes ("DICM"
at byte offset 128).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Case-insensitive name checks.
BLOCKED_SUFFIXES = {".dcm", ".dicom", ".ima", ".nii", ".nrrd", ".mha", ".mhd"}
BLOCKED_NAMES = {"dicomdir"}


def is_dicom_magic(path: Path) -> bool:
    """True if the file carries the DICOM preamble magic ("DICM" at offset 128)."""
    try:
        with path.open("rb") as fh:
            head = fh.read(132)
    except OSError:
        return False
    return len(head) >= 132 and head[128:132] == b"DICM"


def is_blocked(arg: str) -> bool:
    path = Path(arg)
    name = path.name.lower()
    joined_suffixes = "".join(path.suffixes).lower()
    return (
        path.suffix.lower() in BLOCKED_SUFFIXES
        or name in BLOCKED_NAMES
        or joined_suffixes.endswith(".nii.gz")
        or is_dicom_magic(path)
    )


def main(argv: list[str]) -> int:
    offenders = [arg for arg in argv if is_blocked(arg)]
    if offenders:
        sys.stderr.write(
            "Refusing to commit DICOM / medical image files - patient data "
            "(docs/05_CONTRAINTES_SECURITE.md):\n"
        )
        for offender in offenders:
            sys.stderr.write(f"  - {offender}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
