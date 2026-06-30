"""Report PDF: establishment templating and light/dark theme."""

from __future__ import annotations

from app.services.export import build_report_pdf


def _pdf(theme: str) -> bytes:
    return build_report_pdf(
        exam_label="Scintigraphie osseuse",
        identity={"PatientName": "DOE^JOHN", "PatientID": "P1"},
        content="RÉSULTATS\nVolumes segmentés.\n\nCONCLUSION\nÀ valider.",
        validated_by_name="Dr Nucleaire",
        validated_at="2026-06-30",
        establishment_name="CHU de Cotonou",
        establishment_subtitle="Service de Médecine Nucléaire",
        theme=theme,
    )


def test_pdf_is_valid_and_theme_changes_output() -> None:
    light = _pdf("light")
    dark = _pdf("dark")
    assert light[:5] == b"%PDF-" and dark[:5] == b"%PDF-"
    assert len(light) > 500
    assert light != dark  # the theme actually changes the rendered document
