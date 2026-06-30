"""DICOM de-identification guarantees (app.services.anonymization).

These are the critical security tests for Phase 1: no PHI must survive, date
intervals must be preserved, and CT/SPECT linkage must hold.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydicom.dataset import Dataset

from app.services.anonymization import Deidentifier, deidentify_series

_STUDY_UID = "1.2.826.0.1.3680043.8.100"


def _make_dataset(*, series_uid: str, sop_uid: str, modality: str) -> Dataset:
    ds = Dataset()
    # Direct identifiers (PHI).
    ds.PatientName = "DOE^JOHN"
    ds.PatientID = "PID-12345"
    ds.PatientBirthDate = "19800101"
    ds.PatientSex = "M"  # clinically useful, not a direct identifier — kept
    ds.InstitutionName = "Hopital Central"
    ds.ReferringPhysicianName = "SMITH^ALICE"
    ds.OperatorsName = "TECH^BOB"
    ds.AccessionNumber = "ACC-987"
    ds.StudyID = "ST-1"
    # Linkage UIDs.
    ds.StudyInstanceUID = _STUDY_UID
    ds.SeriesInstanceUID = f"1.2.826.0.1.3680043.8.{series_uid}"
    ds.SOPInstanceUID = f"1.2.826.0.1.3680043.8.{sop_uid}"
    ds.FrameOfReferenceUID = "1.2.826.0.1.3680043.8.400"
    # Dates (one day apart, to test interval preservation).
    ds.StudyDate = "20240115"
    ds.AcquisitionDate = "20240116"
    ds.Modality = modality
    # A private tag that must be stripped.
    block = ds.private_block(0x0009, "ACME 1.0", create=True)
    block.add_new(0x01, "LO", "SECRET-VENDOR-VALUE")
    return ds


def test_direct_identifiers_are_blanked_or_removed() -> None:
    deid = Deidentifier(pseudonym="PSEUDO-1", date_offset_days=10)
    clean = deid.deidentify(_make_dataset(series_uid="201", sop_uid="301", modality="CT"))

    assert clean.PatientName == ""
    assert clean.PatientID == ""
    assert clean.PatientBirthDate == ""
    assert "InstitutionName" not in clean
    assert "ReferringPhysicianName" not in clean
    assert "OperatorsName" not in clean
    assert "AccessionNumber" not in clean
    assert "StudyID" not in clean
    # Clinical, non-identifying tag is preserved.
    assert clean.PatientSex == "M"
    # De-identification is marked.
    assert clean.PatientIdentityRemoved == "YES"


def test_no_residual_phi_in_dataset() -> None:
    deid = Deidentifier(pseudonym="PSEUDO-1", date_offset_days=10)
    clean = deid.deidentify(_make_dataset(series_uid="201", sop_uid="301", modality="CT"))
    dumped = str(clean)
    for leaked in ("DOE", "PID-12345", "Hopital", "SMITH", "ACC-987", "SECRET-VENDOR-VALUE"):
        assert leaked not in dumped


def test_private_tags_are_stripped() -> None:
    deid = Deidentifier(pseudonym="PSEUDO-1", date_offset_days=10)
    clean = deid.deidentify(_make_dataset(series_uid="201", sop_uid="301", modality="CT"))
    assert not any(elem.tag.is_private for elem in clean)


def test_dates_shifted_by_coherent_offset() -> None:
    offset = 37
    deid = Deidentifier(pseudonym="PSEUDO-1", date_offset_days=offset)
    clean = deid.deidentify(_make_dataset(series_uid="201", sop_uid="301", modality="CT"))

    new_study = datetime.strptime(clean.StudyDate, "%Y%m%d").date()
    new_acq = datetime.strptime(clean.AcquisitionDate, "%Y%m%d").date()
    original_study = datetime.strptime("20240115", "%Y%m%d").date()

    # Date is shifted...
    assert new_study != original_study
    assert (new_study - original_study).days == offset
    # ...and the 1-day interval (critical for multi-time-point dosimetry) is kept.
    assert (new_acq - new_study).days == 1


def test_ct_and_spect_stay_linked_but_uids_regenerated() -> None:
    ct = _make_dataset(series_uid="201", sop_uid="301", modality="CT")
    spect = _make_dataset(series_uid="202", sop_uid="302", modality="NM")

    cleaned, identity, _ = deidentify_series([ct, spect], pseudonym="PSEUDO-1", date_offset_days=5)
    clean_ct, clean_spect = cleaned

    # Study UID regenerated (no longer the original) ...
    assert clean_ct.StudyInstanceUID != _STUDY_UID
    # ... but identical across CT and SPECT (linkage preserved).
    assert clean_ct.StudyInstanceUID == clean_spect.StudyInstanceUID
    # Series UIDs remain distinct.
    assert clean_ct.SeriesInstanceUID != clean_spect.SeriesInstanceUID
    # Identity was captured from the series for the re-identification table.
    assert identity["PatientName"] == "DOE^JOHN"
    assert identity["PatientID"] == "PID-12345"


def test_input_dataset_is_not_mutated() -> None:
    original = _make_dataset(series_uid="201", sop_uid="301", modality="CT")
    Deidentifier(pseudonym="PSEUDO-1", date_offset_days=10).deidentify(original)
    assert original.PatientName == "DOE^JOHN"
    assert original.StudyInstanceUID == _STUDY_UID


def test_extract_identity_reads_phi() -> None:
    ds = _make_dataset(series_uid="201", sop_uid="301", modality="CT")
    identity = Deidentifier(pseudonym="P").extract_identity(ds)
    assert identity == {
        "PatientName": "DOE^JOHN",
        "PatientID": "PID-12345",
        "PatientBirthDate": "19800101",
        "PatientSex": "M",
    }


@pytest.mark.parametrize("offset", [-200, -1, 1, 200])
def test_offset_is_applied_consistently(offset: int) -> None:
    deid = Deidentifier(pseudonym="P", date_offset_days=offset)
    a = deid.deidentify(_make_dataset(series_uid="211", sop_uid="311", modality="CT"))
    b = deid.deidentify(_make_dataset(series_uid="212", sop_uid="312", modality="NM"))
    assert a.StudyDate == b.StudyDate  # same patient, same offset
