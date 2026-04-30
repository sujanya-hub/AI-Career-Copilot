from __future__ import annotations

import asyncio
import traceback
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.models.schemas import (
    AnalysisResponse,
    AnalyzeTextRequest,
    BulletImproveRequest,
    BulletImprovement,
    HistoryResponse,
    JobFitPrediction,
    JobFitRequest,
    KeywordInjectionRequest,
    OptimizeRequest,
    OptimizationResponse,
    RecruiterFeedback,
    RecruiterFeedbackRequest,
    ResumeChatRequest,
    ResumeChatResponse,
    ResumeComparisonResponse,
    SectionRewrite,
)
from backend.services.career_copilot import CareerCopilotService
from configs.logging_config import get_logger
from database.connection import AnalysisResult, get_db, init_db

logger = get_logger(__name__)
service: CareerCopilotService | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global service
    init_db()
    service = CareerCopilotService()
    logger.info("Career Copilot API ready")
    yield


app = FastAPI(
    title="ResumeIQ Career Copilot API",
    version="3.0.0",
    description="Production-style resume analysis, recruiter feedback, comparison, optimization, and AI copilot APIs.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Invalid request payload."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.error(f"Unhandled API error:\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "message": "Internal server error."},
    )


def _require_service() -> CareerCopilotService:
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized.")
    return service


def _persist_analysis(db: Session, analysis: AnalysisResponse, job_description: str) -> None:
    record = AnalysisResult(
        resume_snippet=analysis.resume_text[:300],
        job_description_snippet=job_description[:300],
        ats_score=analysis.ats_score,
        matched_keywords=", ".join(analysis.matched_keywords),
        missing_keywords=", ".join(analysis.missing_keywords),
        result_json=analysis.json() if hasattr(analysis, "json") else str(analysis),
    )
    db.add(record)
    db.commit()


async def _read_resume_from_request(
    request: Request,
    copilot: CareerCopilotService,
    file: UploadFile | None,
    form_resume_text: str | None,
    form_job_description: str | None,
) -> tuple[str, str]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = AnalyzeTextRequest(**(await request.json()))
        return payload.resume_text.strip(), payload.job_description.strip()

    if file is not None:
        file_bytes = await file.read()
        resume_text, _ = await asyncio.to_thread(copilot.extract_resume_text, file_bytes)
    elif form_resume_text:
        resume_text = form_resume_text.strip()
    else:
        raise HTTPException(status_code=422, detail="Provide either a PDF file or resume_text.")

    if not form_job_description or len(form_job_description.strip()) < 20:
        raise HTTPException(status_code=422, detail="job_description is required.")

    return resume_text, form_job_description.strip()


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "ResumeIQ Career Copilot API", "version": "3.0.0"}


@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_resume(
    request: Request,
    file: UploadFile | None = File(default=None),
    resume_text: str | None = Form(default=None),
    job_description: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    copilot = _require_service()
    parsed_resume_text, parsed_job_description = await _read_resume_from_request(
        request,
        copilot,
        file,
        resume_text,
        job_description,
    )
    analysis = await asyncio.to_thread(
        lambda: copilot.analyze(
            parsed_resume_text,
            parsed_job_description,
            include_ai=True,
            use_cache=True,
        )
    )
    if not analysis.cached:
        await asyncio.to_thread(_persist_analysis, db, analysis, parsed_job_description)
    return analysis


@app.post("/recruiter-feedback", response_model=RecruiterFeedback, tags=["Analysis"])
async def recruiter_feedback(payload: RecruiterFeedbackRequest):
    copilot = _require_service()
    analysis = await asyncio.to_thread(
        lambda: copilot.analyze(
            payload.resume_text,
            payload.job_description,
            include_ai=False,
            use_cache=True,
        )
    )
    return await asyncio.to_thread(
        lambda: RecruiterFeedback(
            **copilot.ai_engine.recruiter_feedback(
                payload.resume_text,
                payload.job_description,
                payload.analysis_snapshot or analysis.dict(),
            )
        )
    )


@app.post("/optimize", response_model=OptimizationResponse, tags=["Optimization"])
async def optimize_resume(payload: OptimizeRequest):
    copilot = _require_service()
    return await asyncio.to_thread(
        copilot.optimize,
        payload.resume_text,
        payload.job_description,
        payload.optimization_level,
    )


@app.post("/improve-bullet", response_model=BulletImprovement, tags=["Optimization"])
async def improve_bullet(payload: BulletImproveRequest):
    copilot = _require_service()
    return await asyncio.to_thread(
        copilot.improve_bullet,
        payload.resume_text,
        payload.job_description,
        payload.bullet_text,
        payload.section,
    )


@app.post("/inject-keywords", response_model=list[SectionRewrite], tags=["Optimization"])
async def inject_keywords(payload: KeywordInjectionRequest):
    copilot = _require_service()
    return await asyncio.to_thread(
        copilot.inject_keywords,
        payload.resume_text,
        payload.job_description,
        payload.missing_keywords,
        payload.sections,
    )


@app.post("/chat", response_model=ResumeChatResponse, tags=["Copilot"])
async def resume_chat(payload: ResumeChatRequest):
    copilot = _require_service()
    history = [message.dict() if hasattr(message, "dict") else message.model_dump() for message in payload.history]
    return await asyncio.to_thread(
        copilot.chat,
        payload.resume_text,
        payload.job_description,
        payload.question,
        history,
        payload.analysis_snapshot,
    )


@app.post("/job-fit", response_model=list[JobFitPrediction], tags=["Copilot"])
async def job_fit(payload: JobFitRequest):
    copilot = _require_service()
    return await asyncio.to_thread(copilot.predict_roles, payload.resume_text, payload.job_description)


@app.post("/compare", response_model=ResumeComparisonResponse, tags=["Analysis"])
async def compare_resumes(
    baseline_file: UploadFile = File(...),
    candidate_file: UploadFile = File(...),
    job_description: str = Form(...),
):
    copilot = _require_service()
    baseline_text, _ = await asyncio.to_thread(copilot.extract_resume_text, await baseline_file.read())
    candidate_text, _ = await asyncio.to_thread(copilot.extract_resume_text, await candidate_file.read())
    return await asyncio.to_thread(
        copilot.compare,
        baseline_file.filename or "Baseline Resume",
        baseline_text,
        candidate_file.filename or "Candidate Resume",
        candidate_text,
        job_description,
    )


@app.get("/history", response_model=HistoryResponse, tags=["History"])
async def get_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    records = (
        db.query(AnalysisResult)
        .order_by(AnalysisResult.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(AnalysisResult).count()
    return HistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        count=len(records),
        results=[
            {
                "id": record.id,
                "ats_score": record.ats_score,
                "resume_snippet": record.resume_snippet,
                "job_description_snippet": record.job_description_snippet,
                "matched_keywords": [item.strip() for item in (record.matched_keywords or "").split(",") if item.strip()],
                "missing_keywords": [item.strip() for item in (record.missing_keywords or "").split(",") if item.strip()],
                "created_at": record.created_at.isoformat(),
            }
            for record in records
        ],
    )
