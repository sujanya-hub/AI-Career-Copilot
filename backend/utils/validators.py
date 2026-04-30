"""
backend/utils/validators.py
Input validation layer — guards all user-supplied data before processing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from loguru import logger


# ─── Constants ─────────────────────────────────────────────────────────────

MAX_PDF_SIZE_BYTES   = 10 * 1024 * 1024   # 10 MB
MIN_JD_LENGTH        = 50
MAX_JD_LENGTH        = 25_000
MIN_RESUME_WORDS     = 50
MAX_RESUME_WORDS     = 3000
ALLOWED_MIME_TYPES   = {"application/pdf"}
ALLOWED_EXTENSIONS   = {".pdf"}

# Injection / abuse patterns
_INJECTION_PATTERNS = [
    r"<script[\s\S]*?>",
    r"javascript:",
    r"on\w+\s*=",
    r"--\s*drop\s+table",
    r"union\s+select",
    r"\$\{.*?\}",     # template injection
]
_COMPILED_INJECTIONS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


# ─── Result type ─────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    valid:    bool
    errors:   List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ─── Validators ──────────────────────────────────────────────────────────────

class ResumeFileValidator:
    """Validates uploaded resume files before extraction."""

    def validate(
        self,
        file_name: str,
        file_size: int,
        mime_type: Optional[str] = None,
    ) -> ValidationResult:
        result = ValidationResult(valid=True)

        # Extension check
        ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if ext not in ALLOWED_EXTENSIONS:
            result.add_error(
                f"Unsupported file type '{ext}'. Only PDF files are accepted."
            )

        # Size check
        if file_size == 0:
            result.add_error("Uploaded file is empty.")
        elif file_size > MAX_PDF_SIZE_BYTES:
            mb = round(file_size / 1024 / 1024, 1)
            result.add_error(
                f"File size {mb} MB exceeds the 10 MB limit."
            )

        # MIME type (optional — not always available from browsers)
        if mime_type and mime_type not in ALLOWED_MIME_TYPES:
            result.add_error(
                f"MIME type '{mime_type}' is not allowed. Expected 'application/pdf'."
            )

        # Filename sanitization
        if not self._safe_filename(file_name):
            result.add_warning(
                "Filename contains special characters — it will be sanitized."
            )

        if result.valid:
            logger.debug("ResumeFileValidator: '{}' passed ({} bytes)", file_name, file_size)
        else:
            logger.warning("ResumeFileValidator: '{}' failed | {}", file_name, result.errors)

        return result

    @staticmethod
    def _safe_filename(name: str) -> bool:
        return bool(re.match(r"^[\w\s\-.()\[\]]+$", name))


class JobDescriptionValidator:
    """Validates job description text input."""

    def validate(self, text: str) -> ValidationResult:
        result = ValidationResult(valid=True)

        if not text or not text.strip():
            result.add_error("Job description cannot be empty.")
            return result

        stripped = text.strip()
        length   = len(stripped)

        # Length checks
        if length < MIN_JD_LENGTH:
            result.add_error(
                f"Job description is too short ({length} chars). "
                f"Minimum is {MIN_JD_LENGTH} characters."
            )
        elif length > MAX_JD_LENGTH:
            result.add_warning(
                f"Job description is very long ({length} chars). "
                "Consider trimming to the key requirements for better results."
            )

        # Injection check
        for pattern in _COMPILED_INJECTIONS:
            if pattern.search(stripped):
                result.add_error(
                    "Job description contains invalid content. "
                    "Please paste plain text only."
                )
                break

        # Quality checks (warnings only)
        word_count = len(stripped.split())
        if word_count < 30:
            result.add_warning(
                "Job description seems very brief — results will be less accurate."
            )

        if not re.search(r"\b(require|must|experience|skill|responsible|duty)\b",
                         stripped, re.IGNORECASE):
            result.add_warning(
                "Job description may be missing requirements section — "
                "keyword analysis may be limited."
            )

        if result.valid:
            logger.debug("JobDescriptionValidator: passed | length={} words={}", length, word_count)
        else:
            logger.warning("JobDescriptionValidator: failed | {}", result.errors)

        return result


class ResumeTextValidator:
    """Validates extracted resume text quality."""

    def validate(self, text: str) -> ValidationResult:
        result = ValidationResult(valid=True)

        if not text or not text.strip():
            result.add_error(
                "Could not extract text from the PDF. "
                "Ensure you are uploading a text-based PDF (not a scan/image)."
            )
            return result

        word_count = len(text.split())
        if word_count < MIN_RESUME_WORDS:
            result.add_error(
                f"Extracted text is too short ({word_count} words). "
                "The PDF may be image-based or scanned. Please use a text-based PDF."
            )
        elif word_count > MAX_RESUME_WORDS:
            result.add_warning(
                f"Resume is very long ({word_count} words). "
                "Consider limiting to 1–2 pages for best ATS performance."
            )

        # Check for garbled / binary text (common in scanned PDFs)
        non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / max(len(text), 1)
        if non_ascii_ratio > 0.15:
            result.add_warning(
                "Resume text contains many special characters — "
                "it may be partially garbled. Accuracy could be reduced."
            )

        # Injection check
        for pattern in _COMPILED_INJECTIONS:
            if pattern.search(text):
                result.add_error("Resume content contains invalid patterns.")
                break

        return result


class APIKeyValidator:
    """Validates API key format before making outbound calls."""

    GROQ_PREFIX    = "gsk_"
    OPENAI_PREFIX  = "sk-"

    @classmethod
    def validate_groq(cls, key: Optional[str]) -> ValidationResult:
        result = ValidationResult(valid=True)
        if not key:
            result.add_error("GROQ_API_KEY is not set.")
            return result
        if not key.startswith(cls.GROQ_PREFIX):
            result.add_warning(
                f"GROQ_API_KEY does not start with '{cls.GROQ_PREFIX}' — "
                "it may be invalid."
            )
        if len(key) < 30:
            result.add_error("GROQ_API_KEY appears too short to be valid.")
        return result

    @classmethod
    def validate_openai(cls, key: Optional[str]) -> ValidationResult:
        result = ValidationResult(valid=True)
        if not key:
            result.add_error("OPENAI_API_KEY is not set.")
            return result
        if not key.startswith(cls.OPENAI_PREFIX):
            result.add_warning(
                f"OPENAI_API_KEY does not start with '{cls.OPENAI_PREFIX}'."
            )
        return result


# ─── Convenience composite validator ─────────────────────────────────────────

class InputValidator:
    """
    Convenience wrapper that runs all relevant validators for the main
    analysis flow and returns a single aggregated result.
    """

    def __init__(self) -> None:
        self.file_validator = ResumeFileValidator()
        self.jd_validator   = JobDescriptionValidator()
        self.text_validator = ResumeTextValidator()

    def validate_analysis_inputs(
        self,
        file_name: str,
        file_size: int,
        jd_text: str,
    ) -> ValidationResult:
        combined = ValidationResult(valid=True)

        file_result = self.file_validator.validate(file_name, file_size)
        jd_result   = self.jd_validator.validate(jd_text)

        for r in [file_result, jd_result]:
            combined.errors.extend(r.errors)
            combined.warnings.extend(r.warnings)
            if not r.valid:
                combined.valid = False

        return combined

    def validate_extracted_text(self, resume_text: str) -> ValidationResult:
        return self.text_validator.validate(resume_text)