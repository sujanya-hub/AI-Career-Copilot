# ResumeIQ Career Copilot

Production-style Streamlit + FastAPI resume platform with:

- ATS scoring with explainable weights
- Recruiter feedback mode
- Semantic JD alignment
- Bullet point rewriting
- Resume comparison
- AI resume chat
- Smart keyword injection
- Job fit prediction
- Resume optimization with PDF/DOCX export

## Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables before starting the apps:

```bash
set BACKEND_URL=https://ai-career-copilot-6u8o.onrender.com
set ANTHROPIC_API_KEY=your_anthropic_key
set GROQ_API_KEY=your_key
set OPENAI_API_KEY=your_key
```

4. Start FastAPI:

```bash
uvicorn main:app --reload
```

5. Start Streamlit:

```bash
streamlit run app.py
```

## Notes

- The backend accepts PDF uploads for analysis and comparison.
- For Render deployments, `BACKEND_URL` on the Streamlit service must point to the public FastAPI service URL, not `127.0.0.1`.
- The Copilot Chat tab requires `ANTHROPIC_API_KEY` on the Streamlit service because that request is sent directly from the frontend app.
- If LLM keys are missing, the app still works using strong deterministic fallbacks.
- Analysis results are cached in-memory and persisted to SQLite history.
