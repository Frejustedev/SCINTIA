"""TotalSegmentator adapter: statistics parsing, mask volumes, and the no-GPU guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.segmentation import (
    OrganVolume,
    TotalSegmentatorSegmenter,
    parse_statistics,
    volumes_from_masks,
)


def test_parse_statistics_converts_mm3_to_ml_and_filters() -> None:
    stats = {
        "liver": {"volume": 1_500_000.0, "intensity": 50.0},
        "spleen": {"volume": 200_000.0},
        "air_pocket": {"volume": 0.0},  # dropped (non-positive)
        "no_volume": {"intensity": 12.0},  # dropped (no volume)
        "garbage": "not-a-mapping",  # dropped
    }
    result = parse_statistics(stats)
    assert result == [
        OrganVolume(organ_name="liver", volume_ml=1500.0),
        OrganVolume(organ_name="spleen", volume_ml=200.0),
    ]


def test_totalsegmentator_requires_the_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    # No silent fallback: when the tool is absent, segmentation must fail loudly.
    monkeypatch.setattr(TotalSegmentatorSegmenter, "_locate_binary", lambda self: None)
    with pytest.raises(RuntimeError, match="TotalSegmentator introuvable"):
        TotalSegmentatorSegmenter().segment([b"fake-dicom"])


def test_volumes_from_masks(tmp_path: Path) -> None:
    """Volume = non-zero voxels × voxel size; empty masks are dropped; mean HU sampled."""
    np = pytest.importorskip("numpy")
    sitk = pytest.importorskip("SimpleITK")

    ct = sitk.GetImageFromArray(np.full((4, 4, 4), 120, dtype=np.int16))
    ct.SetSpacing((1.0, 1.0, 1.0))
    ct_path = tmp_path / "ct.nii.gz"
    sitk.WriteImage(ct, str(ct_path))

    masks = tmp_path / "seg"
    masks.mkdir()
    liver = np.zeros((4, 4, 4), dtype=np.uint8)
    liver[0:2, 0:2, 0:2] = 1  # 8 voxels × 1 mm³ = 8 mm³ = 0.008 mL
    liver_img = sitk.GetImageFromArray(liver)
    liver_img.SetSpacing((1.0, 1.0, 1.0))
    sitk.WriteImage(liver_img, str(masks / "liver.nii.gz"))
    empty = sitk.GetImageFromArray(np.zeros((4, 4, 4), dtype=np.uint8))
    empty.SetSpacing((1.0, 1.0, 1.0))
    sitk.WriteImage(empty, str(masks / "spleen.nii.gz"))

    result = volumes_from_masks(ct_path, masks)
    assert result == [OrganVolume(organ_name="liver", volume_ml=0.008, mean_hu=120.0)]
