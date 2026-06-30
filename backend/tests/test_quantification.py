"""SPECT quantification formulas."""

from __future__ import annotations

import pytest

from app.services.quantification import (
    counts_to_activity_mbq,
    lesion_to_background_ratio,
    pct_injected_activity,
)


def test_counts_to_activity() -> None:
    assert counts_to_activity_mbq(2000.0, 100.0) == 20.0


def test_counts_to_activity_rejects_bad_calibration() -> None:
    with pytest.raises(ValueError):
        counts_to_activity_mbq(2000.0, 0.0)


def test_pct_injected_activity() -> None:
    assert pct_injected_activity(50.0, 200.0) == 25.0


def test_pct_injected_activity_rejects_zero_injected() -> None:
    with pytest.raises(ValueError):
        pct_injected_activity(50.0, 0.0)


def test_lesion_to_background_ratio() -> None:
    assert lesion_to_background_ratio(300.0, 100.0) == 3.0


def test_lesion_ratio_rejects_zero_background() -> None:
    with pytest.raises(ValueError):
        lesion_to_background_ratio(300.0, 0.0)
