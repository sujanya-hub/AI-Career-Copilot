"""
core/extractor.py — PDF text extraction via PyMuPDF.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Optional

from .logger import get_logger

logger = get_logger("extractor")

try:
    import fitz  # PyMuPDF
    _FITZ_AVAILABLE = True
except ImportError:
    _FITZ_AVAILABLE = False
    logger.warning("PyMuPDF (fitz) not installed. PDF extraction will fail.")


@dataclass
class ExtractionResult:
    text: str
    word_count: int
    page_count: int
    warnings: list[str] = field(default_factory=list)


class PDFExtractor:
    """Extracts text from PDF bytes using PyMuPDF."""

    MIN_WORDS = 50

    def extract(self, pdf_bytes: bytes) -> ExtractionResult:
        if not _FITZ_AVAILABLE:
            raise ValueError("PyMuPDF is not installed. Run: pip install pymupdf")

        warnings: list[str] = []

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            raise ValueError(f"Could not open PDF: {exc}") from exc

        pages_text: list[str] = []
        scanned_pages = 0

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if not text or len(text.strip()) < 20:
                scanned_pages += 1
            else:
                pages_text.append(text)

        doc.close()

        if scanned_pages:
            warnings.append(
                f"{scanned_pages} page(s) appear to be scanned images — "
                "text may be incomplete. Consider a text-based PDF."
            )

        full_text = "\n".join(pages_text)
        full_text = self._clean(full_text)
        word_count = len(full_text.split())

        if word_count < self.MIN_WORDS:
            raise ValueError(
                f"Extracted only {word_count} words. "
                "The PDF may be scanned or image-based."
            )

        logger.info("Extracted %d words from %d pages", word_count, len(pages_text))
        return ExtractionResult(
            text=full_text,
            word_count=word_count,
            page_count=len(pages_text) + scanned_pages,
            warnings=warnings,
        )

    @staticmethod
    def _clean(text: str) -> str:
        # Normalize whitespace but preserve paragraph breaks
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()