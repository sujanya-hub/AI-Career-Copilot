from __future__ import annotations

import os
from typing import Any

import requests


BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://ai-career-copilot-6u8o.onrender.com"
).rstrip("/")

class APIError(RuntimeError):
    pass


def _handle_response(response: requests.Response) -> Any:
    try:
        payload = response.json()
    except Exception as exc:
        raise APIError(f"Backend returned non-JSON output: {response.text[:200]}") from exc

    if response.status_code >= 400:
        detail = payload.get("detail") or payload.get("message") or payload
        raise APIError(str(detail))
    return payload


def analyze_resume(pdf_bytes: bytes, filename: str, job_description: str) -> dict[str, Any]:
    response = requests.post(
        f"{BACKEND_URL}/analyze",
        files={"file": (filename, pdf_bytes, "application/pdf")},
        data={"job_description": job_description},
        timeout=180,
    )
    return _handle_response(response)


def optimize_resume(resume_text: str, job_description: str, optimization_level: str) -> dict[str, Any]:
    response = requests.post(
        f"{BACKEND_URL}/optimize",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
            "optimization_level": optimization_level,
        },
        timeout=180,
    )
    return _handle_response(response)


def improve_bullet(resume_text: str, job_description: str, bullet_text: str, section: str) -> dict[str, Any]:
    response = requests.post(
        f"{BACKEND_URL}/improve-bullet",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
            "bullet_text": bullet_text,
            "section": section,
        },
        timeout=120,
    )
    return _handle_response(response)


def compare_resumes(
    baseline_bytes: bytes,
    baseline_name: str,
    candidate_bytes: bytes,
    candidate_name: str,
    job_description: str,
) -> dict[str, Any]:
    response = requests.post(
        f"{BACKEND_URL}/compare",
        files={
            "baseline_file": (baseline_name, baseline_bytes, "application/pdf"),
            "candidate_file": (candidate_name, candidate_bytes, "application/pdf"),
        },
        data={"job_description": job_description},
        timeout=240,
    )
    return _handle_response(response)


def inject_keywords(
    resume_text: str,
    job_description: str,
    missing_keywords: list[str],
    sections: dict[str, str],
) -> list[dict[str, Any]]:
    response = requests.post(
        f"{BACKEND_URL}/inject-keywords",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
            "missing_keywords": missing_keywords,
            "sections": sections,
        },
        timeout=120,
    )
    return _handle_response(response)


def chat_resume(
    resume_text: str,
    job_description: str,
    question: str,
    history: list[dict[str, str]],
    analysis_snapshot: dict[str, Any],
) -> dict[str, Any]:
    response = requests.post(
        f"{BACKEND_URL}/chat",
        json={
            "resume_text": resume_text,
            "job_description": job_description,
            "question": question,
            "history": history,
            "analysis_snapshot": analysis_snapshot,
        },
        timeout=120,
    )
    return _handle_response(response)


def predict_roles(resume_text: str, job_description: str | None = None) -> list[dict[str, Any]]:
    response = requests.post(
        f"{BACKEND_URL}/job-fit",
        json={"resume_text": resume_text, "job_description": job_description},
        timeout=120,
    )
    return _handle_response(response)
