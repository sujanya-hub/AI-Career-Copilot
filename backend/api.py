"""
Production-ready FastAPI backend for ResumeIQ — AI Resume Analyzer.
Integrates ResumeParser, JobMatcher, ScoringEngine, AIEngine,
SQLAlchemy database, and structured loguru logging.
"""

import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from typing import Optional

from configs.logging_config import get_logger
from database.connection import get_db, AnalysisResult, init_db
from backend.services.resume_parser import ResumeParser
from backend.services.job_matcher import JobMatcher
from backend.services.scoring_engine import ScoringEngine
from backend.ai_engine import AIEngine
from backend.utils.response_formatter import ResponseFormatter

logger = get_logger(__name__)

# ── Service Singletons ────────────────────────────────────────────────────────
# Instantiated once at startup — shared across all requests (stateless services)

parser: ResumeParser = None
matcher: JobMatcher = None
scorer: ScoringEngine = None
ai_engine: AIEngine = None
formatter: ResponseFormatter = None


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize all services and the database on startup.
    Gracefully log shutdown on teardown.
    """
    global parser, matcher, scorer, ai_engine, formatter

    logger.info("ResumeIQ API starting up...")
    try:
        init_db()
        logger.info("Database tables verified/created.")

        parser = ResumeParser()
        matcher = JobMatcher()
        scorer = ScoringEngine()
        ai_engine = AIEngine()
        formatter = ResponseFormatter()

        logger.info("All services initialized successfully.")
    except EnvironmentError as e:
        logger.critical(f"Startup failed — missing environment variable: {e}")
        raise
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        raise

    yield  # ── application is running ──

    logger.info("ResumeIQ API shutting down.")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="ResumeIQ API",
    description=(
        "Production-grade AI Resume Analyzer. "
        "Analyzes, scores, and optimizes resumes for ATS compatibility "
        "using LLaMA 3 via Groq."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Schemas ───────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    resume_text: str = Field(
        ...,
        min_length=50,
        description="Full plain-text content of the resume.",
    )
    job_description: str = Field(
        ...,
        min_length=20,
        description="Full plain-text job description to match against.",
    )

    @validator("resume_text")
    def resume_must_not_be_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("resume_text must not be empty or whitespace.")
        return v.strip()

    @validator("job_description")
    def jd_must_not_be_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("job_description must not be empty or whitespace.")
        return v.strip()


class OptimizeRequest(BaseModel):
    resume_text: str = Field(
        ...,
        min_length=50,
        description="Full plain-text content of the resume to optimize.",
    )
    job_description: str = Field(
        ...,
        min_length=20,
        description="Target job description.",
    )
    optimization_level: Optional[str] = Field(
        default="moderate",
        description="Rewrite intensity: 'light', 'moderate', or 'aggressive'.",
    )

    @validator("optimization_level")
    def must_be_valid_level(cls, v: str) -> str:
        allowed = {"light", "moderate", "aggressive"}
        if v not in allowed:
            raise ValueError(
                f"optimization_level must be one of {allowed}. Got: '{v}'"
            )
        return v


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _run_analysis_pipeline(resume_text: str, job_description: str) -> dict:
    """
    Execute the core parse → match → score pipeline.

    Returns a dict with keys:
        parsed_resume, match_result, score_result
    """
    logger.debug("Running parse step.")
    parsed_resume = parser.parse(resume_text)

    logger.debug(
        f"Parse complete — sections found: {list(parsed_resume.keys())}"
    )

    logger.debug("Running keyword match step.")
    match_result = matcher.match(
        resume_data=parsed_resume,
        job_description=job_description,
    )

    logger.debug(
        f"Match complete — "
        f"matched={len(match_result.get('matched_keywords', []))}, "
        f"missing={len(match_result.get('missing_keywords', []))}"
    )

    logger.debug("Running scoring step.")
    score_result = scorer.score(
        parsed_resume=parsed_resume,
        match_result=match_result,
        job_description=job_description,
    )

    logger.debug(
        f"Scoring complete — ats_score={score_result.get('ats_score')}"
    )

    return {
        "parsed_resume": parsed_resume,
        "match_result": match_result,
        "score_result": score_result,
    }


def _persist_analysis(
    db: Session,
    resume_text: str,
    job_description: str,
    ats_score: float,
    matched_keywords: list,
    missing_keywords: list,
    result_json: str,
) -> AnalysisResult:
    """Persist a completed analysis to the database and return the record."""
    record = AnalysisResult(
        resume_snippet=resume_text[:300],
        job_description_snippet=job_description[:300],
        ats_score=ats_score,
        matched_keywords=", ".join(matched_keywords),
        missing_keywords=", ".join(missing_keywords),
        result_json=result_json,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="Health check")
async def root():
    """
    Confirm the API is alive and identify the service.
    """
    logger.debug("GET / — health check called.")
    return {"status": "ok", "service": "ResumeIQ API", "version": "1.0.0"}


@app.post("/analyze", tags=["Analysis"], summary="Analyze a resume against a JD")
async def analyze_resume(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Parse the resume, match it against the job description, and return:
    - ATS compatibility score
    - Matched and missing keywords
    - Parsed section breakdown
    - Score breakdown (if available)
    - Improvement recommendations
    """
    logger.info("POST /analyze — request received.")

    try:
        pipeline = _run_analysis_pipeline(
            payload.resume_text,
            payload.job_description,
        )
        parsed_resume = pipeline["parsed_resume"]
        match_result = pipeline["match_result"]
        score_result = pipeline["score_result"]

        # Build unified response via formatter
        response = formatter.format_analysis(
            parsed_resume=parsed_resume,
            match_result=match_result,
            score_result=score_result,
        )

        # Persist to DB
        record = _persist_analysis(
            db=db,
            resume_text=payload.resume_text,
            job_description=payload.job_description,
            ats_score=score_result.get("ats_score", 0.0),
            matched_keywords=match_result.get("matched_keywords", []),
            missing_keywords=match_result.get("missing_keywords", []),
            result_json=str(response),
        )
        logger.info(
            f"Analysis saved — db_id={record.id}, "
            f"ats_score={score_result.get('ats_score')}"
        )

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)

    except ValueError as e:
        logger.warning(f"Validation error in /analyze: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception:
        logger.error(f"Unexpected error in /analyze:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during resume analysis.",
        )


@app.post("/optimize", tags=["Optimization"], summary="AI-powered resume optimization")
async def optimize_resume(
    payload: OptimizeRequest,
    db: Session = Depends(get_db),
):
    """
    Rewrite the resume using LLaMA 3 (Groq) for maximum ATS compatibility,
    then re-score the optimized version.

    Returns:
    - Full optimized resume text
    - List of changes made
    - Original vs optimized ATS scores
    - Updated keyword match data
    """
    logger.info(
        f"POST /optimize — level={payload.optimization_level}, request received."
    )

    try:
        # ── Step 1: Analyse original resume ──────────────────────────────────
        logger.debug("Step 1: Analysing original resume.")
        original_pipeline = _run_analysis_pipeline(
            payload.resume_text,
            payload.job_description,
        )
        parsed_resume = original_pipeline["parsed_resume"]
        original_match = original_pipeline["match_result"]
        original_score = original_pipeline["score_result"]

        # ── Step 2: AI Optimization ───────────────────────────────────────────
        logger.info(
            f"Step 2: Calling AI engine — level={payload.optimization_level}, "
            f"missing_keywords={len(original_match.get('missing_keywords', []))}"
        )
        optimization_result = ai_engine.optimize(
            resume_text=payload.resume_text,
            parsed_resume=parsed_resume,
            job_description=payload.job_description,
            missing_keywords=original_match.get("missing_keywords", []),
            optimization_level=payload.optimization_level,
        )

        optimized_text: str = optimization_result.get(
            "optimized_resume", payload.resume_text
        )
        changes_made: list = optimization_result.get("changes_made", [])

        # ── Step 3: Score the optimized resume ───────────────────────────────
        logger.debug("Step 3: Scoring optimized resume.")
        optimized_pipeline = _run_analysis_pipeline(
            optimized_text,
            payload.job_description,
        )
        optimized_match = optimized_pipeline["match_result"]
        optimized_score = optimized_pipeline["score_result"]

        # ── Build response ────────────────────────────────────────────────────
        response = formatter.format_optimization(
            original_resume=payload.resume_text,
            optimized_result=optimization_result,
            original_score=original_score,
            optimized_score=optimized_score,
            match_result=optimized_match,
        ) if hasattr(formatter, "format_optimization") else {
            "optimized_resume": optimized_text,
            "changes_made": changes_made,
            "original_score": original_score.get("ats_score", 0.0),
            "optimized_score": optimized_score.get("ats_score", 0.0),
            "matched_keywords": optimized_match.get("matched_keywords", []),
            "missing_keywords": optimized_match.get("missing_keywords", []),
            "score_delta": round(
                optimized_score.get("ats_score", 0.0)
                - original_score.get("ats_score", 0.0),
                2,
            ),
        }

        logger.info(
            f"Optimization complete — "
            f"original_score={original_score.get('ats_score')}, "
            f"optimized_score={optimized_score.get('ats_score')}, "
            f"changes={len(changes_made)}"
        )

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)

    except ValueError as e:
        logger.warning(f"Validation error in /optimize: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except RuntimeError as e:
        # Raised by AIEngine when all retries are exhausted
        logger.error(f"AI engine failure in /optimize: {e}")
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI optimization service is temporarily unavailable. "
                "Please try again in a few moments."
            ),
        )

    except Exception:
        logger.error(f"Unexpected error in /optimize:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during resume optimization.",
        )


