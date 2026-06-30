"""DICOM de-identification — the first, mandatory step before any processing.

Follows the spirit of the DICOM PS3.15 confidentiality profile
(docs/05_CONTRAINTES_SECURITE.md):

* direct identifiers are blanked (Type 2) or removed (Type 3);
* private tags are stripped;
* dates are *shifted by a coherent per-patient offset* (intervals preserved, so
  multi-time-point dosimetry stays valid) rather than deleted;
* instance UIDs are regenerated but kept *consistent via a mapping*, so the CT
  and SPECT of one study stay linked.

The captured real identity is returned to the caller, which encrypts it
(app.core.crypto) into the isolated ``patient_identities`` table. This module
never persists anything and never sends data anywhere.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterable, Sequence
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from pydicom.dataset import Dataset
from pydicom.uid import generate_uid

# Type-2 identifiers: keep the tag, blank the value.
_PHI_BLANK = {"PatientName", "PatientID", "PatientBirthDate"}

# Type-3 identifiers: remove the tag entirely.
_PHI_REMOVE = {
    "PatientAddress",
    "PatientTelephoneNumbers",
    "PatientMobileNumbers",
    "OtherPatientIDs",
    "OtherPatientIDsSequence",
    "OtherPatientNames",
    "PatientBirthName",
    "PatientMotherBirthName",
    "CountryOfResidence",
    "RegionOfResidence",
    "PatientReligiousPreference",
    "MilitaryRank",
    "BranchOfService",
    "ReferringPhysicianName",
    "ReferringPhysicianAddress",
    "ReferringPhysicianTelephoneNumbers",
    "ReferringPhysicianIdentificationSequence",
    "RequestingPhysician",
    "PerformingPhysicianName",
    "PerformingPhysicianIdentificationSequence",
    "NameOfPhysiciansReadingStudy",
    "PhysiciansOfRecord",
    "OperatorsName",
    "OperatorIdentificationSequence",
    "InstitutionName",
    "InstitutionAddress",
    "InstitutionalDepartmentName",
    "InstitutionCodeSequence",
    "StationName",
    "AccessionNumber",
    "StudyID",
    "IssuerOfPatientID",
    "AdmissionID",
    "IssuerOfAdmissionID",
    "CurrentPatientLocation",
    "PatientInsurancePlanCodeSequence",
}

# UIDs that identify an instance/study/series and must be regenerated (but NOT
# well-known UIDs such as SOPClassUID or TransferSyntaxUID).
_REMAP_UID_KEYWORDS = {
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
    "MediaStorageSOPInstanceUID",
    "FrameOfReferenceUID",
    "SynchronizationFrameOfReferenceUID",
    "ReferencedSOPInstanceUID",
    "ConcatenationUID",
    "IrradiationEventUID",
}

# Identity fields captured (before blanking) for the re-identification table.
_IDENTITY_KEYWORDS = (
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "OtherPatientIDs",
)

_DEID_METHOD = "Scintia de-identification (DICOM PS3.15-inspired)"


def _random_offset_days() -> int:
    """A non-zero offset in ±[30, 349] days."""
    return secrets.choice((-1, 1)) * (secrets.randbelow(320) + 30)


class Deidentifier:
    """De-identifies all datasets of a single patient with consistent state.

    Construct ONE instance per patient (or per study) and apply it to every
    dataset (CT, SPECT, multi-time-point), so UID remapping and the date offset
    stay coherent across the series.
    """

    def __init__(
        self,
        *,
        pseudonym: str,
        date_offset_days: int | None = None,
        uid_map: dict[str, str] | None = None,
    ) -> None:
        self.pseudonym = pseudonym
        self.date_offset = timedelta(
            days=date_offset_days if date_offset_days is not None else _random_offset_days()
        )
        self.uid_map: dict[str, str] = uid_map if uid_map is not None else {}

    # ── public API ──

    def extract_identity(self, ds: Dataset) -> dict[str, str]:
        """Capture the real identity BEFORE de-identification."""
        identity: dict[str, str] = {}
        for keyword in _IDENTITY_KEYWORDS:
            value = getattr(ds, keyword, None)
            if value not in (None, ""):
                identity[keyword] = str(value)
        return identity

    def deidentify(self, ds: Dataset) -> Dataset:
        """Return a de-identified deep copy of ``ds`` (the input is untouched)."""
        clean = deepcopy(ds)
        self._clean_level(clean)
        file_meta = getattr(clean, "file_meta", None)
        if file_meta is not None:
            self._clean_level(file_meta)
        clean.remove_private_tags()
        clean.PatientIdentityRemoved = "YES"
        clean.DeidentificationMethod = _DEID_METHOD
        return clean

    # ── internals ──

    def _clean_level(self, ds: Dataset) -> None:
        to_delete = []
        for elem in ds:
            keyword = elem.keyword
            if keyword in _PHI_REMOVE:
                to_delete.append(elem.tag)
                continue
            if keyword in _PHI_BLANK:
                elem.value = ""
                continue
            if elem.VR == "UI" and keyword in _REMAP_UID_KEYWORDS:
                elem.value = self._remap_uid(elem.value)
                continue
            if elem.VR == "DA":
                elem.value = self._shift_da(elem.value)
                continue
            if elem.VR == "DT":
                elem.value = self._shift_dt(elem.value)
                continue
            if elem.VR == "SQ":
                for item in elem.value:
                    self._clean_level(item)
        for tag in to_delete:
            del ds[tag]

    def _remap_uid(self, original: Any) -> str:
        key = str(original)
        if not key:
            return key
        if key not in self.uid_map:
            self.uid_map[key] = str(generate_uid())
        return self.uid_map[key]

    def _shift_da(self, value: Any) -> Any:
        text = str(value)
        if not text:
            return value
        try:
            parsed = datetime.strptime(text, "%Y%m%d").date()
        except ValueError:
            return value
        return (parsed + self.date_offset).strftime("%Y%m%d")

    def _shift_dt(self, value: Any) -> Any:
        text = str(value)
        if len(text) < 8:
            return value
        shifted_date = self._shift_da(text[:8])
        if shifted_date == text[:8]:
            return value
        return f"{shifted_date}{text[8:]}"


def deidentify_series(
    datasets: Iterable[Dataset],
    *,
    pseudonym: str,
    date_offset_days: int | None = None,
) -> tuple[list[Dataset], dict[str, str], Deidentifier]:
    """De-identify a patient's datasets together (shared UID map + date offset).

    Returns the cleaned datasets, the captured identity (from the first dataset),
    and the :class:`Deidentifier` (exposes ``uid_map`` / ``date_offset``).
    """
    deid = Deidentifier(pseudonym=pseudonym, date_offset_days=date_offset_days)
    materialized: Sequence[Dataset] = list(datasets)
    identity: dict[str, str] = {}
    cleaned: list[Dataset] = []
    for ds in materialized:
        if not identity:
            identity = deid.extract_identity(ds)
        cleaned.append(deid.deidentify(ds))
    return cleaned, identity, deid
