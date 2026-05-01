from __future__ import annotations

import re
import uuid
from typing import Any

from ai_engine import AIEngine
from models.schemas import (
    AnalysisResponse,
    BulletCandidate,
    BulletImprovement,
    ComparisonDelta,
    DeepMatch,
    JobFitPrediction,
    OptimizationResponse,
    RecruiterFeedback,
    ResumeChatResponse,
    ResumeComparisonResponse,
    ScoreBreakdown,
    ScoreComponent,
    SectionRewrite,
)
from services.analysis_cache import AnalysisCache
from services.job_matcher import JobMatcher
from services.resume_parser import ResumeParser
from services.scoring_engine import ScoringEngine
from backend.core.analyzer import ResumeAnalyzer
from backend.core.extractor import PDFExtractor


ACTION_VERBS = (
    "led", "built", "designed", "developed", "optimized", "launched",
    "owned", "delivered", "implemented", "scaled", "automated", "improved",
)


class CareerCopilotService:
    def __init__(self) -> None:
        self.extractor = PDFExtractor()
        self.resume_analyzer = ResumeAnalyzer()
        self.resume_parser = ResumeParser()
        self.job_matcher = JobMatcher()
        self.scoring_engine = ScoringEngine()
        self.ai_engine = AIEngine()
        self.cache = AnalysisCache()

    def extract_resume_text(self, pdf_bytes: bytes) -> tuple[str, list[str]]:
        extraction = self.extractor.extract(pdf_bytes)
        return extraction.text, extraction.warnings

    def analyze(
        self,
        resume_text: str,
        job_description: str,
        *,
        include_ai: bool = True,
        use_cache: bool = True,
    ) -> AnalysisResponse:
        cache_key = self.cache.make_key("analysis", resume_text, job_description, str(include_ai))
        cached = self.cache.get(cache_key) if use_cache else None
        if cached:
            payload = cached.dict() if hasattr(cached, "dict") else cached.model_dump()
            return AnalysisResponse(**{**payload, "cached": True})

        analysis = self.resume_analyzer.analyze(resume_text, job_description)
        parsed = self.resume_parser.parse(resume_text)
        matcher = self.job_matcher.match(
            resume_text,
            job_description,
            analysis.matched_keywords,
            analysis.missing_keywords,
        )
        scoring = self.scoring_engine.score(
            resume_text,
            job_description,
            analysis.matched_keywords,
            analysis.missing_keywords,
            semantic_similarity=analysis.semantic_score / 100,
        )

        deep_match = self._deep_match(analysis, matcher, scoring, resume_text, job_description)
        score_breakdown = self._score_breakdown(analysis, scoring, deep_match, resume_text)
        analysis_snapshot = {
            "ats_score": score_breakdown.overall_score,
            "matched_keywords": analysis.matched_keywords,
            "missing_keywords": analysis.missing_keywords,
            "deep_match": deep_match.model_dump(),
            "has_metrics": bool(re.search(r"\d+[%$xX]|\b\d+\b", resume_text)),
            "suggestions": analysis.suggestions,
        }

        recruiter_payload = (
            self.ai_engine.recruiter_feedback(resume_text, job_description, analysis_snapshot)
            if include_ai else self.ai_engine._fallback_recruiter_feedback(analysis_snapshot)
        )
        keyword_preview_payload = (
            self.ai_engine.inject_keywords(
                resume_text,
                job_description,
                analysis.missing_keywords[:8],
                parsed.raw_sections,
            )
            if include_ai else self.ai_engine._fallback_keyword_injection(parsed.raw_sections, analysis.missing_keywords[:8])
        )
        role_payload = (
            self.ai_engine.predict_roles(resume_text, job_description)
            if include_ai else self.ai_engine._fallback_roles(resume_text)
        )

        response = AnalysisResponse(
            request_id=str(uuid.uuid4()),
            cached=False,
            resume_text=resume_text,
            ats_score=score_breakdown.overall_score,
            semantic_score=analysis.semantic_score,
            tfidf_score=analysis.tfidf_score,
            keyword_score=analysis.keyword_score,
            matched_keywords=analysis.matched_keywords,
            missing_keywords=analysis.missing_keywords,
            jd_top_keywords=analysis.jd_top_keywords,
            resume_top_keywords=analysis.resume_top_keywords,
            suggestions=self._merge_suggestions(analysis.suggestions, matcher.tailoring_hints, score_breakdown.why_this_score),
            warnings=analysis.warnings + parsed.parsing_warnings,
            badges=self._badges(score_breakdown.overall_score, deep_match.overall_alignment),
            percentile_label=self._percentile_label(score_breakdown.overall_score),
            parsed_sections=parsed.raw_sections,
            section_word_counts=analysis.sections.word_counts(),
            recruiter_feedback=RecruiterFeedback(**recruiter_payload),
            deep_match=deep_match,
            score_breakdown=score_breakdown,
            bullets=self._collect_bullets(parsed),
            keyword_injection_preview=[SectionRewrite(**item) for item in keyword_preview_payload],
            job_fit_predictions=[JobFitPrediction(**item) for item in role_payload[:5]],
        )

        if use_cache:
            self.cache.set(cache_key, response)
        return response

    def optimize(
        self,
        resume_text: str,
        job_description: str,
        optimization_level: str = "moderate",
    ) -> OptimizationResponse:
        baseline = self.analyze(resume_text, job_description, include_ai=False, use_cache=True)
        optimization = self.ai_engine.optimize_resume(
            resume_text,
            job_description,
            baseline.missing_keywords,
            optimization_level,
        )
        optimized_resume = optimization.get("optimized_resume", resume_text)
        optimized_analysis = self.analyze(optimized_resume, job_description, include_ai=False, use_cache=False)
        return OptimizationResponse(
            request_id=str(uuid.uuid4()),
            optimized_resume=optimized_resume,
            changes_made=optimization.get("changes_made", []),
            original_score=baseline.ats_score,
            optimized_score=optimized_analysis.ats_score,
            score_delta=optimized_analysis.ats_score - baseline.ats_score,
            matched_keywords=optimized_analysis.matched_keywords,
            missing_keywords=optimized_analysis.missing_keywords,
            before_after_sections=[
                SectionRewrite(**item)
                for item in optimization.get("before_after_sections", [])
            ],
        )

    def compare(
        self,
        baseline_name: str,
        baseline_resume_text: str,
        candidate_name: str,
        candidate_resume_text: str,
        job_description: str,
    ) -> ResumeComparisonResponse:
        baseline = self.analyze(baseline_resume_text, job_description, include_ai=False, use_cache=True)
        candidate = self.analyze(candidate_resume_text, job_description, include_ai=False, use_cache=True)

        baseline_total = len(set(baseline.matched_keywords) | set(baseline.missing_keywords)) or 1
        candidate_total = len(set(candidate.matched_keywords) | set(candidate.missing_keywords)) or 1
        baseline_cov = round((len(baseline.matched_keywords) / baseline_total) * 100)
        candidate_cov = round((len(candidate.matched_keywords) / candidate_total) * 100)
        improvement = candidate.ats_score - baseline.ats_score

        return ResumeComparisonResponse(
            request_id=str(uuid.uuid4()),
            baseline_name=baseline_name,
            candidate_name=candidate_name,
            baseline_score=baseline.ats_score,
            candidate_score=candidate.ats_score,
            improvement_percent=improvement,
            keyword_coverage_change=candidate_cov - baseline_cov,
            deltas=[
                ComparisonDelta(label="ATS Score", baseline=baseline.ats_score, candidate=candidate.ats_score, delta=improvement),
                ComparisonDelta(label="Keyword Coverage", baseline=baseline_cov, candidate=candidate_cov, delta=candidate_cov - baseline_cov),
                ComparisonDelta(
                    label="Alignment",
                    baseline=baseline.deep_match.overall_alignment,
                    candidate=candidate.deep_match.overall_alignment,
                    delta=candidate.deep_match.overall_alignment - baseline.deep_match.overall_alignment,
                ),
            ],
            summary=(
                f"{candidate_name} is {abs(improvement)} points "
                f"{'stronger' if improvement >= 0 else 'weaker'} than {baseline_name} for this role."
            ),
        )

    def improve_bullet(
        self,
        resume_text: str,
        job_description: str,
        bullet_text: str,
        section: str,
    ) -> BulletImprovement:
        payload = self.ai_engine.improve_bullet(resume_text, job_description, bullet_text, section)
        return BulletImprovement(**payload)

    def inject_keywords(
        self,
        resume_text: str,
        job_description: str,
        missing_keywords: list[str],
        sections: dict[str, str],
    ) -> list[SectionRewrite]:
        payload = self.ai_engine.inject_keywords(resume_text, job_description, missing_keywords, sections)
        return [SectionRewrite(**item) for item in payload]

    def chat(
        self,
        resume_text: str,
        job_description: str,
        question: str,
        history: list[dict[str, str]],
        analysis_snapshot: dict[str, Any] | None = None,
    ) -> ResumeChatResponse:
        payload = self.ai_engine.chat_resume(history, question, analysis_snapshot)
        return ResumeChatResponse(
            request_id=str(uuid.uuid4()),
            answer=payload.get("answer", ""),
            follow_up_questions=payload.get("follow_up_questions", []),
        )

    def predict_roles(self, resume_text: str, job_description: str | None = None) -> list[JobFitPrediction]:
        return [JobFitPrediction(**item) for item in self.ai_engine.predict_roles(resume_text, job_description)]

    def _deep_match(self, analysis: Any, matcher: Any, scoring: Any, resume_text: str, job_description: str) -> DeepMatch:
        experience_alignment = max(0, min(100, int((scoring.experience_score + scoring.semantic_score) / 2)))
        skills_overlap = max(0, min(100, int((matcher.overall_match_pct + scoring.skills_coverage) / 2)))
        semantic = analysis.semantic_score
        overall = round((experience_alignment * 0.35) + (skills_overlap * 0.4) + (semantic * 0.25))
        seniority_lookup = {
            "under": ("underqualified", "underqualified"),
            "match": ("well-matched", "qualified"),
            "over": ("overqualified", "overqualified"),
        }
        mismatch, signal = seniority_lookup.get(matcher.seniority_match, ("well-matched", "qualified"))
        evidence = [
            f"Required skills coverage: {matcher.required_skills_pct}%",
            f"Preferred skills coverage: {matcher.preferred_skills_pct}%",
            f"Semantic alignment: {semantic}%",
        ]
        summary = f"You are {overall}% aligned with this role and appear {mismatch.replace('-', ' ')}."
        return DeepMatch(
            overall_alignment=overall,
            summary=summary,
            experience_alignment_score=experience_alignment,
            skills_overlap_score=skills_overlap,
            semantic_alignment_score=semantic,
            role_seniority_mismatch=mismatch,
            qualification_signal=signal,
            evidence=evidence,
        )

    def _score_breakdown(self, analysis: Any, scoring: Any, deep_match: DeepMatch, resume_text: str) -> ScoreBreakdown:
        keyword_score = min(100, round((analysis.keyword_score + scoring.keyword_score) / 2))
        experience_score = deep_match.experience_alignment_score
        structure_score = scoring.structure_score
        impact_score = self._impact_score(resume_text)
        overall = round(
            keyword_score * 0.40
            + experience_score * 0.30
            + structure_score * 0.20
            + impact_score * 0.10
        )
        reasons = []
        if keyword_score < 65:
            reasons.append("Keyword coverage is still leaving relevant JD signals on the table.")
        else:
            reasons.append("Keyword coverage is solid enough to support ATS parsing.")
        if experience_score < 65:
            reasons.append("Experience alignment needs clearer evidence of role-fit and seniority.")
        if structure_score < 70:
            reasons.append("Resume structure can be cleaner for both ATS systems and recruiters.")
        if impact_score < 60:
            reasons.append("More quantified outcomes would improve recruiter confidence.")
        if not reasons:
            reasons.append("The resume is balanced across keywords, structure, experience, and impact.")

        components = [
            ScoreComponent(name="Keywords", weight=40, score=keyword_score, rationale="How well your resume mirrors the core JD language."),
            ScoreComponent(name="Experience", weight=30, score=experience_score, rationale="How clearly your background matches the role's scope and seniority."),
            ScoreComponent(name="Structure", weight=20, score=structure_score, rationale="Whether the resume is easy for ATS systems and recruiters to scan."),
            ScoreComponent(name="Impact", weight=10, score=impact_score, rationale="How much measurable business or engineering outcome the resume shows."),
        ]
        return ScoreBreakdown(overall_score=overall, why_this_score=reasons, components=components)

    def _impact_score(self, resume_text: str) -> int:
        metrics = len(re.findall(r"\b\d+[%$xX]?\b", resume_text))
        action_verbs = sum(1 for verb in ACTION_VERBS if re.search(rf"\b{verb}\b", resume_text, re.IGNORECASE))
        leadership = 1 if re.search(r"\b(led|managed|mentored|owned)\b", resume_text, re.IGNORECASE) else 0
        score = min(100, 35 + metrics * 8 + action_verbs * 6 + leadership * 10)
        return max(25, score)

    def _collect_bullets(self, parsed: Any) -> list[BulletCandidate]:
        bullets: list[BulletCandidate] = []
        index = 1
        for entry in parsed.experience:
            for bullet in entry.bullets[:4]:
                bullets.append(
                    BulletCandidate(
                        bullet_id=f"exp-{index}",
                        section="experience",
                        source=f"{entry.title} @ {entry.company}",
                        text=bullet,
                    )
                )
                index += 1
        for project in parsed.projects[:4]:
            bullets.append(
                BulletCandidate(
                    bullet_id=f"proj-{index}",
                    section="projects",
                    source="Projects",
                    text=project,
                )
            )
            index += 1
        return bullets

    def _merge_suggestions(self, *collections: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for collection in collections:
            for item in collection or []:
                clean = (item or "").strip()
                if clean and clean not in seen:
                    seen.add(clean)
                    merged.append(clean)
        return merged[:8]

    def _percentile_label(self, score: int) -> str:
        if score >= 85:
            return "Top 20% Resume"
        if score >= 72:
            return "Interview-Ready"
        if score >= 60:
            return "Competitive With Improvements"
        return "Needs Improvement"

    def _badges(self, score: int, alignment: int) -> list[str]:
        badges = [self._percentile_label(score)]
        if alignment >= 75:
            badges.append("High JD Alignment")
        if score < 60:
            badges.append("Needs Improvement")
        if score >= 80:
            badges.append("Recruiter Friendly")
        return badges
