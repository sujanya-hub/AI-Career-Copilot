"""
core/pdf_report.py — Generate a downloadable PDF analysis report.
Uses ReportLab if available, falls back to a plain-text PDF via fpdf2.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from .logger import get_logger

if TYPE_CHECKING:
    from .analyzer import AnalysisResult

logger = get_logger("pdf_report")

# ── Try ReportLab first, then fpdf2 ──────────────────────────────────────────

_REPORTLAB_OK = False
_FPDF_OK = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    _REPORTLAB_OK = True
except ImportError:
    pass

if not _REPORTLAB_OK:
    try:
        from fpdf import FPDF
        _FPDF_OK = True
    except ImportError:
        pass


class PDFReportGenerator:
    """Generates a styled PDF report from an AnalysisResult."""

    def generate(self, result: "AnalysisResult") -> bytes:
        if _REPORTLAB_OK:
            return self._reportlab(result)
        if _FPDF_OK:
            return self._fpdf(result)
        # Last resort: return JSON as UTF-8 bytes inside a minimal PDF-like text
        logger.warning("No PDF library available; returning JSON bytes.")
        return result.to_json().encode("utf-8")

    # ── ReportLab implementation ──────────────────────────────────────────────

    def _reportlab(self, result: "AnalysisResult") -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        AMBER = colors.HexColor("#f5a623")
        DARK = colors.HexColor("#0a0a0b")
        SLATE = colors.HexColor("#d4d0c8")
        DARK_BG = colors.HexColor("#101013")

        title_style = ParagraphStyle(
            "Title", parent=styles["Normal"],
            fontSize=28, textColor=AMBER, spaceAfter=6,
            fontName="Helvetica-Bold", alignment=TA_LEFT,
        )
        heading_style = ParagraphStyle(
            "Heading", parent=styles["Normal"],
            fontSize=11, textColor=AMBER, spaceAfter=4, spaceBefore=12,
            fontName="Helvetica-Bold", borderPad=2,
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=9, textColor=colors.HexColor("#555560"),
            fontName="Helvetica", spaceAfter=3, leading=13,
        )
        score_style = ParagraphStyle(
            "Score", parent=styles["Normal"],
            fontSize=48, textColor=AMBER, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=0,
        )
        verdict_style = ParagraphStyle(
            "Verdict", parent=styles["Normal"],
            fontSize=10, textColor=colors.HexColor("#88889a"),
            alignment=TA_CENTER, fontName="Helvetica",
        )

        story = []

        # ── Header ──
        story.append(Paragraph("ATS Resume Analyzer", title_style))
        story.append(Paragraph("AI-Powered Resume Intelligence Report", body_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e1e24"), spaceAfter=12))

        # ── Score block ──
        story.append(Paragraph(str(result.ats_score), score_style))
        story.append(Paragraph("ATS COMPATIBILITY SCORE / 100", verdict_style))
        story.append(Paragraph(self._verdict_text(result.ats_score), verdict_style))
        story.append(Spacer(1, 14))

        # ── Sub-scores table ──
        story.append(Paragraph("Score Breakdown", heading_style))
        score_data = [
            ["Metric", "Score"],
            ["Semantic Similarity (40%)", f"{result.semantic_score}%"],
            ["TF-IDF Cosine Match (30%)", f"{result.tfidf_score}%"],
            ["Keyword Overlap (30%)", f"{result.keyword_score}%"],
            ["Resume Word Count", str(result.resume_word_count)],
            ["JD Word Count", str(result.jd_word_count)],
        ]
        t = Table(score_data, colWidths=[10 * cm, 5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), AMBER),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), SLATE),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0d0d10")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0d0d10"), colors.HexColor("#101013")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#1e1e24")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

        # ── Missing keywords ──
        if result.missing_keywords:
            story.append(Paragraph("Missing Keywords", heading_style))
            story.append(Paragraph(", ".join(result.missing_keywords[:25]), body_style))

        # ── Matched keywords ──
        if result.matched_keywords:
            story.append(Paragraph("Matched Keywords", heading_style))
            story.append(Paragraph(", ".join(result.matched_keywords[:25]), body_style))

        # ── Skill categories ──
        cats = result.categorized_skills.as_dict()
        non_empty = {k: v for k, v in cats.items() if v}
        if non_empty:
            story.append(Paragraph("Skill Categories (from Resume)", heading_style))
            for cat, skills in non_empty.items():
                story.append(Paragraph(f"<b>{cat}:</b> {', '.join(skills)}", body_style))

        # ── Section word counts ──
        wc = result.sections.word_counts()
        if wc:
            story.append(Paragraph("Resume Section Word Counts", heading_style))
            wc_data = [["Section", "Words"]] + [
                [str(k.value if hasattr(k, "value") else k).title(), str(v)]
                for k, v in wc.items()
            ]
            wt = Table(wc_data, colWidths=[10 * cm, 5 * cm])
            wt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), AMBER),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 1), (-1, -1), SLATE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0d0d10")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#1e1e24")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(wt)

        # ── Suggestions ──
        story.append(Paragraph("Improvement Suggestions", heading_style))
        for i, sug in enumerate(result.suggestions, 1):
            story.append(Paragraph(f"{i}. {sug}", body_style))

        # ── Alignment gaps ──
        if result.alignment.gap_messages:
            story.append(Paragraph("Section Alignment Gaps", heading_style))
            for msg in result.alignment.gap_messages[:10]:
                story.append(Paragraph(f"• {msg}", body_style))

        doc.build(story)
        return buf.getvalue()

    # ── fpdf2 fallback ────────────────────────────────────────────────────────

    def _fpdf(self, result: "AnalysisResult") -> bytes:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_fill_color(10, 10, 11)
        pdf.rect(0, 0, 210, 297, "F")

        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(245, 166, 35)
        pdf.cell(0, 12, "ATS Resume Analyzer Report", ln=True, align="C")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(136, 136, 154)
        pdf.cell(0, 6, "AI-Powered Resume Intelligence", ln=True, align="C")
        pdf.ln(6)

        # Score
        pdf.set_font("Helvetica", "B", 40)
        pdf.set_text_color(245, 166, 35)
        pdf.cell(0, 20, str(result.ats_score), ln=True, align="C")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(136, 136, 154)
        pdf.cell(0, 6, "ATS COMPATIBILITY SCORE / 100", ln=True, align="C")
        pdf.cell(0, 5, self._verdict_text(result.ats_score), ln=True, align="C")
        pdf.ln(8)

        def section_header(title: str):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(245, 166, 35)
            pdf.cell(0, 8, title, ln=True)
            pdf.set_draw_color(30, 30, 36)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)

        def body_text(txt: str):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(212, 208, 200)
            pdf.multi_cell(0, 5, txt)
            pdf.ln(1)

        section_header("Score Breakdown")
        body_text(
            f"Semantic Similarity (40%): {result.semantic_score}%\n"
            f"TF-IDF Cosine Match (30%): {result.tfidf_score}%\n"
            f"Keyword Overlap (30%): {result.keyword_score}%\n"
            f"Resume Words: {result.resume_word_count}  |  JD Words: {result.jd_word_count}"
        )

        if result.missing_keywords:
            section_header("Missing Keywords")
            body_text(", ".join(result.missing_keywords[:25]))

        if result.matched_keywords:
            section_header("Matched Keywords")
            body_text(", ".join(result.matched_keywords[:25]))

        section_header("Improvement Suggestions")
        for i, sug in enumerate(result.suggestions, 1):
            body_text(f"{i}. {sug}")

        return bytes(pdf.output())

    @staticmethod
    def _verdict_text(score: int) -> str:
        if score >= 80:
            return "Strong — High probability of passing ATS filters"
        if score >= 65:
            return "Good — Minor improvements will secure this role"
        if score >= 45:
            return "Moderate — Targeted revisions strongly advised"
        return "Weak — Significant rewrite recommended"