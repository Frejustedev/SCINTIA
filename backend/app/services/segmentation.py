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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.clinical import OrganMeasurement
from app.models.enums import SeriesKind, StudyStatus
from app.models.study import Study
from app.services.storage import ObjectStorage


@dataclass(frozen=True)
class OrganVolume:
    organ_name: str
    volume_ml: float
    snomed_code: str | None = None


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

    def segment(self, ct_instances: list[bytes]) -> list[OrganVolume]:  # pragma: no cover
        raise NotImplementedError(
            "TotalSegmentator integration runs on a GPU host; not available offline. "
            "Wire it here: DICOM->NIfTI (dcm2niix/SimpleITK) then "
            "`TotalSegmentator -i ct.nii.gz -o out --statistics --roi_subset ...`, "
            "and parse statistics.json (mm3 -> mL)."
        )


def get_segmenter() -> Segmenter:
    """Return the configured segmenter (stub by default)."""
    from app.core.config import get_settings

    backend = get_settings().segmenter_backend.lower()
    if backend == "totalsegmentator":
        return TotalSegmentatorSegmenter()
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
            segmentation_corrected=False,
        )
        db.add(measurement)
        measurements.append(measurement)
    db.flush()
    return measurements