@app.get("/history", tags=["History"], summary="Fetch past analysis results")
async def get_history(
    limit: int = Query(default=10, ge=1, le=100, description="Records per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    Return paginated list of past resume analysis records, newest first.

    Query parameters:
    - **limit**: number of records to return (1–100, default 10)
    - **offset**: number of records to skip for pagination (default 0)
    """
    logger.info(f"GET /history — limit={limit}, offset={offset}")

    try:
        total: int = db.query(AnalysisResult).count()

        records = (
            db.query(AnalysisResult)
            .order_by(AnalysisResult.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        history = [
            {
                "id": r.id,
                "ats_score": r.ats_score,
                "resume_snippet": r.resume_snippet,
                "job_description_snippet": r.job_description_snippet,
                "matched_keywords": (
                    [k.strip() for k in r.matched_keywords.split(",") if k.strip()]
                    if r.matched_keywords
                    else []
                ),
                "missing_keywords": (
                    [k.strip() for k in r.missing_keywords.split(",") if k.strip()]
                    if r.missing_keywords
                    else []
                ),
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]

        logger.info(
            f"History query returned {len(history)} records "
            f"(total={total})."
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "limit": limit,
                "offset": offset,
                "count": len(history),
                "results": history,
            },
        )

    except Exception:
        logger.error(f"Unexpected error in /history:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching history.",
        )


from backend.main import app as app
