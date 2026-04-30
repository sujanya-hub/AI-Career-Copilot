from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AnalyzeTextRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=20)


class OptimizeRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=20)
    optimization_level: Literal["light", "moderate", "aggressive"] = "moderate"


class BulletImproveRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=20)
    bullet_text: str = Field(..., min_length=8)
    section: str = "experience"


class KeywordInjectionRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=20)
    missing_keywords: List[str] = Field(default_factory=list)
    sections: Dict[str, str] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class ResumeChatRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=20)
    question: str = Field(..., min_length=2)
    history: List[ChatMessage] = Field(default_factory=list)
    analysis_snapshot: Optional[Dict[str, object]] = None


class RecruiterFeedbackRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: str = Field(..., min_length=20)
    analysis_snapshot: Optional[Dict[str, object]] = None


class JobFitRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)
    job_description: Optional[str] = None


class ExportRequest(BaseModel):
    optimized_resume: str = Field(..., min_length=50)
    title: str = "Optimized Resume"


class DeepMatch(BaseModel):
    overall_alignment: int
    summary: str
    experience_alignment_score: int
    skills_overlap_score: int
    semantic_alignment_score: int
    role_seniority_mismatch: Literal["underqualified", "well-matched", "overqualified"]
    qualification_signal: Literal["underqualified", "qualified", "overqualified"]
    evidence: List[str] = Field(default_factory=list)


class RecruiterFeedback(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    hiring_decision: Literal["Reject", "Maybe", "Strong Hire"]
    recruiter_verdict: str


class ScoreComponent(BaseModel):
    name: str
    weight: int
    score: int
    rationale: str


class ScoreBreakdown(BaseModel):
    overall_score: int
    why_this_score: List[str] = Field(default_factory=list)
    components: List[ScoreComponent] = Field(default_factory=list)


class BulletCandidate(BaseModel):
    bullet_id: str
    section: str
    source: str
    text: str


class BulletImprovement(BaseModel):
    original_bullet: str
    improved_bullet: str
    rationale: List[str] = Field(default_factory=list)
    metrics_hint: Optional[str] = None
    star_hint: Optional[str] = None


class SectionRewrite(BaseModel):
    section: str
    before: str
    after: str
    injected_keywords: List[str] = Field(default_factory=list)


class JobFitPrediction(BaseModel):
    role: str
    match_score: int
    rationale: str
    missing_signals: List[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    request_id: str
    cached: bool = False
    resume_text: str
    ats_score: int
    semantic_score: int
    tfidf_score: int
    keyword_score: int
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    jd_top_keywords: List[str] = Field(default_factory=list)
    resume_top_keywords: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)
    percentile_label: str
    parsed_sections: Dict[str, str] = Field(default_factory=dict)
    section_word_counts: Dict[str, int] = Field(default_factory=dict)
    recruiter_feedback: RecruiterFeedback
    deep_match: DeepMatch
    score_breakdown: ScoreBreakdown
    bullets: List[BulletCandidate] = Field(default_factory=list)
    keyword_injection_preview: List[SectionRewrite] = Field(default_factory=list)
    job_fit_predictions: List[JobFitPrediction] = Field(default_factory=list)


class OptimizationResponse(BaseModel):
    request_id: str
    optimized_resume: str
    changes_made: List[str] = Field(default_factory=list)
    original_score: int
    optimized_score: int
    score_delta: int
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    before_after_sections: List[SectionRewrite] = Field(default_factory=list)


class ComparisonDelta(BaseModel):
    label: str
    baseline: int
    candidate: int
    delta: int


class ResumeComparisonResponse(BaseModel):
    request_id: str
    baseline_name: str
    candidate_name: str
    baseline_score: int
    candidate_score: int
    improvement_percent: int
    keyword_coverage_change: int
    deltas: List[ComparisonDelta] = Field(default_factory=list)
    summary: str


class ResumeChatResponse(BaseModel):
    request_id: str
    answer: str
    follow_up_questions: List[str] = Field(default_factory=list)


class HistoryRecord(BaseModel):
    id: int
    ats_score: float
    resume_snippet: str
    job_description_snippet: str
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    created_at: str


class HistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    count: int
    results: List[HistoryRecord] = Field(default_factory=list)
