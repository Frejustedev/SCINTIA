"""Structured interoperability exports: FHIR DiagnosticReport and DICOM-SR.

These exports are for hospital systems (RIS/PACS). They are **pseudonymous** — the
subject is the internal pseudonym, never the real identity (which is only
re-identified locally at PDF export). The non-removable AI banner is part of the
``content`` and is therefore carried into both exports.
"""

from __future__ import annotations

import io
from typing import Any

from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import UID, ExplicitVRLittleEndian, generate_uid

# Basic Text SR storage SOP class.
_BASIC_TEXT_SR_SOP_CLASS = UID("1.2.840.10008.5.1.4.1.1.88.11")


def build_fhir_diagnostic_report(
    *,
    pseudonym: str,
    exam_label: str,
    content: str,
    validated: bool,
    issued_iso: str | None,
    score_type: str | None = None,
    score_value: str | None = None,
    organs: list[tuple[str, float | None]] | None = None,
) -> dict[str, Any]:
    """A FHIR R4 DiagnosticReport (pseudonymous), with contained quantitative results."""
    contained: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    def _add_observation(obs_id: str, text: str, value: dict[str, Any]) -> None:
        observation: dict[str, Any] = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final" if validated else "preliminary",
            "code": {"text": text},
            "subject": {"identifier": {"system": "urn:scintia:pseudonym", "value": pseudonym}},
            **value,
        }
        contained.append(observation)
        results.append({"reference": f"#{obs_id}"})

    if score_value is not None:
        _add_observation(
            "score",
            f"Score ({score_type})" if score_type else "Score",
            {"valueString": score_value},
        )
    for index, (organ_name, volume_ml) in enumerate(organs or []):
        if volume_ml is None:
            continue
        _add_observation(
            f"organ-{index}",
            f"Volume — {organ_name}",
            {
                "valueQuantity": {
                    "value": round(volume_ml, 2),
                    "unit": "mL",
                    "system": "http://unitsofmeasure.org",
                    "code": "mL",
                }
            },
        )

    report: dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "status": "final" if validated else "preliminary",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "NMR",
                        "display": "Nuclear Medicine",
                    }
                ]
            }
        ],
        "code": {"text": exam_label},
        "subject": {"identifier": {"system": "urn:scintia:pseudonym", "value": pseudonym}},
        "conclusion": content,
    }
    if issued_iso is not None:
        report["issued"] = issued_iso
    if contained:
        report["contained"] = contained
        report["result"] = results
    return report


def build_dicom_sr(
    *,
    pseudonym: str,
    exam_label: str,
    content: str,
    validated: bool,
) -> bytes:
    """A minimal, pseudonymous DICOM Basic Text SR carrying the report content."""
    ds = Dataset()
    ds.SOPClassUID = _BASIC_TEXT_SR_SOP_CLASS
    ds.SOPInstanceUID = generate_uid()
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.Modality = "SR"
    # UTF-8 so accented French and the em-dash in the banner encode losslessly.
    ds.SpecificCharacterSet = "ISO_IR 192"
    ds.SeriesNumber = "1"
    ds.InstanceNumber = "1"
    # Pseudonymous identity only — never the real patient name.
    ds.PatientName = pseudonym
    ds.PatientID = pseudonym
    ds.CompletionFlag = "COMPLETE" if validated else "PARTIAL"
    ds.VerificationFlag = "VERIFIED" if validated else "UNVERIFIED"

    # SR document root: a CONTAINER holding one TEXT item with the report.
    ds.ValueType = "CONTAINER"
    ds.ContinuityOfContent = "SEPARATE"
    ds.ConceptNameCodeSequence = [
        _code_item("18748-4", "LN", "Diagnostic imaging report"),
    ]
    text_item = Dataset()
    text_item.RelationshipType = "CONTAINS"
    text_item.ValueType = "TEXT"
    text_item.ConceptNameCodeSequence = [_code_item("121070", "DCM", "Findings")]
    text_item.TextValue = content
    title_item = Dataset()
    title_item.RelationshipType = "HAS CONCEPT MOD"
    title_item.ValueType = "TEXT"
    title_item.ConceptNameCodeSequence = [_code_item("121049", "DCM", "Language of Content")]
    title_item.TextValue = exam_label
    ds.ContentSequence = [title_item, text_item]

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = _BASIC_TEXT_SR_SOP_CLASS
    meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta = meta

    buffer = io.BytesIO()
    ds.save_as(buffer, enforce_file_format=True)
    return buffer.getvalue()


def _code_item(code: str, scheme: str, meaning: str) -> Dataset:
    item = Dataset()
    item.CodeValue = code
    item.CodingSchemeDesignator = scheme
    item.CodeMeaning = meaning
    return item
