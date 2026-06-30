"""PDF export of a validated report.

Re-identification happens HERE only, locally, at export time (docs/05): the
patient identity (decrypted by the caller) is placed in the PDF header. The AI
banner is part of the report content and remains visible.
"""

from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_report_pdf(
    *,
    exam_label: str,
    identity: dict[str, str],
    content: str,
    validated_by_name: str | None,
    validated_at: str | None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title="Compte-rendu Scintia",
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(exam_label), styles["Title"])]

    name = identity.get("PatientName", "—")
    pid = identity.get("PatientID", "—")
    birth = identity.get("PatientBirthDate", "—")
    story.append(
        Paragraph(
            escape(f"Patient : {name}  —  ID : {pid}  —  Naissance : {birth}"),
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 6 * mm))

    for line in content.split("\n"):
        story.append(Paragraph(escape(line) if line.strip() else "&nbsp;", styles["Normal"]))

    story.append(Spacer(1, 8 * mm))
    if validated_by_name:
        story.append(
            Paragraph(
                escape(f"Validé par : {validated_by_name}  —  le {validated_at or ''}"),
                styles["Normal"],
            )
        )
    doc.build(story)
    return buffer.getvalue()
