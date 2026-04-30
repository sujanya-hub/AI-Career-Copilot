"""
core/jd_aligner.py — Map JD keywords to resume sections, surface gaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .section_detector import DetectedSections, ResumeSection
from .logger import get_logger

logger = get_logger("jd_aligner")


@dataclass
class AlignmentResult:
    gap_messages: list[str] = field(default_factory=list)
    section_coverage: dict[str, int] = field(default_factory=dict)


# Ordered scan priority: Skills first, then other content sections
_SCAN_ORDER: list[tuple[str, str]] = [
    ("skills",         "Skills"),
    ("experience",     "Experience"),
    ("projects",       "Projects"),
    ("education",      "Education"),
    ("summary",        "Summary"),
    ("certifications", "Certifications"),
]


class JDAligner:
    """Maps JD keywords to resume sections and surfaces alignment gaps."""

    def align(
        self,
        jd_keywords: list[str],
        sections: DetectedSections,
    ) -> AlignmentResult:
        # Build {display_label: lowercased_text} for non-empty sections only
        section_texts: dict[str, str] = {
            label: getattr(sections, attr, "").lower()
            for attr, label in _SCAN_ORDER
            if getattr(sections, attr, "").strip()
        }

        coverage: dict[str, int] = {}
        gap_messages: list[str] = []

        for kw in jd_keywords:
            kw_lower = kw.lower().strip()
            if not kw_lower:
                continue

            found_in: list[str] = []
            for label, text in section_texts.items():
                if kw_lower in text:
                    found_in.append(label)
                    coverage[label] = coverage.get(label, 0) + 1

            if not found_in:
                gap_messages.append(
                    f'"{kw}" not found in any resume section'
                )
            elif "Skills" in section_texts and "Skills" not in found_in:
                # Present somewhere but absent from the Skills section specifically
                gap_messages.append(
                    f'"{kw}" found in {", ".join(found_in)} '
                    f"but missing from Skills section"
                )

        logger.info(
            "Alignment complete — %d gaps from %d JD keywords",
            len(gap_messages),
            len(jd_keywords),
        )

        return AlignmentResult(
            gap_messages=gap_messages[:20],   # cap for UI rendering
            section_coverage=coverage,
        )