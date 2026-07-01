"""Render a single DICOM frame to PNG for the in-browser viewer.

A lightweight, dependency-light viewer path: the server applies rescale and
window/level and returns a grayscale PNG, so the frontend needs no DICOM decoder.
(The richer Cornerstone3D viewer remains the production target — see DECISIONS.md.)
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
import pydicom
from PIL import Image


def _rescaled(dataset: pydicom.Dataset) -> np.ndarray:
    """Pixel array mapped to real units (HU for CT) via rescale slope/intercept."""
    pixels = dataset.pixel_array.astype(np.float32)
    slope = float(getattr(dataset, "RescaleSlope", 1) or 1)
    intercept = float(getattr(dataset, "RescaleIntercept", 0) or 0)
    return pixels * slope + intercept


def _first_float(value: Any, default: float) -> float:
    """First scalar of a possibly multi-valued DICOM element (WindowCenter/Width)."""
    if value is None:
        return default
    try:
        # MultiValue / list / tuple are iterable (but a str isn't a multi-value here).
        if hasattr(value, "__iter__") and not isinstance(value, str):
            return float(next(iter(value)))
        return float(value)
    except (TypeError, ValueError, StopIteration):
        return default


def extract_pixels(dicom_bytes: bytes) -> tuple[bytes, float, float]:
    """Return one frame as raw little-endian int16 (rescaled), plus its min/max.

    The browser applies window/level on these values, so windowing is instant and
    a real HU / count readout is possible client-side.
    """
    dataset = pydicom.dcmread(io.BytesIO(dicom_bytes))
    pixels = _rescaled(dataset)
    clipped = np.clip(np.rint(pixels), -32768, 32767).astype("<i2")
    return clipped.tobytes(), float(pixels.min()), float(pixels.max())


def series_pixel_meta(dicom_bytes: bytes) -> dict[str, Any]:
    """Per-series display metadata read from the first instance."""
    dataset = pydicom.dcmread(io.BytesIO(dicom_bytes))
    pixels = _rescaled(dataset)
    lo, hi = float(pixels.min()), float(pixels.max())
    wc = _first_float(dataset.get("WindowCenter"), (hi + lo) / 2.0)
    ww = _first_float(dataset.get("WindowWidth"), max(hi - lo, 1.0))
    spacing = dataset.get("PixelSpacing")
    pixel_spacing = [float(spacing[0]), float(spacing[1])] if spacing else None
    return {
        "rows": int(dataset.Rows),
        "cols": int(dataset.Columns),
        "window_center": wc,
        "window_width": ww,
        "min": lo,
        "max": hi,
        "pixel_spacing_mm": pixel_spacing,
        "photometric": str(dataset.get("PhotometricInterpretation", "MONOCHROME2")),
        "modality": str(dataset.get("Modality", "")),
        "inverted": str(dataset.get("PhotometricInterpretation", "")).upper() == "MONOCHROME1",
    }


def render_frame_png(
    dicom_bytes: bytes, *, window: float | None = None, level: float | None = None
) -> bytes:
    """Window/level a DICOM frame and encode it as an 8-bit grayscale PNG."""
    dataset = pydicom.dcmread(io.BytesIO(dicom_bytes))
    pixels = dataset.pixel_array.astype(np.float32)

    # Map stored values to real units (HU for CT) when rescale tags are present.
    slope = float(getattr(dataset, "RescaleSlope", 1) or 1)
    intercept = float(getattr(dataset, "RescaleIntercept", 0) or 0)
    pixels = pixels * slope + intercept

    # Default window/level spans the data range when not supplied by the client.
    data_min, data_max = float(pixels.min()), float(pixels.max())
    if level is None:
        level = (data_max + data_min) / 2.0
    if window is None:
        window = max(data_max - data_min, 1.0)

    low = level - window / 2.0
    high = level + window / 2.0
    if high <= low:
        high = low + 1.0
    normalized = np.clip((pixels - low) / (high - low), 0.0, 1.0)
    grayscale = (normalized * 255.0).astype(np.uint8)

    # MONOCHROME1 stores high values as dark — invert for natural display.
    if str(getattr(dataset, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        grayscale = 255 - grayscale

    buffer = io.BytesIO()
    Image.fromarray(grayscale, mode="L").save(buffer, format="PNG")
    return buffer.getvalue()
