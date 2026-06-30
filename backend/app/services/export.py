"""PDF export of a validated report.

Re-identification happens HERE only, locally, at export time (docs/05): the
patient identity (decrypted by the caller) is placed in the PDF header. The AI
banner is part of the report content and remains visible.

The header/footer carry the establishment (per-site CR templating) and the export
supports a light (default) or dark theme.
"""

from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus.doctemplate import BaseDocTemplate

_THEMES = {
    "light": {
        "bg": colors.white,
        "fg": colors.HexColor("#111418"),
        "muted": colors.HexColor("#555a61"),
    },
    "dark": {
        "bg": colors.HexColor("#0e1116"),
        "fg": colors.HexColor("#e6e8eb"),
        "muted": colors.HexColor("#9aa0a6"),
    },
}


def build_report_pdf(
    *,
    exam_label: str,
    identity: dict[str, str],
    content: str,
    validated_by_name: str | None,
    validated_at: str | None,
    establishment_name: str = "",
    establishment_subtitle: str = "",
    theme: str = "light",
) -> bytes:
    palette = _THEMES.get(theme, _THEMES["light"])
    fg, muted, bg = palette["fg"], palette["muted"], palette["bg"]

    def _paint(canvas: Canvas, doc: BaseDocTemplate) -> None:
        canvas.saveState()
        canvas.setFillColor(bg)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(muted)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(
            18 * mm,
            10 * mm,
            "Brouillon généré par IA, relu et validé par le médecin — prototype de "
            "recherche, non destiné au diagnostic autonome.",
        )
        canvas.restoreState()

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
    base = getSampleStyleSheet()
    title_style = ParagraphStyle("ScTitle", parent=base["Title"], textColor=fg)
    normal_style = ParagraphStyle("ScNormal", parent=base["Normal"], textColor=fg)
    muted_style = ParagraphStyle("ScMuted", parent=base["Normal"], textColor=muted, fontSize=9)
    head_style = ParagraphStyle("ScHead", parent=base["Heading2"], textColor=fg, spaceAfter=2)

    story: list[object] = []
    if establishment_name:
        story.append(Paragraph(escape(establishment_name), head_style))
    if establishment_subtitle:
        story.append(Paragraph(escape(establishment_subtitle), muted_style))
    if establishment_name or establishment_subtitle:
        story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(escape(exam_label), title_style))

    name = identity.get("PatientName", "—")
    pid = identity.get("PatientID", "—")
    birth = identity.get("PatientBirthDate", "—")
    story.append(
        Paragraph(escape(f"Patient : {name}  —  ID : {pid}  —  Naissance : {birth}"), normal_style)
    )
    story.append(Spacer(1, 6 * mm))

    for line in content.split("\n"):
        story.append(Paragraph(escape(line) if line.strip() else "&nbsp;", normal_style))

    story.append(Spacer(1, 8 * mm))
    if validated_by_name:
        story.append(
            Paragraph(
                escape(f"Validé par : {validated_by_name}  —  le {validated_at or ''}"),
                normal_style,
            )
        )
    doc.build(story, onFirstPage=_paint, onLaterPages=_paint)
    return buffer.getvalue()
