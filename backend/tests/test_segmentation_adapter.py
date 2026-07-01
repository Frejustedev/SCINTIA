"""TotalSegmentator adapter: statistics parsing and the no-GPU guard."""

from __future__ import annotations

import pytest

from app.services.segmentation import (
    OrganVolume,
    TotalSegmentatorSegmenter,
    parse_statistics,
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
