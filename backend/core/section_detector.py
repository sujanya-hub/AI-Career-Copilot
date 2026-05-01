"""
core/section_detector.py — Regex + heuristic resume section detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .logger import get_logger

logger = get_logger("section_detector")


class ResumeSection(str, Enum):
    SKILLS         = "skills"
    EXPERIENCE     = "experience"
    EDUCATION      = "education"
    PROJECTS       = "projects"
    SUMMARY        = "summary"
    CERTIFICATIONS = "certifications"
    OTHER          = "other"


@dataclass
class DetectedSections:
    skills:         str = ""
    experience:     str = ""
    education:      str = ""
    projects:       str = ""
    summary:        str = ""
    certifications: str = ""
    other:          str = ""

    def as_dict(self) -> dict[str, str]:
        """Return {section_name: content} for all sections except OTHER."""
        return {
            s.value: getattr(self, s.value, "")
            for s in ResumeSection
            if s != ResumeSection.OTHER
        }

    def word_counts(self) -> dict[str, int]:
        return {k: len(v.split()) for k, v in self.as_dict().items() if v.strip()}


# ── Section header patterns ───────────────────────────────────────────────────

_PATTERNS: dict[ResumeSection, str] = {
    ResumeSection.SUMMARY: (
        r"summary|profile|objective|about\s+me|career\s+summary|"
        r"professional\s+summary|overview"
    ),
    ResumeSection.SKILLS: (
        r"skills?|technologies|tech\s+stack|expertise|"
        r"technical\s+skills?|core\s+competenc|proficienc|tools?\s*&?\s*technologies?"
    ),
    ResumeSection.EXPERIENCE: (
        r"experience|employment|work\s+history|internship|"
        r"professional\s+experience|career\s+history|positions?\s+held"
    ),
    ResumeSection.EDUCATION: (
        r"education|academic|qualifications?|degree|university|college|schooling"
    ),
    ResumeSection.PROJECTS: (
        r"projects?|portfolio|open.?source|personal\s+projects?|"
        r"academic\s+projects?|side\s+projects?"
    ),
    ResumeSection.CERTIFICATIONS: (
        r"certifications?|certificates?|licens|courses?|training|credentials?"
    ),
}

# Pre-compile all patterns once at import time
_COMPILED: dict[ResumeSection, re.Pattern[str]] = {
    sec: re.compile(rf"\b({pat})\b", re.IGNORECASE)
    for sec, pat in _PATTERNS.items()
}

_MAX_HEADER_LEN = 55
_MAX_HEADER_WORDS = 7


class SectionDetector:
    """Splits resume text into labelled sections using regex + heuristics."""

    def detect(self, text: str) -> DetectedSections:
        lines = text.splitlines()
        detected = DetectedSections()
        current_section = ResumeSection.OTHER

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            classified = self._classify_header(stripped)
            if classified is not None:
                current_section = classified
            else:
                attr = current_section.value
                existing = getattr(detected, attr, "")
                setattr(detected, attr, f"{existing}\n{line}" if existing else line)

        # Strip leading/trailing whitespace from all sections
        for sec in ResumeSection:
            attr = sec.value
            setattr(detected, attr, getattr(detected, attr, "").strip())

        found = [s.value for s in ResumeSection if getattr(detected, s.value, "").strip()]
        logger.info("Sections detected: %s", found)
        return detected

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _classify_header(line: str) -> ResumeSection | None:
        """
        Return a ResumeSection if the line looks like a section header,
        otherwise return None.
        """
        if len(line) > _MAX_HEADER_LEN:
            return None
        if len(line.split()) > _MAX_HEADER_WORDS:
            return None

        lower = line.lower().rstrip(":")

        for sec, pattern in _COMPILED.items():
            if pattern.search(lower):
                return sec

        # Heuristic: all-caps short line with no punctuation is likely a header
        core = re.sub(r"[^a-z\s]", "", lower).strip()
        if core and line.isupper() and len(core.split()) <= _MAX_HEADER_WORDS:
            return ResumeSection.OTHER   # unknown all-caps header → group as OTHER

        return None