"""
backend/services/scoring_engine.py
Advanced ATS Scoring Engine — section-wise, weighted, skill-aware.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from loguru import logger


# ─── Section weights (must sum to 1.0) ────────────────────────────────────────

SECTION_WEIGHTS: Dict[str, float] = {
    "keyword_match":      0.30,
    "semantic_alignment": 0.25,
    "skills_coverage":    0.20,
    "experience_match":   0.15,
    "structure_quality":  0.10,
}

# High-value keywords get a 1.5x multiplier in scoring
HIGH_VALUE_KEYWORD_PATTERNS = [
    r"\b(python|java|golang|rust|typescript|kotlin)\b",
    r"\b(machine learning|deep learning|nlp|llm|generative ai)\b",
    r"\b(kubernetes|docker|terraform|aws|gcp|azure)\b",
    r"\b(lead|senior|principal|architect|manager)\b",
    r"\b(revenue|growth|scale|optimize|reduce cost)\b",
]

SECTION_HEADERS = {
    "summary":    r"(summary|profile|objective|about)",
    "experience": r"(experience|employment|work history|career)",
    "skills":     r"(skills|technical skills|competencies|expertise)",
    "education":  r"(education|academic|degree|university|college)",
    "projects":   r"(projects|portfolio|work samples)",
    "certs":      r"(certifications|certificates|licenses|awards)",
}


@dataclass
class SectionScore:
    name: str
    raw_score: float           # 0–100
    weight: float
    weighted_score: float
    details: Dict[str, object] = field(default_factory=dict)


@dataclass
class ATSScoreResult:
    overall_score: int                         # 0–100
    grade: str                                 # A+/A/B/C/D/F
    section_scores: Dict[str, SectionScore]
    keyword_score: int
    semantic_score: int
    skills_coverage: int
    experience_score: int
    structure_score: int
    matched_keywords: List[str]
    missing_keywords: List[str]
    high_value_matched: List[str]
    improvement_delta: int                     # projected +pts after optimization
    confidence: float                          # 0.0–1.0


class ScoringEngine:
    """
    Enterprise ATS Scoring Engine.

    Produces a composite ATS score from:
    - Keyword match rate (TF-IDF weighted)
    - Semantic alignment (cosine similarity proxy)
    - Skills coverage (presence of domain skills)
    - Experience relevance (seniority + tenure signals)
    - Structure quality (section completeness + formatting signals)
    """

    # ── Construction ──────────────────────────────────────────────────────────

    def __init__(self) -> None:
        self._hv_patterns = [
            re.compile(p, re.IGNORECASE) for p in HIGH_VALUE_KEYWORD_PATTERNS
        ]
        self._section_patterns = {
            k: re.compile(v, re.IGNORECASE) for k, v in SECTION_HEADERS.items()
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def score(
        self,
        resume_text: str,
        jd_text: str,
        matched_keywords: List[str],
        missing_keywords: List[str],
        semantic_similarity: float,    # 0.0–1.0 from NLP pipeline
    ) -> ATSScoreResult:
        """Compute full ATS score breakdown."""
        logger.info("ScoringEngine.score() | matched={} missing={} semantic={:.3f}",
                    len(matched_keywords), len(missing_keywords), semantic_similarity)

        # Individual dimension scores
        kw_score   = self._keyword_score(matched_keywords, missing_keywords)
        sem_score  = int(min(100, max(0, semantic_similarity * 100)))
        skill_score = self._skills_coverage(resume_text, jd_text)
        exp_score  = self._experience_score(resume_text, jd_text)
        struct_score = self._structure_score(resume_text)

        # High-value keyword detection
        hv_matched = self._high_value_matched(matched_keywords)

        # Weighted composite
        raw = (
            kw_score    * SECTION_WEIGHTS["keyword_match"]
            + sem_score * SECTION_WEIGHTS["semantic_alignment"]
            + skill_score * SECTION_WEIGHTS["skills_coverage"]
            + exp_score * SECTION_WEIGHTS["experience_match"]
            + struct_score * SECTION_WEIGHTS["structure_quality"]
        )
        # High-value bonus: +2 pts per HV keyword (cap 10 pts)
        hv_bonus = min(10, len(hv_matched) * 2)
        overall  = int(min(100, max(0, raw + hv_bonus)))

        # Build section breakdown
        section_scores = {
            "keyword_match": SectionScore(
                name="Keyword Match", raw_score=kw_score,
                weight=SECTION_WEIGHTS["keyword_match"],
                weighted_score=kw_score * SECTION_WEIGHTS["keyword_match"],
                details={"matched": len(matched_keywords), "missing": len(missing_keywords)},
            ),
            "semantic_alignment": SectionScore(
                name="Semantic Alignment", raw_score=sem_score,
                weight=SECTION_WEIGHTS["semantic_alignment"],
                weighted_score=sem_score * SECTION_WEIGHTS["semantic_alignment"],
                details={"similarity": round(semantic_similarity, 4)},
            ),
            "skills_coverage": SectionScore(
                name="Skills Coverage", raw_score=skill_score,
                weight=SECTION_WEIGHTS["skills_coverage"],
                weighted_score=skill_score * SECTION_WEIGHTS["skills_coverage"],
            ),
            "experience_match": SectionScore(
                name="Experience Match", raw_score=exp_score,
                weight=SECTION_WEIGHTS["experience_match"],
                weighted_score=exp_score * SECTION_WEIGHTS["experience_match"],
            ),
            "structure_quality": SectionScore(
                name="Structure Quality", raw_score=struct_score,
                weight=SECTION_WEIGHTS["structure_quality"],
                weighted_score=struct_score * SECTION_WEIGHTS["structure_quality"],
            ),
        }

        return ATSScoreResult(
            overall_score=overall,
            grade=self._grade(overall),
            section_scores=section_scores,
            keyword_score=kw_score,
            semantic_score=sem_score,
            skills_coverage=skill_score,
            experience_score=exp_score,
            structure_score=struct_score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            high_value_matched=hv_matched,
            improvement_delta=min(30, max(5, 100 - overall - len(missing_keywords))),
            confidence=self._confidence(resume_text, jd_text),
        )

    # ── Dimension scorers ─────────────────────────────────────────────────────

    def _keyword_score(
        self,
        matched: List[str],
        missing: List[str],
    ) -> int:
        total = len(matched) + len(missing)
        if total == 0:
            return 50
        base = int(100 * len(matched) / total)
        # Weight high-value matches extra
        hv_bonus = min(15, len(self._high_value_matched(matched)) * 3)
        return min(100, base + hv_bonus)

    def _skills_coverage(self, resume_text: str, jd_text: str) -> int:
        """Detect skill categories present in both JD and resume."""
        skill_categories = {
            "programming":   r"\b(python|java|javascript|typescript|c\+\+|go|rust|scala|ruby|kotlin|swift)\b",
            "cloud":         r"\b(aws|gcp|azure|cloud|s3|ec2|lambda|kubernetes|k8s|docker|terraform)\b",
            "data":          r"\b(sql|nosql|postgres|mysql|mongodb|redis|elasticsearch|kafka|spark|hadoop)\b",
            "ml_ai":         r"\b(machine learning|deep learning|nlp|pytorch|tensorflow|scikit|transformers|llm)\b",
            "frameworks":    r"\b(django|fastapi|flask|react|nextjs|vue|angular|node|express|spring)\b",
            "soft":          r"\b(leadership|communication|collaboration|agile|scrum|cross.functional)\b",
        }
        resume_lower = resume_text.lower()
        jd_lower     = jd_text.lower()

        jd_categories     = sum(1 for p in skill_categories.values() if re.search(p, jd_lower))
        matched_categories = 0
        for p in skill_categories.values():
            if re.search(p, jd_lower) and re.search(p, resume_lower):
                matched_categories += 1

        if jd_categories == 0:
            return 60
        return int(min(100, 100 * matched_categories / jd_categories))

    def _experience_score(self, resume_text: str, jd_text: str) -> int:
        """Score experience based on seniority signals and years mentioned."""
        # Seniority detection
        seniority_map = {
            r"\b(intern|internship|junior|entry.level)\b": 1,
            r"\b(mid.level|associate|developer|engineer)\b": 2,
            r"\b(senior|sr\.?|lead|principal|staff)\b": 3,
            r"\b(manager|director|vp|head of|architect)\b": 4,
        }
        resume_level = 1
        jd_level     = 1
        for pattern, level in seniority_map.items():
            if re.search(pattern, resume_text, re.IGNORECASE):
                resume_level = max(resume_level, level)
            if re.search(pattern, jd_text, re.IGNORECASE):
                jd_level = max(jd_level, level)

        # Years of experience
        yoe_pattern = r"(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)"
        resume_yoe  = self._extract_max_years(resume_text, yoe_pattern)
        jd_yoe      = self._extract_max_years(jd_text, yoe_pattern)

        # Score
        level_match = 100 - abs(resume_level - jd_level) * 20
        yoe_match   = 100 if jd_yoe == 0 else min(100, int(100 * min(resume_yoe, jd_yoe * 1.5) / max(jd_yoe, 1)))
        return int((level_match + yoe_match) / 2)

    def _structure_score(self, resume_text: str) -> int:
        """Score based on presence of standard resume sections."""
        found = sum(
            1 for p in self._section_patterns.values()
            if p.search(resume_text)
        )
        total = len(self._section_patterns)
        base  = int(100 * found / total)

        # Bonus: consistent formatting signals (bullet markers, dates)
        has_bullets = bool(re.search(r"^[\•\-\*\◦\▸]\s", resume_text, re.MULTILINE))
        has_dates   = bool(re.search(r"\b(20\d{2}|19\d{2})\b", resume_text))
        has_email   = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text))
        has_phone   = bool(re.search(r"(\+?\d[\d\s\-().]{7,}\d)", resume_text))

        bonus = sum([has_bullets * 5, has_dates * 5, has_email * 5, has_phone * 5])
        return min(100, base + bonus)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _high_value_matched(self, matched: List[str]) -> List[str]:
        hv = []
        for kw in matched:
            if any(p.search(kw) for p in self._hv_patterns):
                hv.append(kw)
        return hv

    @staticmethod
    def _extract_max_years(text: str, pattern: str) -> int:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if not matches:
            return 0
        return max(int(m[0]) if isinstance(m, tuple) else int(m) for m in matches)

    @staticmethod
    def _grade(score: int) -> str:
        if score >= 90: return "A+"
        if score >= 80: return "A"
        if score >= 70: return "B"
        if score >= 60: return "C"
        if score >= 50: return "D"
        return "F"

    def _confidence(self, resume_text: str, jd_text: str) -> float:
        """Confidence in analysis quality based on text length."""
        r_words = len(resume_text.split())
        j_words = len(jd_text.split())
        r_conf  = min(1.0, r_words / 300)
        j_conf  = min(1.0, j_words / 150)
        return round((r_conf + j_conf) / 2, 2)