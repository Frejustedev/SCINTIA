"""SPECT functional quantification formulas.

Deterministic, unit-tested conversions used by the quantification step. The actual
sampling of SPECT counts inside the CT-derived organ masks (registration + pixel
access) runs on real data; these are the underlying arithmetic.
"""

from __future__ import annotations


def counts_to_activity_mbq(counts_per_second: float, calibration_cps_per_mbq: float) -> float:
    """Convert a count rate to activity using the camera calibration factor."""
    if calibration_cps_per_mbq <= 0:
        raise ValueError("Le facteur de calibration doit être > 0 (cps/MBq).")
    return counts_per_second / calibration_cps_per_mbq


def pct_injected_activity(organ_activity_mbq: float, injected_activity_mbq: float) -> float:
    """Percent of injected activity (%AI) — the most standardized SPECT metric."""
    if injected_activity_mbq <= 0:
        raise ValueError("L'activité injectée doit être > 0 (MBq).")
    return organ_activity_mbq / injected_activity_mbq * 100.0


def lesion_to_background_ratio(lesion_intensity: float, background_intensity: float) -> float:
    """Standardized lesion-to-background ratio."""
    if background_intensity <= 0:
        raise ValueError("L'intensité de fond doit être > 0.")
    return lesion_intensity / background_intensity
