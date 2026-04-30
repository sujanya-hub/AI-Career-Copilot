"""
backend/services/resume_parser.py
Structured Resume Parser — extracts sections, contact info, skills, and experience.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from loguru import logger


# ─── Data models ──────────────────────────────────────────────────────────────

@dataclass
class ContactInfo:
    name:     Optional[str] = None
    email:    Optional[str] = None
    phone:    Optional[str] = None
    linkedin: Optional[str] = None
    github:   Optional[str] = None
    location: Optional[str] = None
    website:  Optional[str] = None


@dataclass
class ExperienceEntry:
    title:       str
    company:     str
    start_date:  Optional[str]
    end_date:    Optional[str]
    duration_months: int
    bullets:     List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    degree:      str
    institution: str
    year:        Optional[str]
    gpa:         Optional[str] = None
    majors:      List[str] = field(default_factory=list)


@dataclass
class ParsedResume:
    contact:         ContactInfo
    summary:         Optional[str]
    experience:      List[ExperienceEntry]
    education:       List[EducationEntry]
    skills:          List[str]
    certifications:  List[str]
    projects:        List[str]
    raw_sections:    Dict[str, str]
    word_count:      int
    has_all_sections: bool
    parsing_warnings: List[str]


# ─── Section boundary patterns ────────────────────────────────────────────────

_SECTION_PATTERNS: Dict[str, str] = {
    "summary":        r"^\s*(summary|profile|objective|professional summary|about me|career objective)\s*$",
    "experience":     r"^\s*(experience|work experience|employment|employment history|work history|career history)\s*$",
    "education":      r"^\s*(education|academic|academic background|qualifications)\s*$",
    "skills":         r"^\s*(skills|technical skills|core competencies|competencies|expertise|technologies)\s*$",
    "certifications": r"^\s*(certifications?|certificates?|licenses?|professional development)\s*$",
    "projects":       r"^\s*(projects?|portfolio|personal projects?|open source)\s*$",
    "awards":         r"^\s*(awards?|honors?|achievements?|recognitions?)\s*$",
}

_DATE_PATTERN        = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{4}"
_DURATION_MONTHS_RE  = re.compile(
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*(\d{4})",
    re.IGNORECASE,
)
_MONTH_MAP = dict(
    jan=1, feb=2, mar=3, apr=4, may=5, jun=6,
    jul=7, aug=8, sep=9, oct=10, nov=11, dec=12,
)

_TECH_KEYWORDS = re.compile(
    r"\b(python|java|javascript|typescript|react|node\.?js|django|fastapi|flask|"
    r"aws|gcp|azure|kubernetes|docker|sql|postgres|mysql|mongodb|redis|"
    r"tensorflow|pytorch|scikit|spark|kafka|elasticsearch|terraform|"
    r"golang|rust|kotlin|swift|c\+\+|scala|ruby|php)\b",
    re.IGNORECASE,
)


class ResumeParser:
    """
    Parses raw resume text into structured sections and entities.
    Designed to be format-agnostic — handles PDFs converted to plain text.
    """

    # ── Public API ────────────────────────────────────────────────────────────

    def parse(self, raw_text: str) -> ParsedResume:
        logger.info("ResumeParser.parse() | chars={}", len(raw_text))
        warnings: List[str] = []

        raw_sections = self._split_sections(raw_text)

        contact = self._extract_contact(raw_text)
        summary = raw_sections.get("summary")
        experience = self._parse_experience(raw_sections.get("experience", ""), warnings)
        education  = self._parse_education(raw_sections.get("education", ""), warnings)
        skills     = self._parse_skills(raw_sections.get("skills", ""))
        certs      = self._parse_list(raw_sections.get("certifications", ""))
        projects   = self._parse_list(raw_sections.get("projects", ""))

        required = {"summary", "experience", "education", "skills"}
        has_all  = required.issubset(raw_sections.keys())
        if not has_all:
            missing_secs = required - raw_sections.keys()
            warnings.append(f"Could not detect sections: {', '.join(missing_secs)}")

        return ParsedResume(
            contact=contact,
            summary=summary,
            experience=experience,
            education=education,
            skills=skills,
            certifications=certs,
            projects=projects,
            raw_sections=raw_sections,
            word_count=len(raw_text.split()),
            has_all_sections=has_all,
            parsing_warnings=warnings,
        )

    # ── Section splitter ──────────────────────────────────────────────────────

    def _split_sections(self, text: str) -> Dict[str, str]:
        lines      = text.splitlines()
        sections: Dict[str, str] = {}
        current_section: Optional[str] = None
        current_lines: List[str] = []

        compiled = {k: re.compile(v, re.IGNORECASE | re.MULTILINE)
                    for k, v in _SECTION_PATTERNS.items()}

        for line in lines:
            matched_section: Optional[str] = None
            for name, pattern in compiled.items():
                if pattern.match(line.strip()):
                    matched_section = name
                    break

            if matched_section:
                if current_section and current_lines:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = matched_section
                current_lines   = []
            elif current_section:
                current_lines.append(line)

        if current_section and current_lines:
            sections[current_section] = "\n".join(current_lines).strip()

        return sections

    # ── Contact extraction ────────────────────────────────────────────────────

    def _extract_contact(self, text: str) -> ContactInfo:
        # Take the first 600 chars as the header block
        header = text[:600]

        email    = self._first(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", header)
        phone    = self._first(r"(\+?[\d][\d\s\-()\.]){9,15}", header)
        linkedin = self._first(r"linkedin\.com/in/[\w\-]+", header, re.IGNORECASE)
        github   = self._first(r"github\.com/[\w\-]+", header, re.IGNORECASE)
        website  = self._first(r"https?://[^\s]+", header, re.IGNORECASE)

        # Name: first non-empty line that isn't an email/URL/phone
        name: Optional[str] = None
        for line in text.splitlines()[:5]:
            line = line.strip()
            if line and not re.search(r"[@/\d]{3,}", line) and 2 < len(line) < 60:
                name = line
                break

        location = self._first(
            r"\b([A-Z][a-z]+([\s,]+[A-Z][a-z]+){0,3},?\s*(USA?|UK|India|Canada|Australia|[A-Z]{2}))\b",
            header,
        )

        return ContactInfo(
            name=name, email=email, phone=phone,
            linkedin=linkedin, github=github,
            location=location, website=website,
        )

    # ── Experience parsing ────────────────────────────────────────────────────

    def _parse_experience(self, text: str, warnings: List[str]) -> List[ExperienceEntry]:
        if not text.strip():
            return []
        entries: List[ExperienceEntry] = []

        # Split on lines that look like job titles (ALL CAPS or Title Case + date)
        blocks = re.split(
            r"\n(?=[A-Z][^\n]{5,60}\n|[A-Z ]{8,}\n)",
            text.strip(),
        )
        for block in blocks:
            if len(block.strip()) < 20:
                continue
            lines   = [l.strip() for l in block.strip().splitlines() if l.strip()]
            title   = lines[0] if lines else "Unknown Title"
            company = lines[1] if len(lines) > 1 else "Unknown Company"

            date_str = ""
            for line in lines[:4]:
                if re.search(_DATE_PATTERN, line, re.IGNORECASE):
                    date_str = line
                    break

            start, end = self._parse_date_range(date_str)
            bullets    = [l for l in lines[2:] if l.startswith(("•", "-", "*", "◦", "▸")) or len(l) > 40]
            techs      = _TECH_KEYWORDS.findall(block)

            entries.append(ExperienceEntry(
                title=title, company=company,
                start_date=start, end_date=end,
                duration_months=self._date_to_months(start, end),
                bullets=bullets[:10],
                technologies=list({t.lower() for t in techs}),
            ))

        if not entries:
            warnings.append("Could not parse individual experience entries.")

        return entries

    # ── Education parsing ─────────────────────────────────────────────────────

    def _parse_education(self, text: str, warnings: List[str]) -> List[EducationEntry]:
        if not text.strip():
            return []
        entries: List[EducationEntry] = []
        degree_pattern = re.compile(
            r"\b(b\.?s\.?|m\.?s\.?|b\.?e\.?|m\.?e\.?|b\.?tech|m\.?tech|phd|"
            r"bachelor|master|doctorate|associate|mba|bca|mca)\b",
            re.IGNORECASE,
        )
        year_pattern = re.compile(r"\b(20\d{2}|19\d{2})\b")
        gpa_pattern  = re.compile(r"\bgpa\s*:?\s*([\d.]+)", re.IGNORECASE)

        blocks = re.split(r"\n{2,}", text.strip())
        for block in blocks:
            if not block.strip():
                continue
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if not lines:
                continue
            degree = lines[0]
            institution = lines[1] if len(lines) > 1 else ""
            year_m = year_pattern.search(block)
            gpa_m  = gpa_pattern.search(block)
            entries.append(EducationEntry(
                degree=degree, institution=institution,
                year=year_m.group() if year_m else None,
                gpa=gpa_m.group(1) if gpa_m else None,
            ))
        return entries

    # ── Skills parsing ────────────────────────────────────────────────────────

    def _parse_skills(self, text: str) -> List[str]:
        if not text.strip():
            return []
        # Handle comma/pipe/slash/newline delimiters
        raw = re.split(r"[,|\n/•\-\*]", text)
        skills = []
        for item in raw:
            item = item.strip().strip("•-*◦▸").strip()
            if 1 < len(item) < 60 and not re.match(r"^\d+$", item):
                skills.append(item)
        return list(dict.fromkeys(skills))  # deduplicate, preserve order

    def _parse_list(self, text: str) -> List[str]:
        if not text.strip():
            return []
        items = re.split(r"[•\-\*\n]", text)
        return [i.strip() for i in items if i.strip() and len(i.strip()) > 3]

    # ── Date helpers ──────────────────────────────────────────────────────────

    def _parse_date_range(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        dates = re.findall(
            r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|\d{4}|present|current)",
            text, re.IGNORECASE,
        )
        start = dates[0] if dates else None
        end   = dates[1] if len(dates) > 1 else ("Present" if dates else None)
        return start, end

    def _date_to_months(self, start: Optional[str], end: Optional[str]) -> int:
        """Rough month-count between two date strings."""
        try:
            def to_ym(s: str):
                s = s.strip().lower()
                if "present" in s or "current" in s:
                    import datetime
                    now = datetime.date.today()
                    return now.year * 12 + now.month
                m = _DURATION_MONTHS_RE.search(s)
                if m:
                    month = _MONTH_MAP.get(m.group(1)[:3].lower(), 1)
                    return int(m.group(2)) * 12 + month
                y = re.search(r"\d{4}", s)
                return int(y.group()) * 12 if y else 0

            if not start:
                return 0
            sm = to_ym(start)
            em = to_ym(end or "present")
            return max(0, em - sm)
        except Exception:
            return 0

    # ── Util ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _first(pattern: str, text: str, flags: int = 0) -> Optional[str]:
        m = re.search(pattern, text, flags)
        return m.group().strip() if m else None