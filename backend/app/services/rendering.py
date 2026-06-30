"""Render a single DICOM frame to PNG for the in-browser viewer.

A lightweight, dependency-light viewer path: the server applies rescale and
window/level and returns a grayscale PNG, so the frontend needs no DICOM decoder.
(The richer Cornerstone3D viewer remains the production target — see DECISIONS.md.)
"""

from __future__ import annotations

import io

import numpy as np
import pydicom
from PIL import Image


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
