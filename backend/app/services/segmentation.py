"""Anatomical segmentation of the CT, producing per-organ volumes.

TotalSegmentator needs a GPU and is heavy, so it sits behind a :class:`Segmenter`
interface with two implementations:

* :class:`StubSegmenter` — deterministic, dependency-free; lets the whole pipeline
  run and be tested offline (no GPU). It returns a representative skeletal set with
  plausible volumes — clearly NOT real measurements.
* :class:`TotalSegmentatorSegmenter` — the real adapter (subprocess), used on a GPU
  machine. Selected via ``SEGMENTER_BACKEND=totalsegmentator``.

Manual correction of masks remains mandatory before clinical use
(docs/01_SPECIFICATIONS.md §C).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.clinical import OrganMeasurement
from app.models.enums import SeriesKind, StudyStatus
from app.models.study import Study
from app.services.storage import ObjectStorage

logger = get_logger(__name__)

# TotalSegmentator --statistics reports per-ROI "volume"; convert to millilitres.
# NOTE: the source unit must be confirmed against the installed TotalSegmentator
# version on the GPU host (assumed mm³ here); validate before clinical use.
_VOLUME_MM3_PER_ML = 1000.0


@dataclass(frozen=True)
class OrganVolume:
    organ_name: str
    volume_ml: float
    snomed_code: str | None = None
    mean_hu: float | None = None


def volumes_from_masks(ct_nifti: Path, mask_dir: Path) -> list[OrganVolume]:
    """Measure each organ mask: volume (voxels × voxel size, mL) + mean HU in the CT.

    Used instead of TotalSegmentator's ``--statistics``, which returns 0 volumes with
    the ``--fast`` model even when the masks are correctly populated.
    """
    import numpy as np
    import SimpleITK as sitk  # noqa: N813 - conventional alias

    ct = sitk.GetArrayFromImage(sitk.ReadImage(str(ct_nifti)))
    volumes: list[OrganVolume] = []
    for mask_file in sorted(mask_dir.glob("*.nii.gz")):
        image = sitk.ReadImage(str(mask_file))
        mask = sitk.GetArrayFromImage(image) > 0
        voxels = int(mask.sum())
        if voxels == 0:
            continue
        voxel_ml = float(np.prod(image.GetSpacing())) / 1000.0
        mean_hu = float(ct[mask].mean()) if ct.shape == mask.shape else None
        volumes.append(
            OrganVolume(
                organ_name=mask_file.name.removesuffix(".nii.gz"),
                volume_ml=round(voxels * voxel_ml, 3),
                mean_hu=round(mean_hu, 1) if mean_hu is not None else None,
            )
        )
    return sorted(volumes, key=lambda v: v.organ_name)


def parse_statistics(stats: Mapping[str, Any]) -> list[OrganVolume]:
    """Parse a TotalSegmentator ``statistics.json`` mapping into organ volumes (mL)."""
    volumes: list[OrganVolume] = []
    for organ, metrics in stats.items():
        if not isinstance(metrics, Mapping):
            continue
        raw_volume = metrics.get("volume")
        if raw_volume is None:
            continue
        volume_ml = float(raw_volume) / _VOLUME_MM3_PER_ML
        if volume_ml <= 0:
            continue
        volumes.append(OrganVolume(organ_name=str(organ), volume_ml=round(volume_ml, 3)))
    return sorted(volumes, key=lambda v: v.organ_name)


def dicom_series_to_nifti(ct_instances: list[bytes], out_path: Path) -> None:
    """Convert in-memory CT DICOM instances to a single NIfTI volume (SimpleITK).

    The geometry (orientation / spacing) is preserved by reading the series through
    SimpleITK's GDCM reader, which is required for a correct segmentation.
    """
    try:
        import SimpleITK as sitk  # noqa: N813 - conventional alias
    except ImportError as exc:  # pragma: no cover - depends on the GPU host
        raise RuntimeError(
            "SimpleITK requis pour la conversion DICOM→NIfTI (pip install SimpleITK)."
        ) from exc

    with tempfile.TemporaryDirectory() as tmp:  # pragma: no cover - GPU host
        tmpdir = Path(tmp)
        for index, blob in enumerate(ct_instances):
            (tmpdir / f"{index:05d}.dcm").write_bytes(blob)
        reader = sitk.ImageSeriesReader()
        series_ids = reader.GetGDCMSeriesIDs(str(tmpdir))
        if not series_ids:
            raise RuntimeError("Aucune série DICOM lisible pour la conversion NIfTI.")
        reader.SetFileNames(reader.GetGDCMSeriesFileNames(str(tmpdir), series_ids[0]))
        sitk.WriteImage(reader.Execute(), str(out_path))


class Segmenter(ABC):
    """Segments a CT (as a list of DICOM instance blobs) into organ volumes."""

    name: str = "abstract"

    @abstractmethod
    def segment(self, ct_instances: list[bytes]) -> list[OrganVolume]: ...


# A representative skeletal set for bone scintigraphy (TotalSegmentator names).
# Volumes are plausible placeholders, NOT measurements — the stub never reads pixels.
_STUB_SKELETON: tuple[tuple[str, float], ...] = (
    ("skull", 620.0),
    ("vertebrae_C4", 22.0),
    ("vertebrae_T8", 28.0),
    ("vertebrae_L3", 36.0),
    ("sacrum", 92.0),
    ("sternum", 34.0),
    ("rib_left_6", 15.0),
    ("rib_right_6", 15.0),
    ("scapula_left", 58.0),
    ("scapula_right", 58.0),
    ("humerus_left", 120.0),
    ("humerus_right", 120.0),
    ("hip_left", 185.0),
    ("hip_right", 185.0),
    ("femur_left", 250.0),
    ("femur_right", 250.0),
)


class StubSegmenter(Segmenter):
    """Deterministic, GPU-free segmenter for offline development and tests."""

    name = "stub-0"

    def segment(self, ct_instances: list[bytes]) -> list[OrganVolume]:
        return [OrganVolume(organ_name=name, volume_ml=volume) for name, volume in _STUB_SKELETON]


class TotalSegmentatorSegmenter(Segmenter):
    """Real adapter around TotalSegmentator v2 (requires a GPU and the package).

    Implemented lazily so importing this module never requires TotalSegmentator.
    Runs on the GPU machine; see docs/02_ARCHITECTURE.md.
    """

    name = "totalsegmentator-v2"

    def __init__(self, roi_subset: list[str] | None = None, fast: bool = False) -> None:
        self.roi_subset = roi_subset or []
        self.fast = fast

    def _locate_binary(self) -> str | None:
        """Find the TotalSegmentator CLI on PATH, else next to the interpreter (venv)."""
        found = shutil.which("TotalSegmentator")
        if found:
            return found
        scripts = Path(sys.executable).parent
        for name in ("TotalSegmentator.exe", "TotalSegmentator"):
            candidate = scripts / name
            if candidate.is_file():
                return str(candidate)
        return None

    def segment(self, ct_instances: list[bytes]) -> list[OrganVolume]:
        """DICOM → NIfTI → TotalSegmentator (--statistics) → per-organ volumes (mL).

        Raises a clear error (no silent fallback) when the tool is unavailable, so a
        real measurement is never fabricated. Runs on CPU (``--fast``) or GPU.
        """
        if not ct_instances:
            raise RuntimeError("Aucune instance CT à segmenter.")
        binary = self._locate_binary()
        if binary is None:
            raise RuntimeError(
                "TotalSegmentator introuvable. Installez-le (`pip install TotalSegmentator`) ; "
                "un GPU l'accélère mais le CPU fonctionne (mode --fast)."
            )
        with tempfile.TemporaryDirectory() as tmp:  # pragma: no cover - heavy external tool
            tmpdir = Path(tmp)
            nifti = tmpdir / "ct.nii.gz"
            dicom_series_to_nifti(ct_instances, nifti)
            outdir = tmpdir / "seg"
            # Single-thread resampling/saving: avoids the process-spawn storm that
            # thrashes the CPU and triggers multiprocessing failures on Windows.
            cmd = [
                binary,
                "-i",
                str(nifti),
                "-o",
                str(outdir),
                "--nr_thr_resamp",
                "1",
                "--nr_thr_saving",
                "1",
            ]
            if self.fast:
                cmd.append("--fast")
            if self.roi_subset:
                cmd += ["--roi_subset", *self.roi_subset]
            logger.info(
                "Running TotalSegmentator (fast=%s, %d ROIs)", self.fast, len(self.roi_subset)
            )
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or exc.stdout or "").strip()
                logger.error("TotalSegmentator failed (code %s):\n%s", exc.returncode, detail)
                raise RuntimeError(
                    f"TotalSegmentator a échoué (code {exc.returncode}). {detail[-600:]}"
                ) from exc
            if not outdir.is_dir() or not any(outdir.glob("*.nii.gz")):
                raise RuntimeError("TotalSegmentator n'a produit aucun masque.")
            # Measure volumes from the masks (statistics.json is unreliable with --fast).
            return volumes_from_masks(nifti, outdir)


def get_segmenter() -> Segmenter:
    """Return the configured segmenter (stub by default)."""
    from app.core.config import get_settings

    settings = get_settings()
    if settings.segmenter_backend.lower() == "totalsegmentator":
        roi_subset = [r.strip() for r in settings.segmenter_roi_subset.split(",") if r.strip()]
        return TotalSegmentatorSegmenter(roi_subset=roi_subset, fast=settings.segmenter_fast)
    return StubSegmenter()


def run_segmentation(
    db: Session,
    storage: ObjectStorage,
    *,
    study: Study,
    segmenter: Segmenter,
) -> list[OrganMeasurement]:
    """Segment the study's CT and persist per-organ volume measurements."""
    ct_series = next((s for s in study.series if s.kind is SeriesKind.ct), None)
    if ct_series is None:
        study.status = StudyStatus.error
        study.error_message = "Aucune série CT à segmenter."
        db.flush()
        raise ValueError("No CT series to segment.")

    study.status = StudyStatus.segmenting
    db.flush()

    metadata = ct_series.series_metadata or {}
    instance_count = int(str(metadata.get("instances", 0)))
    ct_instances = [
        storage.read_bytes(f"{ct_series.storage_path}/{index:04d}.dcm")
        for index in range(instance_count)
    ]
    volumes = segmenter.segment(ct_instances)

    measurements: list[OrganMeasurement] = []
    for volume in volumes:
        measurement = OrganMeasurement(
            study_id=study.id,
            organ_name=volume.organ_name,
            snomed_code=volume.snomed_code,
            volume_ml=Decimal(str(volume.volume_ml)),
            mean_intensity=(Decimal(str(volume.mean_hu)) if volume.mean_hu is not None else None),
            segmentation_corrected=False,
        )
        db.add(measurement)
        measurements.append(measurement)
    db.flush()
    return measurements
