"""
backend/services/job_matcher.py
Job Description ↔ Resume Alignment Engine.
Produces granular matching signals beyond simple keyword overlap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger


@dataclass
class SkillGap:
    required_skill:  str
    found_in_resume: bool
    importance:      str   # "critical" | "preferred" | "nice-to-have"
    suggestion:      Optional[str] = None


@dataclass
class JobMatchResult:
    overall_match_pct:   int
    required_skills_pct: int
    preferred_skills_pct: int
    title_alignment:     bool
    seniority_match:     str         # "over" | "match" | "under"
    industry_match:      bool
    skill_gaps:          List[SkillGap]
    top_requirements:    List[str]   # most important missing items
    strengths:           List[str]   # what the candidate does well
    red_flags:           List[str]   # potential deal-breakers
    tailoring_hints:     List[str]   # specific wording advice


# ─── Requirement extraction patterns ─────────────────────────────────────────

_REQUIRED_MARKERS = re.compile(
    r"(?:required|must have|must be|must possess|you must|we require|"
    r"minimum requirement|mandatory|essential)[\s\S]{0,200}",
    re.IGNORECASE,
)

_PREFERRED_MARKERS = re.compile(
    r"(?:preferred|nice to have|bonus|plus|ideally|desired|advantage|"
    r"strong plus|would be great)[\s\S]{0,200}",
    re.IGNORECASE,
)

_SKILL_KEYWORDS = re.compile(
    r"\b([A-Z][a-z]+(?:\.[a-z]+)*|[a-z]+(?:js|\.js|py|\.net)?|"
    r"[A-Z]{2,}(?:\s[A-Z]{2,})*)\b",
    re.IGNORECASE,
)

_SENIORITY_LEVELS = {
    "intern":    0,
    "junior":    1,
    "associate": 2,
    "mid":       3,
    "senior":    4,
    "lead":      5,
    "principal": 6,
    "staff":     6,
    "architect": 7,
    "director":  8,
    "vp":        9,
    "head":      8,
}

_INDUSTRY_TERMS: Dict[str, List[str]] = {
    "fintech":    ["payment", "banking", "financial", "ledger", "compliance", "kyc", "aml"],
    "healthtech": ["ehr", "hipaa", "clinical", "patient", "medical", "fda", "hl7"],
    "ecommerce":  ["cart", "checkout", "inventory", "order management", "marketplace"],
    "saas":       ["b2b", "subscription", "tenant", "onboarding", "churn", "arr", "mrr"],
    "ml":         ["model", "training", "inference", "dataset", "accuracy", "f1", "recall"],
    "security":   ["penetration", "vulnerability", "soc", "siem", "zero trust", "devsecops"],
}


class JobMatcher:
    """
    Produces deep alignment analysis between a resume and a job description.
    Designed to give candidates actionable intelligence about gaps.
    """

    def match(
        self,
        resume_text: str,
        jd_text: str,
        matched_keywords: List[str],
        missing_keywords: List[str],
    ) -> JobMatchResult:
        logger.info("JobMatcher.match() | resume_words={} jd_words={}",
                    len(resume_text.split()), len(jd_text.split()))

        required_skills  = self._extract_required_skills(jd_text)
        preferred_skills = self._extract_preferred_skills(jd_text)

        skill_gaps = self._compute_skill_gaps(resume_text, required_skills, preferred_skills)

        req_matched = sum(1 for g in skill_gaps if g.importance == "critical" and g.found_in_resume)
        req_total   = sum(1 for g in skill_gaps if g.importance == "critical")
        pref_matched = sum(1 for g in skill_gaps if g.importance == "preferred" and g.found_in_resume)
        pref_total   = sum(1 for g in skill_gaps if g.importance == "preferred")

        req_pct  = int(100 * req_matched  / req_total)  if req_total  else 80
        pref_pct = int(100 * pref_matched / pref_total) if pref_total else 70

        overall = int(req_pct * 0.65 + pref_pct * 0.35)

        return JobMatchResult(
            overall_match_pct=overall,
            required_skills_pct=req_pct,
            preferred_skills_pct=pref_pct,
            title_alignment=self._titles_align(resume_text, jd_text),
            seniority_match=self._seniority_match(resume_text, jd_text),
            industry_match=self._industry_match(resume_text, jd_text),
            skill_gaps=skill_gaps,
            top_requirements=self._top_requirements(skill_gaps),
            strengths=self._detect_strengths(resume_text, jd_text, matched_keywords),
            red_flags=self._detect_red_flags(resume_text, jd_text, skill_gaps),
            tailoring_hints=self._tailoring_hints(jd_text, missing_keywords, skill_gaps),
        )

    # ── Extraction helpers ────────────────────────────────────────────────────

    def _extract_required_skills(self, jd_text: str) -> List[str]:
        skills: List[str] = []
        for block in _REQUIRED_MARKERS.findall(jd_text):
            skills.extend(self._extract_noun_phrases(block))
        # Fallback: anything in "Requirements:" bullet list
        skills.extend(self._extract_bullet_items(jd_text, r"requirements?"))
        return list(dict.fromkeys(s.lower() for s in skills if len(s) > 2))

    def _extract_preferred_skills(self, jd_text: str) -> List[str]:
        skills: List[str] = []
        for block in _PREFERRED_MARKERS.findall(jd_text):
            skills.extend(self._extract_noun_phrases(block))
        skills.extend(self._extract_bullet_items(jd_text, r"preferred|nice.to.have"))
        return list(dict.fromkeys(s.lower() for s in skills if len(s) > 2))

    def _extract_bullet_items(self, text: str, section_re: str) -> List[str]:
        """Extract bullet items from a named section."""
        section_pattern = re.compile(
            rf"{section_re}[\s\S]{{0,20}}\n((?:[\s]*[•\-\*▸].*\n?)+)",
            re.IGNORECASE,
        )
        items: List[str] = []
        for m in section_pattern.finditer(text):
            block = m.group(1)
            for line in block.splitlines():
                item = re.sub(r"^[\s•\-\*▸]+", "", line).strip()
                if item:
                    items.append(item)
        return items

    @staticmethod
    def _extract_noun_phrases(text: str) -> List[str]:
        """Rough noun-phrase extractor — avoids NLTK dependency."""
        pattern = re.compile(
            r"\b(?:[A-Z][a-z]+\s+){0,2}(?:[A-Z][a-z]+|[a-z]+(?:js|py|\.js|\.net)?)\b"
        )
        return pattern.findall(text)

    # ── Gap computation ───────────────────────────────────────────────────────

    def _compute_skill_gaps(
        self,
        resume_text: str,
        required: List[str],
        preferred: List[str],
    ) -> List[SkillGap]:
        resume_lower = resume_text.lower()
        gaps: List[SkillGap] = []

        for skill in required[:25]:
            found = skill.lower() in resume_lower
            gaps.append(SkillGap(
                required_skill=skill,
                found_in_resume=found,
                importance="critical",
                suggestion=f"Add '{skill}' to your skills or experience section." if not found else None,
            ))

        for skill in preferred[:20]:
            found = skill.lower() in resume_lower
            gaps.append(SkillGap(
                required_skill=skill,
                found_in_resume=found,
                importance="preferred",
                suggestion=f"Mention '{skill}' if you have any exposure." if not found else None,
            ))

        return gaps

    # ── Alignment signals ─────────────────────────────────────────────────────

    def _titles_align(self, resume_text: str, jd_text: str) -> bool:
        title_words_jd = re.findall(
            r"\b(engineer|developer|scientist|analyst|architect|manager|designer|lead|"
            r"specialist|consultant|researcher)\b",
            jd_text, re.IGNORECASE,
        )
        if not title_words_jd:
            return True  # can't determine → assume ok
        for word in title_words_jd[:3]:
            if re.search(rf"\b{re.escape(word)}\b", resume_text, re.IGNORECASE):
                return True
        return False

    def _seniority_match(self, resume_text: str, jd_text: str) -> str:
        def level(text: str) -> int:
            best = 2
            for term, lvl in _SENIORITY_LEVELS.items():
                if re.search(rf"\b{term}\b", text, re.IGNORECASE):
                    best = max(best, lvl)
            return best

        r_lvl = level(resume_text)
        j_lvl = level(jd_text)
        if r_lvl > j_lvl + 1:   return "over"
        if r_lvl < j_lvl - 1:   return "under"
        return "match"

    def _industry_match(self, resume_text: str, jd_text: str) -> bool:
        for _industry, terms in _INDUSTRY_TERMS.items():
            jd_has   = sum(1 for t in terms if t in jd_text.lower())
            res_has  = sum(1 for t in terms if t in resume_text.lower())
            if jd_has >= 2 and res_has >= 1:
                return True
            if jd_has >= 2 and res_has == 0:
                return False
        return True  # no specific industry detected → neutral

    # ── Intelligence signals ──────────────────────────────────────────────────

    def _top_requirements(self, gaps: List[SkillGap]) -> List[str]:
        missing_critical = [
            g.required_skill for g in gaps
            if g.importance == "critical" and not g.found_in_resume
        ]
        return missing_critical[:5]

    def _detect_strengths(
        self, resume_text: str, jd_text: str, matched_keywords: List[str]
    ) -> List[str]:
        strengths: List[str] = []
        if len(matched_keywords) >= 10:
            strengths.append(f"Strong keyword alignment — {len(matched_keywords)} JD terms present.")
        if re.search(r"\d+%|\d+ percent", resume_text, re.IGNORECASE):
            strengths.append("Quantified achievements improve ATS and recruiter appeal.")
        if re.search(r"\b(led|managed|directed|drove|owned)\b", resume_text, re.IGNORECASE):
            strengths.append("Leadership language detected — impactful framing.")
        if re.search(r"\b(architecture|designed|built|launched|shipped)\b", resume_text, re.IGNORECASE):
            strengths.append("Delivery-oriented language detected.")
        return strengths[:4]

    def _detect_red_flags(
        self, resume_text: str, jd_text: str, gaps: List[SkillGap]
    ) -> List[str]:
        flags: List[str] = []
        words = resume_text.split()
        if len(words) < 200:
            flags.append("Resume is very short — may not pass ATS minimum content threshold.")
        if len(words) > 1500:
            flags.append("Resume may be too long — consider trimming to 1–2 pages.")
        critical_missing = sum(1 for g in gaps if g.importance == "critical" and not g.found_in_resume)
        if critical_missing >= 3:
            flags.append(f"{critical_missing} critical requirements are missing from your resume.")
        if not re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text):
            flags.append("No email address detected — ensure contact info is text-readable.")
        return flags[:4]

    def _tailoring_hints(
        self,
        jd_text: str,
        missing_keywords: List[str],
        gaps: List[SkillGap],
    ) -> List[str]:
        hints: List[str] = []
        if missing_keywords:
            sample = ", ".join(missing_keywords[:4])
            hints.append(f"Naturally integrate these JD keywords: {sample}.")
        # Role-specific advice
        if re.search(r"\b(full.?stack|frontend|backend)\b", jd_text, re.IGNORECASE):
            hints.append("Highlight specific stack layers (e.g., React + Node + Postgres) explicitly.")
        if re.search(r"\b(machine learning|ml|ai|data science)\b", jd_text, re.IGNORECASE):
            hints.append("Quantify model performance metrics (accuracy, F1, latency) in bullets.")
        if re.search(r"\b(cloud|devops|infrastructure)\b", jd_text, re.IGNORECASE):
            hints.append("List cloud certifications and IaC tools (Terraform, CDK) prominently.")
        if re.search(r"\b(leadership|team lead|manage)\b", jd_text, re.IGNORECASE):
            hints.append("Add team size managed and cross-functional collaboration examples.")
        missing_critical = [
            g.required_skill for g in gaps
            if g.importance == "critical" and not g.found_in_resume
        ][:2]
        for skill in missing_critical:
            hints.append(f"Address missing critical skill: '{skill}' — add to skills section or bullets.")
        return hints[:6]