from __future__ import annotations

import json
from typing import Any

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from requests import exceptions as request_exceptions

from frontend.api_client import (
    APIError,
    analyze_resume,
    chat_resume,
    compare_resumes,
    improve_bullet,
    inject_keywords,
    optimize_resume,
    predict_roles,
)
from frontend.export_utils import build_docx_bytes, build_pdf_bytes


def main() -> None:
    st.set_page_config(
        page_title="ResumeIQ Career Copilot",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _styles()
    _init_state()

    st.markdown(
        """
        <div class="hero-shell">
          <div class="hero-top">AI Career Copilot</div>
          <div class="hero-grid">
            <div>
              <div class="hero-title">Turn your resume analyzer into a recruiter-grade career operating system.</div>
              <div class="hero-sub">Deep JD alignment, harsh recruiter feedback, bullet rewriting, resume chat, keyword injection, version comparison, and polished exports in one flow.</div>
            </div>
            <div class="hero-side">
              <div class="glass-card stat-pill">
                <span>Recruiter Lens</span>
                <strong>Reject / Maybe / Strong Hire</strong>
              </div>
              <div class="glass-card stat-pill">
                <span>Explainability</span>
                <strong>Keywords 40 · Experience 30 · Structure 20 · Impact 10</strong>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1], gap="large")
    with left:
        primary_file = st.file_uploader("Primary Resume (PDF)", type=["pdf"], key="primary_resume")
        comparison_file = st.file_uploader("Compare Against Another Resume (Optional)", type=["pdf"], key="comparison_resume")
    with right:
        jd_text = st.text_area(
            "Target Job Description",
            key="job_description",
            height=255,
            placeholder="Paste the full job description, including requirements, responsibilities, and preferred qualifications.",
        )

    c1, c2, c3 = st.columns([1.2, 1.2, 4])
    analyze_clicked = c1.button("Analyze Resume", use_container_width=True, type="primary")
    refresh_roles_clicked = c2.button("Refresh Job Fit", use_container_width=True)

    if analyze_clicked:
        if primary_file is None:
            st.session_state.ui_error = "Upload a primary resume PDF to start."
        elif len((jd_text or "").strip()) < 20:
            st.session_state.ui_error = "Paste a fuller job description so the copilot can score accurately."
        else:
            _run_analysis(primary_file, jd_text)

    analysis = st.session_state.analysis
    if analysis and refresh_roles_clicked:
        try:
            analysis["job_fit_predictions"] = predict_roles(analysis["resume_text"], jd_text)
            st.session_state.analysis = analysis
        except Exception as exc:
            st.session_state.ui_error = _friendly_error(exc)

    if st.session_state.ui_error:
        st.error(st.session_state.ui_error)

    if not analysis:
        st.markdown(_empty_state(), unsafe_allow_html=True)
        return

    _render_score_header(analysis)
    tabs = st.tabs(
        [
            "Overview",
            "🤖 Recruiter Feedback",
            "🛠 Bullet Lab",
            "📊 Compare Versions",
            "💬 Resume Chat",
            "🧩 Keyword Injection",
            "✨ Optimizer",
        ]
    )

    with tabs[0]:
        _render_overview(analysis)

    with tabs[1]:
        _render_recruiter_feedback(analysis)

    with tabs[2]:
        _render_bullet_lab(analysis, jd_text)

    with tabs[3]:
        _render_comparison(comparison_file, jd_text)

    with tabs[4]:
        _render_chat(analysis, jd_text)

    with tabs[5]:
        _render_keyword_injection(analysis, jd_text)

    with tabs[6]:
        _render_optimizer(analysis, jd_text)


def _run_analysis(primary_file: Any, jd_text: str) -> None:
    placeholder = st.empty()
    placeholder.markdown(_skeleton_markup(), unsafe_allow_html=True)
    try:
        payload = analyze_resume(primary_file.getvalue(), primary_file.name, jd_text)
        st.session_state.analysis = payload
        st.session_state.optimized = None
        st.session_state.compare_result = None
        st.session_state.chat_messages = []
        st.session_state.bullet_rewrites = {}
        st.session_state.injection_preview = payload.get("keyword_injection_preview", [])
        st.session_state.ui_error = None
    except Exception as exc:
        st.session_state.ui_error = _friendly_error(exc)
    finally:
        placeholder.empty()


def _render_score_header(analysis: dict[str, Any]) -> None:
    score = int(analysis["ats_score"])
    alignment = int(analysis["deep_match"]["overall_alignment"])
    badges = analysis.get("badges", [])
    left, right = st.columns([1.4, 2], gap="large")
    with left:
        st.plotly_chart(_gauge(score), use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown(
            f"""
            <div class="glass-card score-panel">
              <div class="eyebrow">Recruiter-Visible Outcome</div>
              <div class="score-inline">{score}<span>/100</span></div>
              <div class="align-line">{analysis['deep_match']['summary']}</div>
              <div class="badge-row">{''.join(f'<span class="badge">{badge}</span>' for badge in badges)}</div>
              <div class="preview-line">Score improvement preview: +{max(6, min(18, len(analysis.get('missing_keywords', [])) * 2))} points if you close the biggest gaps.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("JD Alignment", f"{alignment}%")
        m2.metric("Missing Keywords", len(analysis.get("missing_keywords", [])))
        m3.metric("Resume Tier", analysis.get("percentile_label", "Needs Improvement"))


def _render_overview(analysis: dict[str, Any]) -> None:
    deep = analysis["deep_match"]
    score_breakdown = analysis["score_breakdown"]
    metrics = st.columns(4)
    metrics[0].metric("Semantic Match", f"{analysis['semantic_score']}%")
    metrics[1].metric("Skills Overlap", f"{deep['skills_overlap_score']}%")
    metrics[2].metric("Experience Alignment", f"{deep['experience_alignment_score']}%")
    metrics[3].metric("Seniority Signal", deep["qualification_signal"].replace("-", " ").title())

    st.markdown("### Transparent Score Breakdown")
    for component in score_breakdown["components"]:
        st.markdown(
            f"""
            <div class="breakdown-card">
              <div>
                <div class="breakdown-title">{component['name']}</div>
                <div class="breakdown-rationale">{component['rationale']}</div>
              </div>
              <div class="breakdown-score">{component['score']} <span>{component['weight']}%</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    reason_col, fit_col = st.columns([1.2, 1], gap="large")
    with reason_col:
        st.markdown("### Why This Score")
        for reason in score_breakdown["why_this_score"]:
            st.markdown(f"- {reason}")
        st.markdown("### Suggestions")
        for suggestion in analysis.get("suggestions", [])[:6]:
            st.markdown(f"- {suggestion}")
    with fit_col:
        st.markdown("### Job Fit Predictor")
        for prediction in analysis.get("job_fit_predictions", [])[:5]:
            st.markdown(
                f"""
                <div class="fit-card">
                  <div class="fit-role">{prediction['role']}</div>
                  <div class="fit-score">{prediction['match_score']}%</div>
                  <div class="fit-copy">{prediction['rationale']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_recruiter_feedback(analysis: dict[str, Any]) -> None:
    feedback = analysis["recruiter_feedback"]
    decision_class = feedback["hiring_decision"].lower().replace(" ", "-")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            f"""
            <div class="glass-card recruiter-card">
              <div class="eyebrow">Recruiter Verdict</div>
              <div class="decision-badge {decision_class}">{feedback['hiring_decision']}</div>
              <div class="verdict-line">{feedback['recruiter_verdict']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### Strengths")
        for item in feedback["strengths"]:
            st.markdown(f"- {item}")
    with right:
        st.markdown("#### Weaknesses")
        for item in feedback["weaknesses"]:
            st.markdown(f"- {item}")


def _render_bullet_lab(analysis: dict[str, Any], jd_text: str) -> None:
    bullets = analysis.get("bullets", [])
    if not bullets:
        st.info("No distinct resume bullets were parsed from the uploaded resume.")
        return
    for bullet in bullets:
        key = bullet["bullet_id"]
        with st.container():
            st.markdown(f"**{bullet['source']}**")
            st.markdown(f"> {bullet['text']}")
            cols = st.columns([1, 4], gap="small")
            if cols[0].button("Rewrite", key=f"rewrite-{key}"):
                try:
                    rewrite = improve_bullet(
                        analysis["resume_text"],
                        jd_text,
                        bullet["text"],
                        bullet["section"],
                    )
                    st.session_state.bullet_rewrites[key] = rewrite
                    st.session_state.ui_error = None
                except Exception as exc:
                    st.session_state.ui_error = _friendly_error(exc)
            rewrite = st.session_state.bullet_rewrites.get(key)
            if rewrite:
                cols[1].text_area(
                    "Improved bullet",
                    value=rewrite["improved_bullet"],
                    key=f"rewrite-text-{key}",
                    height=110,
                    label_visibility="collapsed",
                )
                cols[1].caption(" | ".join(rewrite.get("rationale", [])))


def _render_comparison(comparison_file: Any, jd_text: str) -> None:
    analysis = st.session_state.analysis
    if comparison_file is None:
        st.info("Upload a second resume at the top to compare versions for the same job description.")
    if comparison_file is not None and st.button("Compare These Versions", use_container_width=True):
        try:
            result = compare_resumes(
                st.session_state.primary_resume_bytes,
                st.session_state.primary_resume_name,
                comparison_file.getvalue(),
                comparison_file.name,
                jd_text,
            )
            st.session_state.compare_result = result
            st.session_state.ui_error = None
        except Exception as exc:
            st.session_state.ui_error = _friendly_error(exc)

    result = st.session_state.compare_result
    if not result:
        return
    st.success(result["summary"])
    cards = st.columns(len(result["deltas"]))
    for idx, delta in enumerate(result["deltas"]):
        cards[idx].metric(delta["label"], delta["candidate"], delta=f"{delta['delta']} vs baseline")
    st.metric("Keyword Coverage Change", f"{result['keyword_coverage_change']} pts")
    st.metric("Improvement %", f"{result['improvement_percent']} pts")


def _render_chat(analysis: dict[str, Any], jd_text: str) -> None:
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask the copilot something like: How do I improve my projects section?")
    if not prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
        response = chat_resume(
            analysis["resume_text"],
            jd_text,
            prompt,
            st.session_state.chat_messages,
            {
                "ats_score": analysis["ats_score"],
                "missing_keywords": analysis["missing_keywords"],
                "suggestions": analysis["suggestions"],
                "deep_match": analysis["deep_match"],
            },
        )
        answer = response["answer"]
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
            if response.get("follow_up_questions"):
                st.caption("Suggested follow-ups: " + " | ".join(response["follow_up_questions"]))
    except Exception as exc:
        st.session_state.ui_error = _friendly_error(exc)


def _render_keyword_injection(analysis: dict[str, Any], jd_text: str) -> None:
    if st.button("Regenerate Injection Plan", use_container_width=True):
        try:
            st.session_state.injection_preview = inject_keywords(
                analysis["resume_text"],
                jd_text,
                analysis["missing_keywords"][:8],
                analysis["parsed_sections"],
            )
            st.session_state.ui_error = None
        except Exception as exc:
            st.session_state.ui_error = _friendly_error(exc)

    previews = st.session_state.injection_preview or analysis.get("keyword_injection_preview", [])
    for preview in previews:
        before, after = st.columns(2, gap="large")
        before.text_area(f"{preview['section'].title()} Before", preview["before"], height=180, disabled=True)
        after.text_area(f"{preview['section'].title()} After", preview["after"], height=180, key=f"after-{preview['section']}")
        st.caption("Injected keywords: " + ", ".join(preview.get("injected_keywords", [])))


def _render_optimizer(analysis: dict[str, Any], jd_text: str) -> None:
    level = st.select_slider(
        "Optimization Level",
        options=["light", "moderate", "aggressive"],
        value="moderate",
    )
    if st.button("Generate Optimized Resume", type="primary", use_container_width=True):
        try:
            st.session_state.optimized = optimize_resume(analysis["resume_text"], jd_text, level)
            st.session_state.ui_error = None
        except Exception as exc:
            st.session_state.ui_error = _friendly_error(exc)

    optimized = st.session_state.optimized
    if not optimized:
        st.info("Generate an optimized version to export it as PDF or DOCX and copy it to your clipboard.")
        return

    cols = st.columns(3)
    cols[0].metric("Original Score", optimized["original_score"])
    cols[1].metric("Optimized Score", optimized["optimized_score"], delta=optimized["score_delta"])
    cols[2].metric("Remaining Missing Keywords", len(optimized.get("missing_keywords", [])))

    st.markdown("### Changes Made")
    for item in optimized.get("changes_made", []):
        st.markdown(f"- {item}")

    optimized_text = optimized["optimized_resume"]
    st.text_area("Optimized Resume", value=optimized_text, height=420)

    docx_bytes = build_docx_bytes("Optimized Resume", optimized_text)
    pdf_bytes = build_pdf_bytes("Optimized Resume", optimized_text)
    d1, d2, d3 = st.columns(3)
    d1.download_button("Download DOCX", data=docx_bytes, file_name="optimized_resume.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    d2.download_button("Download PDF", data=pdf_bytes, file_name="optimized_resume.pdf", mime="application/pdf")
    d3.download_button("Download TXT", data=optimized_text, file_name="optimized_resume.txt", mime="text/plain")
    _copy_button("Copy optimized resume", optimized_text)


def _copy_button(label: str, value: str) -> None:
    payload = json.dumps(value)
    components.html(
        f"""
        <button id="copy-btn" style="width:100%;padding:0.75rem 1rem;border-radius:12px;border:1px solid #293247;background:#101722;color:#d9e4f0;cursor:pointer;">
          {label}
        </button>
        <script>
          const btn = document.getElementById('copy-btn');
          btn.addEventListener('click', async () => {{
            await navigator.clipboard.writeText({payload});
            btn.innerText = 'Copied to clipboard';
          }});
        </script>
        """,
        height=60,
    )


def _gauge(score: int) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 38, "color": "#f4f7fb"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#3e4d66"},
                "bar": {"color": "#3cbf8c"},
                "bgcolor": "#0b1118",
                "bordercolor": "#203042",
                "steps": [
                    {"range": [0, 50], "color": "#45292b"},
                    {"range": [50, 75], "color": "#5b4721"},
                    {"range": [75, 100], "color": "#173b35"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, APIError):
        return str(exc)
    if isinstance(exc, (request_exceptions.ConnectionError, request_exceptions.Timeout)):
        return "The Streamlit app could not reach the FastAPI backend. Start the API server and try again."
    return f"Something went wrong: {exc}"


def _init_state() -> None:
    defaults = {
        "analysis": None,
        "optimized": None,
        "compare_result": None,
        "chat_messages": [],
        "bullet_rewrites": {},
        "injection_preview": [],
        "ui_error": None,
        "primary_resume_bytes": b"",
        "primary_resume_name": "resume.pdf",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if uploaded := st.session_state.get("primary_resume"):
        st.session_state.primary_resume_bytes = uploaded.getvalue()
        st.session_state.primary_resume_name = uploaded.name


def _styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
        :root{
          --bg:#071018; --surface:#0d1824; --surface-2:#122131; --line:#233447; --text:#eaf0f7;
          --muted:#8ea0b2; --accent:#4fd1a5; --accent-2:#7bd3ff; --warn:#f5b642; --danger:#ef6b73;
        }
        html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;background:linear-gradient(180deg,#071018 0%,#0b131d 100%) !important;color:var(--text);}
        .stApp{background:radial-gradient(circle at top right, rgba(79,209,165,0.08), transparent 28%), linear-gradient(180deg,#071018 0%,#0b131d 100%);}
        #MainMenu, header, footer {visibility:hidden;}
        .block-container{max-width:1280px;padding-top:1.2rem;padding-bottom:3rem;}
        .hero-shell{padding:1.5rem;border:1px solid rgba(123,211,255,0.14);border-radius:28px;background:linear-gradient(135deg, rgba(18,33,49,0.95), rgba(10,18,28,0.96));box-shadow:0 24px 80px rgba(0,0,0,0.28);margin-bottom:1.5rem;}
        .hero-top{font-family:'IBM Plex Mono',monospace;font-size:0.78rem;letter-spacing:0.18em;text-transform:uppercase;color:var(--accent-2);margin-bottom:1rem;}
        .hero-grid{display:grid;grid-template-columns:2.3fr 1fr;gap:1rem;}
        .hero-title{font-size:2.5rem;line-height:1.02;font-weight:700;max-width:760px;}
        .hero-sub{font-size:1rem;color:var(--muted);max-width:700px;margin-top:0.85rem;line-height:1.7;}
        .hero-side{display:grid;gap:0.9rem;}
        .glass-card{background:rgba(14,24,36,0.82);border:1px solid rgba(123,211,255,0.12);border-radius:22px;padding:1rem 1.15rem;backdrop-filter:blur(10px);}
        .stat-pill span,.eyebrow{font-family:'IBM Plex Mono',monospace;font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--accent-2);}
        .stat-pill strong{display:block;margin-top:0.45rem;font-size:0.98rem;}
        .score-panel{min-height:220px;display:flex;flex-direction:column;justify-content:center;}
        .score-inline{font-size:4rem;font-weight:700;line-height:1;margin:0.35rem 0 0.7rem;}
        .score-inline span{font-size:1.2rem;color:var(--muted);}
        .align-line,.preview-line,.breakdown-rationale,.fit-copy{color:var(--muted);}
        .badge-row{display:flex;flex-wrap:wrap;gap:0.55rem;margin:1rem 0;}
        .badge{padding:0.4rem 0.8rem;border-radius:999px;border:1px solid rgba(79,209,165,0.22);background:rgba(79,209,165,0.08);color:var(--accent);font-size:0.82rem;}
        .breakdown-card,.fit-card{display:flex;justify-content:space-between;align-items:flex-start;padding:1rem 1.1rem;border-radius:18px;background:rgba(13,24,36,0.92);border:1px solid rgba(35,52,71,0.95);margin-bottom:0.75rem;transition:transform .18s ease,border-color .18s ease;}
        .breakdown-card:hover,.fit-card:hover{transform:translateY(-2px);border-color:rgba(123,211,255,0.25);}
        .breakdown-title,.fit-role{font-weight:700;}
        .breakdown-score,.fit-score{font-size:1.45rem;font-weight:700;color:var(--accent);}
        .breakdown-score span{font-size:0.8rem;color:var(--muted);}
        .recruiter-card{margin-bottom:1rem;}
        .decision-badge{display:inline-block;padding:0.45rem 0.85rem;border-radius:999px;font-weight:700;margin:0.7rem 0 0.8rem;}
        .decision-badge.reject{background:rgba(239,107,115,0.12);color:var(--danger);border:1px solid rgba(239,107,115,0.24);}
        .decision-badge.maybe{background:rgba(245,182,66,0.12);color:var(--warn);border:1px solid rgba(245,182,66,0.24);}
        .decision-badge.strong-hire{background:rgba(79,209,165,0.12);color:var(--accent);border:1px solid rgba(79,209,165,0.24);}
        .verdict-line{font-size:1.05rem;}
        .skeleton-shell{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1rem;}
        .skeleton-card{height:120px;border-radius:20px;background:linear-gradient(90deg,rgba(18,33,49,0.9) 25%, rgba(32,48,66,0.9) 50%, rgba(18,33,49,0.9) 75%);background-size:200% 100%;animation:shimmer 1.4s infinite;}
        @keyframes shimmer {0%{background-position:200% 0}100%{background-position:-200% 0}}
        @media (max-width: 900px){.hero-grid{grid-template-columns:1fr}.score-inline{font-size:3rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _skeleton_markup() -> str:
    return """
    <div class="skeleton-shell">
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
    </div>
    """


def _empty_state() -> str:
    return """
    <div class="glass-card" style="padding:2rem;text-align:center;margin-top:1rem;">
      <div class="hero-top">Ready When You Are</div>
      <div style="font-size:1.25rem;font-weight:700;margin-bottom:0.6rem;">Upload a resume, paste a job description, and let the copilot build the recruiter view.</div>
      <div style="color:#8ea0b2;max-width:720px;margin:0 auto;">You’ll get recruiter-style feedback, transparent scoring, semantic role alignment, interactive bullet rewriting, keyword injection, version comparison, AI chat, and export-ready optimized output.</div>
    </div>
    """
