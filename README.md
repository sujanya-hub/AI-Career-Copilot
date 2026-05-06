# AI-Career-Copilot
### Production-Ready Resume Intelligence & ATS Optimization Platform

<p align="center">
  Resume analysis, semantic matching, recruiter-style feedback, and ATS optimization workflows.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-FastAPI-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/NLP-SentenceTransformers-black?style=for-the-badge" />
  <img src="https://img.shields.io/badge/LLM-Groq%20%7C%20OpenAI%20%7C%20Claude-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Frontend-Streamlit-red?style=for-the-badge" />
</p>

<p align="center">
  <a href="https://ai-career-copilot.streamlit.app/">
    <img src="https://img.shields.io/badge/Live%20Demo-Streamlit-success?style=for-the-badge" />
  </a>

  <a href="https://ai-career-copilot-6u8o.onrender.com">
    <img src="https://img.shields.io/badge/Backend-Render-purple?style=for-the-badge" />
  </a>
</p>

---

## Live Deployment

| Service | Link |
|---|---|
| Frontend | https://ai-career-copilot.streamlit.app/ |
| Backend API | https://ai-career-copilot-6u8o.onrender.com |

---

## Overview

AI-Career-Copilot is a full-stack resume intelligence platform built for ATS analysis, semantic job matching, recruiter-style feedback, and resume optimization workflows.

The system combines:
- deterministic ATS scoring
- semantic similarity pipelines
- optional LLM-assisted optimization
- recruiter-style evaluation logic

to provide explainable and context-aware resume analysis.

The architecture intentionally separates deterministic scoring from LLM generation so the application remains functional even when external AI providers fail or rate-limit requests.

---

## Preview

### Resume ATS Analysis Dashboard

Weighted ATS scoring, keyword analysis, section-level evaluation, and recruiter-style resume breakdown.

![ATS Dashboard](assets/ats-dashboard.png)

---

### Resume ↔ Job Description Semantic Matching

Semantic similarity scoring, missing skill detection, and role alignment analysis using embedding-based retrieval.

![Semantic Matching](assets/semantic-matching.png)

---

### Resume Optimization & Rewrite Pipeline

Bullet point rewriting, ATS keyword enrichment, and recruiter-oriented optimization suggestions.

![Resume Optimization](assets/resume-optimization.png)

---

## Core Features

### ATS Resume Scoring

- Deterministic ATS scoring pipeline
- Explainable weighted scoring system
- Section-wise resume evaluation
- Keyword density analysis

### Semantic Job Description Matching

- Resume ↔ JD similarity scoring
- Missing skill detection
- Role alignment analysis
- Semantic keyword matching

### Recruiter Feedback Pipeline

- Recruiter-style evaluation mode
- Resume weakness detection
- Improvement recommendations
- Hiring-readiness analysis

### Bullet Point Rewrite Pipeline

- Rewrites weak resume bullets
- ATS keyword enrichment
- Action-oriented formatting improvements
- Quantification suggestions

### Resume Comparison Engine

- Compare multiple resumes
- ATS score comparison
- Skill overlap analysis
- Candidate strength evaluation

### Context-Aware Resume Chat

- Resume-aware conversational assistant
- Multi-provider LLM routing
- Context injection using uploaded resume data
- Career optimization support

---

## Why This Architecture?

Traditional ATS systems rely heavily on keyword matching and often fail to capture semantic alignment between resumes and job descriptions.

AI-Career-Copilot combines:
- deterministic scoring pipelines
- semantic embedding similarity
- optional LLM-assisted refinement

to balance:
- explainability
- reliability
- contextual understanding

The backend separates:
- rule-based scoring
- semantic similarity pipelines
- LLM-assisted generation

so the application can continue functioning even when external AI providers fail.

---

## System Architecture

```text
                ┌────────────────────┐
                │ Streamlit Frontend │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │  FastAPI Backend   │
                └─────────┬──────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼                                ▼
┌────────────────────┐         ┌────────────────────┐
│ Resume Parsing &   │         │ Semantic Matching  │
│ ATS Scoring Layer  │         │ + LLM Services     │
└─────────┬──────────┘         └─────────┬──────────┘
          │                                │
          └───────────────┬────────────────┘
                          ▼
             ┌────────────────────────┐
             │ SQLite + Export Layer  │
             └────────────────────────┘
```

