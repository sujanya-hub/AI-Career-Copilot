<div align="center">

<img src="https://img.shields.io/badge/STATUS-LIVE-00ff88?style=for-the-badge&labelColor=0d0d0d" />
<img src="https://img.shields.io/badge/MULTI--LLM-OPENAI%20·%20GROQ%20·%20CLAUDE-A78BFA?style=for-the-badge&labelColor=0d0d0d" />
<img src="https://img.shields.io/badge/RENDER-DEPLOYED-46E3B7?style=for-the-badge&logo=render&logoColor=white&labelColor=0d0d0d" />

<br /><br />

```
 █████╗ ██╗     ██████╗ █████╗ ██████╗ ███████╗███████╗██████╗ 
██╔══██╗██║    ██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗
███████║██║    ██║     ███████║██████╔╝█████╗  █████╗  ██████╔╝
██╔══██║██║    ██║     ██╔══██║██╔══██╗██╔══╝  ██╔══╝  ██╔══██╗
██║  ██║██║    ╚██████╗██║  ██║██║  ██║███████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝

 ██████╗ ██████╗ ██████╗ ██╗██╗      ██████╗ ████████╗
██╔════╝██╔═══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝
██║     ██║   ██║██████╔╝██║██║     ██║   ██║   ██║   
██║     ██║   ██║██╔═══╝ ██║██║     ██║   ██║   ██║   
╚██████╗╚██████╔╝██║     ██║███████╗╚██████╔╝   ██║   
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝   
```

### **AI-Powered Resume Analyzer, ATS Scorer & Job Gap Intelligence Tool**
*Know exactly where your resume falls short — before the recruiter sees it.*

<br />

[![Live App](https://img.shields.io/badge/%20Live%20App-ai--career--copilot1.streamlit.app-A78BFA?style=for-the-badge)](https://ai-career-copilot1.streamlit.app)
[![Backend API](https://img.shields.io/badge/%20Backend%20API-ai--career--copilot--6u8o.onrender.com-46E3B7?style=for-the-badge)](https://ai-career-copilot-6u8o.onrender.com)

</div>

---

## What Is AI Career Copilot?

AI Career Copilot is a **production-deployed resume intelligence tool** that helps job seekers identify skill gaps between their resume and a target job description — then rewrites weak sections with LLM-generated suggestions for better ATS performance.

Paste your resume + target JD → get cosine similarity scores, concrete gap analysis, and rewritten resume bullet points. No generic feedback. No guessing.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│           Streamlit UI (Resume + JD Upload)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP POST (PDF / DOCX)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PARSING LAYER                               │
│          FastAPI Backend — PDF/DOCX Text Extraction            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYSIS LAYER                               │
│   Sentence Transformers → Cosine Similarity Score              │
│   Gap Detection → Skill Alignment Breakdown                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   REWRITING LAYER                               │
│   Multi-LLM Prompt Workflows (OpenAI / Groq / Claude)         │
│   ATS Scoring · Section Rewriting · Fallback Handling          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PERSISTENCE LAYER                             │
│              SQLite — Session History Storage                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Embeddings** | Sentence Transformers |
| **Similarity** | Cosine Similarity (resume ↔ JD) |
| **LLM Providers** | OpenAI API · Groq API · Anthropic Claude API |
| **LLM Fallback** | Multi-provider with automatic fallback |
| **Backend** | FastAPI |
| **Document Parsing** | PDF/DOCX extraction |
| **Session Storage** | SQLite |
| **Frontend** | Streamlit |
| **Deployment** | Streamlit Cloud + Render |

---

## Core Features

- **Resume + JD parsing** — accepts PDF and DOCX formats
- **Cosine similarity scoring** — concrete alignment score between resume and job description
- **Skill gap detection** — surfaces missing skills and weak alignment areas specifically
- **LLM section rewriting** — rewrites weak resume bullets with ATS-optimized language
- **Multi-provider LLM support** — OpenAI, Groq, and Claude with fallback for reliability
- **SQLite session history** — persists analysis results across the session
- **ATS scoring** — structured scoring with actionable improvement flags
- **FastAPI backend** — clean REST API handling all parsing and analysis pipelines

---

## How It Works

```
Step 1: Upload your resume (PDF/DOCX) + paste target job description

Step 2: Sentence Transformers compute cosine similarity
        → Alignment score (0.0 – 1.0)
        → Skill gap breakdown

Step 3: LLM prompt workflows analyze each resume section
        → ATS score per section
        → Specific improvement suggestions

Step 4: Rewritten bullet points generated for weak sections
        → Optimized for ATS keyword matching
        → Maintains your original context

Step 5: Session results saved to SQLite for reference
```

---

## Run Locally

```bash
git clone https://github.com/sujanya-hub/AI-Career-Copilot
cd AI-Career-Copilot
pip install -r requirements.txt
```

Add your API keys to `.env`:
```env
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
ANTHROPIC_API_KEY=your_claude_key
```

```bash
# Start backend
uvicorn backend.main:app --reload

# Start frontend (new terminal)
streamlit run app.py
```

---

## Project Structure

```
AI-Career-Copilot/
├── app.py                      # Streamlit frontend
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── parser.py               # PDF/DOCX text extraction
│   ├── similarity.py           # Sentence Transformers + cosine scoring
│   ├── llm_analyzer.py         # Multi-LLM prompt workflows
│   ├── ats_scorer.py           # ATS scoring logic
│   └── session_store.py        # SQLite persistence
├── requirements.txt
└── .env.example
```

---

## Live Deployments

| Service | URL |
|---------|-----|
| **Streamlit App** | [ai-career-copilot1.streamlit.app](https://ai-career-copilot1.streamlit.app) |
| **Render Backend** | [ai-career-copilot-6u8o.onrender.com](https://ai-career-copilot-6u8o.onrender.com) |

> *Render free-tier has ~7s cold-start on first request. All subsequent requests are fast.*

---

<div align="center">

**Built by [Sujanya Srinivas](https://linkedin.com/in/sujanya-s-538a7a2b1)**
[LinkedIn](https://linkedin.com/in/sujanya-s-538a7a2b1) · [GitHub](https://github.com/sujanya-hub) · [Email](mailto:sujanyasrinivasa@gmail.com)

</div>
