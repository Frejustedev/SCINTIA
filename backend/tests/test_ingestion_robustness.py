"""Robustness of ingestion to real-world DICOM quirks."""

from __future__ import annotations

from pydicom.dataset import Dataset

from app.services.ingestion import _strip_group_lengths


def test_strip_group_lengths_removes_group_length_elements() -> None:
    ds = Dataset()
    ds.add_new(0x00080000, "UL", 100)  # a group-length element (element == 0x0000)
    ds.PatientName = "X"  # a normal element must survive

    # Nested sequence with its own group-length element.
    item = Dataset()
    item.add_new(0x00200000, "UL", 40)
    item.SeriesNumber = "1"
    ds.ReferencedImageSequence = [item]

    _strip_group_lengths(ds)

    assert 0x00080000 not in ds
    assert "PatientName" in ds
    assert 0x00200000 not in ds.ReferencedImageSequence[0]
    assert "SeriesNumber" in ds.ReferencedImageSequence[0]
