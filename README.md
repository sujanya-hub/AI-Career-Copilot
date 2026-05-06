# AI-Career-Copilot

Production-ready resume analysis and ATS optimization platform built with FastAPI and Streamlit.

The system combines deterministic ATS scoring, semantic similarity matching, and optional LLM-assisted optimization pipelines for resume evaluation and recruiter-style feedback.

---

## Live Deployment

* Frontend: [AI-Career-Copilot Frontend](https://ai-career-copilot1.streamlit.app/?utm_source=chatgpt.com)
* Backend API: [AI-Career-Copilot Backend API](https://ai-career-copilot-6u8o.onrender.com/?utm_source=chatgpt.com)

---

## Core Features

### ATS Resume Scoring

* Deterministic ATS scoring pipeline
* Explainable weighted scoring system
* Section-wise resume evaluation
* Keyword density analysis

### Semantic Job Description Matching

* Resume ↔ JD similarity scoring
* Missing skill detection
* Role alignment analysis
* Semantic keyword matching

### Recruiter Feedback Pipeline

* Recruiter-style evaluation mode
* Resume weakness detection
* Improvement recommendations
* Hiring-readiness analysis

### Bullet Point Rewrite Pipeline

* Rewrites weak resume bullets
* ATS keyword enrichment
* Action-oriented formatting improvements
* Quantification suggestions

### Resume Comparison Engine

* Compare multiple resumes
* ATS score comparison
* Skill overlap analysis
* Candidate strength evaluation

### Context-Aware Resume Chat

* Resume-aware conversational assistant
* Multi-provider LLM routing
* Context injection using uploaded resume data
* Career optimization support

### Resume Optimization Export

* Optimized resume export
* PDF support
* DOCX support

---

# Why This Architecture?

Traditional ATS systems rely heavily on keyword matching and often fail to capture semantic alignment between resumes and job descriptions.

AI-Career-Copilot combines:

* deterministic scoring pipelines
* semantic embedding similarity
* optional LLM-assisted refinement

to balance:

* explainability
* reliability
* contextual understanding

The backend intentionally separates rule-based scoring from LLM generation so the application remains functional even when external AI providers fail or rate-limit requests.

---

# System Architecture

```text
Streamlit Frontend
        ↓
FastAPI REST API
        ↓
Resume Parsing + Scoring Layer
        ↓
Semantic Matching + LLM Services
        ↓
SQLite Persistence + Export Layer
```

---

# Tech Stack

| Layer           | Technology                          |
| --------------- | ----------------------------------- |
| Frontend        | Streamlit                           |
| Backend         | FastAPI                             |
| API Server      | Uvicorn                             |
| NLP             | Sentence Transformers, Scikit-learn |
| LLM Providers   | OpenAI, Groq, Claude                |
| Database        | SQLite                              |
| File Processing | PyPDF2, python-docx                 |
| Deployment      | Render, Streamlit Cloud             |

---

# Project Structure

```bash
AI-Career-Copilot/
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

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/AI-Career-Copilot.git

cd AI-Career-Copilot
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
BACKEND_URL=https://ai-career-copilot-6u8o.onrender.com

ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key

ENABLE_SENTENCE_TRANSFORMER=false
```

---

# Running the Application

## Start FastAPI Backend

```bash
uvicorn main:app --reload
```

Backend runs on:

```bash
http://127.0.0.1:8000
```

---

## Start Streamlit Frontend

```bash
streamlit run app.py
```

Frontend runs on:

```bash
http://localhost:8501
```

---

# Deployment Notes

## Render Backend

When deploying on Render:

* Use the public Render backend URL
* Do not use:

  ```bash
  127.0.0.1
  ```

Example:

```env
BACKEND_URL=https://ai-career-copilot-6u8o.onrender.com
```

---

## Streamlit Cloud

The Streamlit frontend communicates with FastAPI through REST endpoints only.

Ensure:

* backend service is publicly accessible
* API keys are configured in Streamlit secrets/environment settings

---

# Operational Notes

* SQLite is used for lightweight persistence and analysis history.
* In-memory caching reduces repeated resume parsing overhead.
* Uploaded files are processed server-side through FastAPI endpoints.
* LLM calls are isolated behind service-layer abstractions for provider switching.
* Deterministic fallback pipelines are used when LLM APIs are unavailable.

---

# Design Tradeoffs

The platform prioritizes explainability and operational reliability over fully generative scoring.

For this reason:

* ATS scoring remains deterministic
* semantic similarity is separated from LLM inference
* recruiter feedback generation is isolated from scoring logic

This allows the application to continue functioning even when external LLM providers fail.

---

# Current Limitations

* PDF parsing accuracy depends on resume formatting consistency.
* Highly stylized resume templates may produce noisy text extraction.
* Semantic similarity scoring is less reliable when:

  ```env
  ENABLE_SENTENCE_TRANSFORMER=false
  ```
* Free Render deployments may experience cold-start latency.
* LLM-generated rewrite suggestions are non-deterministic and may require manual review.

---

# Supported File Types

| Format | Supported |
| ------ | --------- |
| PDF    | Yes       |
| DOCX   | Yes       |

---

# API Overview

| Endpoint    | Description            |
| ----------- | ---------------------- |
| `/analyze`  | Resume ATS analysis    |
| `/compare`  | Resume comparison      |
| `/rewrite`  | Bullet point rewriting |
| `/chat`     | Resume-aware chat      |
| `/optimize` | Resume optimization    |
| `/health`   | API health check       |

---

# Future Improvements

* Authentication system
* Resume version tracking
* Job recommendation pipeline
* Interview simulation
* Vector database integration
* Fine-tuned ATS prediction models
* Recruiter dashboard
* Batch resume processing

---

# Author

**Sujanya Srinivas**
Data Science & AI Developer

---

# License

MIT License

---

# Repository Goal

This project demonstrates:

* full-stack AI application development
* production-ready FastAPI architecture
* semantic NLP pipelines
* LLM integration patterns
* resume intelligence workflows
* deployment and API orchestration

Suitable for:

* AI/ML Engineer portfolios
* NLP engineering projects
* Full-stack AI development showcases
* Applied LLM system design demonstrations