---

## Technical Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| API Server | Uvicorn |
| NLP | Sentence Transformers, Scikit-learn |
| LLM Providers | OpenAI, Groq, Claude |
| Database | SQLite |
| File Processing | PyPDF2, python-docx |
| Deployment | Render, Streamlit Cloud |

---

## Engineering Decisions

| Decision | Reasoning |
|---|---|
| Deterministic ATS scoring | Improves explainability and consistency |
| Semantic similarity pipelines | Captures contextual alignment beyond keyword matching |
| Multi-provider LLM routing | Reduces dependency on a single provider |
| Service-layer abstraction | Simplifies provider switching and maintenance |
| FastAPI backend separation | Decouples frontend and analysis pipelines |
| SQLite persistence | Lightweight storage for resume analysis history |

---

## Project Structure

```text
AI-Career-Copilot/
│
├── assets/
│   ├── ats-dashboard.png
│   ├── semantic-matching.png
│   └── resume-optimization.png
│
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── render.yaml
├── Procfile
│
├── backend/
├── frontend/
├── models/
├── services/
├── utils/
├── exports/
├── uploads/
├── static/
└── database/
```

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/AI-Career-Copilot.git

cd AI-Career-Copilot
```

---

### 2. Create Virtual Environment

#### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
BACKEND_URL=https://ai-career-copilot-6u8o.onrender.com

ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key

ENABLE_SENTENCE_TRANSFORMER=false
```

---

## Running the Application

### Start FastAPI Backend

```bash
uvicorn main:app --reload
```

Backend runs on:

```text
http://127.0.0.1:8000
```

---

### Start Streamlit Frontend

```bash
streamlit run app.py
```

Frontend runs on:

```text
http://localhost:8501
```

---

## Deployment Notes

### Render Backend

When deploying on Render:
- use the public backend URL
- avoid localhost references in production

Example:

```env
BACKEND_URL=https://ai-career-copilot-6u8o.onrender.com
```

### Streamlit Cloud

The frontend communicates with FastAPI through REST endpoints only.

Ensure:
- backend service is publicly accessible
- API keys are configured correctly
- CORS settings allow frontend access

---

## Operational Notes

- SQLite is used for lightweight persistence and analysis history.
- In-memory caching reduces repeated resume parsing overhead.
- Uploaded files are processed server-side through FastAPI endpoints.
- LLM calls are isolated behind service-layer abstractions for provider switching.
- Deterministic fallback pipelines are used when LLM APIs are unavailable.

---

## Current Limitations

- PDF parsing accuracy depends heavily on resume formatting consistency.
- Highly stylized resume templates may produce noisy text extraction.
- Semantic similarity scoring is weaker when sentence transformers are disabled.
- Free Render deployments may experience cold-start latency.
- LLM-generated rewrite suggestions are non-deterministic and may require manual review.

---

## Supported File Types

| Format | Supported |
|---|---|
| PDF | Yes |
| DOCX | Yes |

---

## API Overview

| Endpoint | Description |
|---|---|
| `/analyze` | Resume ATS analysis |
| `/compare` | Resume comparison |
| `/rewrite` | Bullet point rewriting |
| `/chat` | Resume-aware chat |
| `/optimize` | Resume optimization |
| `/health` | API health check |

---

## Future Improvements

- Authentication system
- Resume version tracking
- Job recommendation pipeline
- Interview simulation
- Vector database integration
- Fine-tuned ATS prediction models
- Recruiter dashboard
- Batch resume processing

---

## Developer

### Sujanya Srinivas

Data Science & AI Developer focused on:
- Applied NLP Systems
- Resume Intelligence Pipelines
- Retrieval-Augmented Workflows
- Full-Stack AI Applications
- LLM Integration Patterns

---

## License

MIT License

---

## Repository Goal

This project demonstrates:
- full-stack AI application development
- production-ready FastAPI architecture
- semantic NLP pipelines
- LLM integration patterns
- deployment orchestration
- resume intelligence workflows

Suitable for:
- AI/ML Engineer portfolios
- NLP engineering projects
- Full-stack AI showcases
- Applied LLM system demonstrations
