"""
core/ats_scorer.py
Enterprise ATS Scorer — section-wise scoring, keyword weighting,
experience relevance, and structured score breakdown.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from loguru import logger


# ─── Weight configuration ─────────────────────────────────────────────────────

WEIGHTS: Dict[str, float] = {
    "semantic":   0.30,
    "keywords":   0.30,
    "experience": 0.20,
    "structure":  0.10,
    "skills":     0.10,
}


@dataclass
class SectionBreakdown:
    section:    str
    score:      int
    weight:     float
    contribution: float    # score × weight
    details:    str


@dataclass
class ATSScoreBreakdown:
    overall:          int
    grade:            str
    sections:         List[SectionBreakdown]
    keyword_density:  float
    action_verb_count: int
    quantified_bullets: int
    readability_score: int
    section_completeness: int
    suggestions:      List[str]


# ─── Action verbs library ─────────────────────────────────────────────────────

_ACTION_VERBS = re.compile(
    r"\b(led|managed|built|developed|designed|architected|shipped|launched|"
    r"reduced|increased|improved|grew|accelerated|delivered|deployed|created|"
    r"implemented|optimized|scaled|automated|migrated|refactored|integrated|"
    r"collaborated|mentored|coached|owned|drove|spearheaded|pioneered|executed|"
    r"achieved|exceeded|streamlined|consolidated|established|transformed)\b",
    re.IGNORECASE,
)

_QUANTIFIED_BULLET = re.compile(
    r"([\$€£¥][\d,.]+|\d+\s*%|\d+x|\d+\s*(ms|seconds|hours|days|months|"
    r"users|customers|requests|transactions|tb|gb|mb|k|m|b))\b",
    re.IGNORECASE,
)

_SECTION_RE: Dict[str, re.Pattern] = {
    "contact":    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "summary":    re.compile(r"\b(summary|profile|objective|about)\b", re.IGNORECASE),
    "experience": re.compile(r"\b(experience|employment|work history)\b", re.IGNORECASE),
    "education":  re.compile(r"\b(education|degree|university|college|bachelor|master)\b", re.IGNORECASE),
    "skills":     re.compile(r"\b(skills|technologies|competencies|expertise)\b", re.IGNORECASE),
}


class ATSScorer:
    """
    Section-wise ATS Scorer.
    Each dimension is scored independently and combined with weighted average.
    """

    def score(
        self,
        resume_text:    str,
        jd_text:        str,
        semantic_score: int,
        keyword_score:  int,
        matched_kws:    List[str],
        missing_kws:    List[str],
        skills_score:   int = 70,
    ) -> ATSScoreBreakdown:
        logger.info("ATSScorer.score() | sem={} kw={}", semantic_score, keyword_score)

        word_count      = len(resume_text.split())
        action_count    = len(_ACTION_VERBS.findall(resume_text))
        quantified      = len(_QUANTIFIED_BULLET.findall(resume_text))
        section_score   = self._section_completeness(resume_text)
        readability     = self._readability(resume_text)
        experience_score = self._experience_relevance(resume_text, jd_text)
        kw_density      = self._keyword_density(resume_text, matched_kws)
        structure_score = self._structure_score(resume_text, section_score, action_count, quantified)

        # Build section breakdown
        sections = [
            SectionBreakdown(
                section="Semantic Alignment",
                score=semantic_score,
                weight=WEIGHTS["semantic"],
                contribution=semantic_score * WEIGHTS["semantic"],
                details=f"Cosine similarity between resume and JD concepts.",
            ),
            SectionBreakdown(
                section="Keyword Match",
                score=keyword_score,
                weight=WEIGHTS["keywords"],
                contribution=keyword_score * WEIGHTS["keywords"],
                details=f"{len(matched_kws)} matched / {len(missing_kws)} missing.",
            ),
            SectionBreakdown(
                section="Experience Relevance",
                score=experience_score,
                weight=WEIGHTS["experience"],
                contribution=experience_score * WEIGHTS["experience"],
                details="Seniority alignment + years of experience.",
            ),
            SectionBreakdown(
                section="Structure & Quality",
                score=structure_score,
                weight=WEIGHTS["structure"],
                contribution=structure_score * WEIGHTS["structure"],
                details=f"{action_count} action verbs, {quantified} quantified bullets.",
            ),
            SectionBreakdown(
                section="Skills Coverage",
                score=skills_score,
                weight=WEIGHTS["skills"],
                contribution=skills_score * WEIGHTS["skills"],
                details="Percentage of required skill categories present.",
            ),
        ]

        overall = int(sum(s.contribution for s in sections))

        # High-value keyword bonus
        hv_matched = self._count_high_value(matched_kws)
        overall    = min(100, overall + hv_matched * 2)

        suggestions = self._generate_suggestions(
            overall, semantic_score, keyword_score,
            action_count, quantified, section_score,
            missing_kws, word_count,
        )

        return ATSScoreBreakdown(
            overall=overall,
            grade=self._grade(overall),
            sections=sections,
            keyword_density=kw_density,
            action_verb_count=action_count,
            quantified_bullets=quantified,
            readability_score=readability,
            section_completeness=section_score,
            suggestions=suggestions,
        )

    # ── Dimension scorers ─────────────────────────────────────────────────────

    def _section_completeness(self, resume_text: str) -> int:
        found = sum(1 for p in _SECTION_RE.values() if p.search(resume_text))
        return int(100 * found / len(_SECTION_RE))

    def _readability(self, resume_text: str) -> int:
        """
        Simple readability proxy: penalise very long sentences.
        Returns 0-100 score.
        """
        sentences = re.split(r"[.!?]\s+", resume_text)
        if not sentences:
            return 70
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_words <= 15:
            return 90
        if avg_words <= 22:
            return 75
        if avg_words <= 30:
            return 60
        return 45

    def _experience_relevance(self, resume_text: str, jd_text: str) -> int:
        """Scores experience alignment based on seniority + year signals."""
        seniority_map = {
            r"\b(intern|trainee|entry.level)\b": 1,
            r"\b(junior|associate)\b":           2,
            r"\b(mid.?level|developer|engineer)\b": 3,
            r"\b(senior|sr\.?|lead|principal|staff)\b": 4,
            r"\b(manager|director|head of|vp|architect)\b": 5,
        }

        def seniority(text: str) -> int:
            best = 1
            for p, lvl in seniority_map.items():
                if re.search(p, text, re.IGNORECASE):
                    best = max(best, lvl)
            return best

        r_level = seniority(resume_text)
        j_level = seniority(jd_text)
        diff    = abs(r_level - j_level)
        level_score = max(0, 100 - diff * 20)

        # Years of experience
        def max_yoe(text: str) -> int:
            matches = re.findall(r"(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)", text, re.IGNORECASE)
            if not matches:
                return 0
            return max(int(m[0]) for m in matches)

        r_yoe = max_yoe(resume_text)
        j_yoe = max_yoe(jd_text)
        yoe_score = 80 if j_yoe == 0 else min(100, int(100 * min(r_yoe, j_yoe + 2) / max(j_yoe, 1)))

        return int((level_score + yoe_score) / 2)

    def _structure_score(
        self, resume_text: str, section_score: int, action_count: int, quantified: int
    ) -> int:
        word_count = len(resume_text.split())
        length_ok  = 200 <= word_count <= 1200
        has_bullets = bool(re.search(r"^[\•\-\*\◦\▸]\s", resume_text, re.MULTILINE))
        has_dates   = bool(re.search(r"\b(20\d{2}|19\d{2})\b", resume_text))

        base  = section_score * 0.4
        bonus = (
            (10 if length_ok else 0)
            + (10 if has_bullets else 0)
            + (10 if has_dates else 0)
            + min(15, action_count)
            + min(15, quantified * 3)
        )
        return min(100, int(base + bonus))

    def _keyword_density(self, resume_text: str, matched: List[str]) -> float:
        words = len(resume_text.split())
        if words == 0:
            return 0.0
        return round(len(matched) / words * 100, 2)

    def _count_high_value(self, keywords: List[str]) -> int:
        hv = re.compile(
            r"\b(python|kubernetes|aws|machine learning|pytorch|react|leadership)\b",
            re.IGNORECASE,
        )
        return sum(1 for kw in keywords if hv.search(kw))

    # ── Grade & suggestions ───────────────────────────────────────────────────

    @staticmethod
    def _grade(score: int) -> str:
        thresholds = [(90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D")]
        for threshold, grade in thresholds:
            if score >= threshold:
                return grade
        return "F"

    def _generate_suggestions(
        self,
        overall: int,
        semantic: int,
        keyword: int,
        action_count: int,
        quantified: int,
        section_score: int,
        missing_kws: List[str],
        word_count: int,
    ) -> List[str]:
        suggestions: List[str] = []

        if semantic < 50:
            suggestions.append(
                "Low semantic alignment: rewrite your summary to mirror the language "
                "and tone of the job description."
            )
        if keyword < 60 and missing_kws:
            top_missing = ", ".join(missing_kws[:5])
            suggestions.append(
                f"Integrate these missing keywords naturally into your resume: {top_missing}."
            )
        if action_count < 5:
            suggestions.append(
                "Use strong action verbs to open each bullet point "
                "(e.g., Led, Built, Reduced, Scaled, Delivered)."
            )
        if quantified < 3:
            suggestions.append(
                "Add measurable outcomes to at least 3–5 bullets "
                "(e.g., 'Reduced latency by 40%', 'Grew revenue by $2M')."
            )
        if section_score < 80:
            suggestions.append(
                "Ensure your resume includes all standard sections: "
                "Summary, Experience, Skills, and Education."
            )
        if word_count < 250:
            suggestions.append(
                "Your resume appears too short. Expand bullet points with context and impact."
            )
        elif word_count > 1200:
            suggestions.append(
                "Your resume is quite long. Consider trimming to 1–2 pages for ATS compatibility."
            )
        if overall < 60:
            suggestions.append(
                "Consider using the AI Resume Optimizer to automatically rewrite your resume "
                "for this job description."
            )

        return suggestions[:8]