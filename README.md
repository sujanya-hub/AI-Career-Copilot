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

3. Set API keys if you want live LLM generation:

```bash
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
- If LLM keys are missing, the app still works using strong deterministic fallbacks.
- Analysis results are cached in-memory and persisted to SQLite history.
