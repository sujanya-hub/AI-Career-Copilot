from frontend.career_copilot_app import main as _career_copilot_main

_career_copilot_main()
raise SystemExit

"""
ResumeIQ — Enterprise SaaS UI
AI Resume Analyzer + Optimizer (FastAPI backend)
Production-ready build with stable state management.
"""

import sys
import os
import json
import datetime
import logging

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
import requests

# ─── Logger ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("resumeiq")

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ResumeIQ · AI Resume Analyzer",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Backend base URL ─────────────────────────────────────────────────────────

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

# ─── Global CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap');

    :root {
        --bg-base:       #07080d;
        --bg-surface:    #0e1018;
        --bg-elevated:   #161922;
        --bg-overlay:    #1e2230;
        --border:        #262b3d;
        --border-light:  #1e2230;
        --accent:        #5b7fff;
        --accent-glow:   rgba(91,127,255,0.18);
        --accent-subtle: rgba(91,127,255,0.08);
        --green:         #34d399;
        --green-bg:      rgba(52,211,153,0.08);
        --green-border:  rgba(52,211,153,0.2);
        --red:           #f87171;
        --red-bg:        rgba(248,113,113,0.08);
        --red-border:    rgba(248,113,113,0.2);
        --amber:         #fbbf24;
        --amber-bg:      rgba(251,191,36,0.08);
        --amber-border:  rgba(251,191,36,0.2);
        --purple:        #a78bfa;
        --purple-bg:     rgba(167,139,250,0.08);
        --purple-border: rgba(167,139,250,0.2);
        --text-primary:  #e8eaf0;
        --text-secondary:#8b92a8;
        --text-muted:    #4a5168;
        --radius-sm:     6px;
        --radius-md:     10px;
        --radius-lg:     16px;
        --font-display:  'Syne', sans-serif;
        --font-mono:     'JetBrains Mono', monospace;
        --font-body:     'Outfit', sans-serif;
    }

    html, body, [class*="css"] {
        font-family: var(--font-body);
        background-color: var(--bg-base) !important;
        color: var(--text-primary);
    }
    .stApp { background-color: var(--bg-base); }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 0 !important; padding-bottom: 4rem; max-width: 1200px; }
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

    /* TOPBAR */
    .topbar { display:flex; align-items:center; justify-content:space-between; padding:1.1rem 0; border-bottom:1px solid var(--border); margin-bottom:2.5rem; }
    .topbar-brand { display:flex; align-items:center; gap:0.75rem; }
    .brand-icon { width:34px; height:34px; background:linear-gradient(135deg,#5b7fff 0%,#a78bfa 100%); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1rem; }
    .brand-name { font-family:var(--font-display); font-weight:700; font-size:1.15rem; color:var(--text-primary); letter-spacing:-0.02em; }
    .brand-name span { color:var(--accent); }
    .topbar-badge { font-family:var(--font-mono); font-size:0.62rem; letter-spacing:0.12em; text-transform:uppercase; color:var(--text-muted); background:var(--bg-elevated); border:1px solid var(--border); border-radius:99px; padding:0.3rem 0.85rem; }

    /* HERO */
    .hero { margin-bottom:2.25rem; }
    .hero-eyebrow { font-family:var(--font-mono); font-size:0.65rem; letter-spacing:0.2em; text-transform:uppercase; color:var(--accent); margin-bottom:0.75rem; display:flex; align-items:center; gap:0.5rem; }
    .hero-eyebrow::before { content:''; display:inline-block; width:18px; height:1px; background:var(--accent); opacity:0.6; }
    .hero-title { font-family:var(--font-display); font-weight:800; font-size:2.8rem; line-height:1.08; letter-spacing:-0.03em; color:var(--text-primary); margin:0 0 0.85rem 0; }
    .hero-sub { font-size:1rem; color:var(--text-secondary); font-weight:400; max-width:560px; line-height:1.65; }

    /* INPUT CARDS */
    .input-card { background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:0; overflow:hidden; transition:border-color 0.25s,box-shadow 0.25s; position:relative; }
    .input-card:hover { border-color:#2e3450; box-shadow:0 0 0 1px rgba(91,127,255,0.08),0 8px 32px rgba(0,0,0,0.35); }
    .input-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,var(--accent),var(--purple)); opacity:0; transition:opacity 0.25s; }
    .input-card:hover::before { opacity:1; }
    .input-card-header { display:flex; align-items:center; gap:0.65rem; padding:1rem 1.25rem 0.85rem; border-bottom:1px solid var(--border-light); background:var(--bg-elevated); }
    .input-card-icon-wrap { width:30px; height:30px; background:var(--accent-subtle); border:1px solid rgba(91,127,255,0.18); border-radius:7px; display:flex; align-items:center; justify-content:center; font-size:0.85rem; flex-shrink:0; }
    .input-card-label-group { display:flex; flex-direction:column; gap:0.05rem; }
    .input-card-title { font-family:var(--font-display); font-weight:600; font-size:0.88rem; color:var(--text-primary); line-height:1.2; }
    .input-card-subtitle { font-family:var(--font-mono); font-size:0.58rem; letter-spacing:0.12em; text-transform:uppercase; color:var(--text-muted); }
    .input-card-status { margin-left:auto; }
    .status-dot-idle { width:7px; height:7px; border-radius:50%; background:var(--border); display:inline-block; }
    .status-dot-ready { width:7px; height:7px; border-radius:50%; background:var(--green); display:inline-block; box-shadow:0 0 6px var(--green); }
    .input-card-body { padding:1.1rem 1.25rem 1.25rem; }

    /* UPLOAD ZONE */
    .upload-zone { border:1.5px dashed var(--border); border-radius:var(--radius-md); background:var(--bg-base); transition:border-color 0.2s,background 0.2s; position:relative; overflow:hidden; }
    .upload-zone:hover { border-color:var(--accent); background:var(--accent-subtle); }
    [data-testid="stFileUploader"] { background:transparent !important; border:none !important; padding:0 !important; }
    [data-testid="stFileUploaderDropzone"] { background:transparent !important; border:none !important; padding:1.5rem 1rem !important; min-height:100px !important; }
    [data-testid="stFileUploaderDropzone"]:hover { background:transparent !important; }
    [data-testid="stFileDropzoneInstructions"] > div > span { font-family:var(--font-body) !important; font-size:0.8rem !important; color:var(--text-muted) !important; }
    [data-testid="stFileDropzoneInstructions"] > div > small { font-family:var(--font-mono) !important; font-size:0.65rem !important; color:var(--text-muted) !important; opacity:0.6; }
    [data-testid="stFileUploaderDropzone"] button { background:var(--bg-elevated) !important; color:var(--accent) !important; border:1px solid rgba(91,127,255,0.25) !important; border-radius:var(--radius-sm) !important; font-family:var(--font-mono) !important; font-size:0.68rem !important; letter-spacing:0.08em !important; padding:0.35rem 0.9rem !important; transition:all 0.15s !important; box-shadow:none !important; transform:none !important; width:auto !important; }
    [data-testid="stFileUploaderDropzone"] button:hover { background:var(--accent-subtle) !important; border-color:var(--accent) !important; transform:none !important; box-shadow:none !important; }
    [data-testid="stFileUploaderFile"] { background:var(--green-bg) !important; border:1px solid var(--green-border) !important; border-radius:var(--radius-sm) !important; padding:0.4rem 0.75rem !important; margin-top:0.5rem !important; }
    [data-testid="stFileUploaderFileName"] { font-family:var(--font-mono) !important; font-size:0.72rem !important; color:var(--green) !important; }
    [data-testid="stFileUploaderFileData"] { font-family:var(--font-mono) !important; font-size:0.62rem !important; color:var(--text-muted) !important; }
    [data-testid="stFileUploaderDeleteBtn"] button { background:transparent !important; border:none !important; color:var(--text-muted) !important; box-shadow:none !important; transform:none !important; width:auto !important; padding:0 !important; }
    [data-testid="stFileUploaderDeleteBtn"] button:hover { color:var(--red) !important; background:transparent !important; box-shadow:none !important; }

    /* TEXTAREA */
    .textarea-zone { border:1.5px solid var(--border); border-radius:var(--radius-md); background:var(--bg-base); overflow:hidden; transition:border-color 0.2s,box-shadow 0.2s; }
    .textarea-zone:focus-within { border-color:var(--accent) !important; box-shadow:0 0 0 3px var(--accent-glow); }
    .stTextArea { margin:0 !important; }
    .stTextArea > div { margin:0 !important; }
    .stTextArea textarea { background:var(--bg-base) !important; border:none !important; border-radius:0 !important; color:var(--text-primary) !important; font-family:var(--font-body) !important; font-size:0.875rem !important; line-height:1.7 !important; resize:none !important; padding:1rem !important; box-shadow:none !important; outline:none !important; }
    .stTextArea textarea:focus { border:none !important; box-shadow:none !important; outline:none !important; }
    .stTextArea textarea::placeholder { color:var(--text-muted) !important; font-size:0.82rem !important; }
    .stTextArea label { display:none !important; }
    [data-testid="InputInstructions"] { display:none !important; }
    .textarea-footer { display:flex; align-items:center; justify-content:space-between; padding:0.45rem 0.85rem; border-top:1px solid var(--border-light); background:var(--bg-elevated); }
    .textarea-footer-hint { font-family:var(--font-mono); font-size:0.58rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-muted); }

    /* BUTTON */
    .btn-row-wrapper { margin-top:1.5rem; }
    .stButton > button { background:linear-gradient(135deg,#5b7fff 0%,#7c6fff 100%) !important; color:#fff !important; border:none !important; border-radius:var(--radius-md) !important; font-family:var(--font-display) !important; font-size:0.9rem !important; font-weight:600 !important; letter-spacing:0.01em !important; padding:0.85rem 2.5rem !important; cursor:pointer !important; transition:all 0.22s !important; box-shadow:0 4px 24px rgba(91,127,255,0.32) !important; width:100% !important; }
    .stButton > button:hover { transform:translateY(-2px) !important; box-shadow:0 8px 36px rgba(91,127,255,0.5) !important; background:linear-gradient(135deg,#6b8fff 0%,#8c7fff 100%) !important; }
    .stButton > button:active { transform:translateY(0) !important; box-shadow:0 2px 12px rgba(91,127,255,0.3) !important; }
    .stButton > button:disabled { background:var(--bg-elevated) !important; color:var(--text-muted) !important; box-shadow:none !important; cursor:not-allowed !important; transform:none !important; border:1px solid var(--border) !important; }
    .btn-sublabel { text-align:center; margin-top:0.55rem; font-family:var(--font-mono); font-size:0.6rem; letter-spacing:0.12em; text-transform:uppercase; color:var(--text-muted); }

    /* DIVIDER */
    .section-divider { border:none; border-top:1px solid var(--border); margin:2rem 0; }

    /* RESULTS */
    .results-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:1.75rem; }
    .results-title { font-family:var(--font-display); font-weight:700; font-size:1.5rem; letter-spacing:-0.02em; color:var(--text-primary); }
    .results-timestamp { font-family:var(--font-mono); font-size:0.65rem; color:var(--text-muted); letter-spacing:0.08em; }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { background:var(--bg-surface) !important; border:1px solid var(--border) !important; border-radius:var(--radius-md) !important; padding:0.25rem !important; gap:0 !important; margin-bottom:1.75rem !important; }
    .stTabs [data-baseweb="tab"] { background:transparent !important; color:var(--text-muted) !important; border-radius:var(--radius-sm) !important; font-family:var(--font-body) !important; font-size:0.85rem !important; font-weight:500 !important; padding:0.5rem 1.1rem !important; border:none !important; transition:all 0.15s !important; }
    .stTabs [data-baseweb="tab"]:hover { color:var(--text-primary) !important; }
    .stTabs [aria-selected="true"] { background:var(--bg-elevated) !important; color:var(--text-primary) !important; box-shadow:0 1px 4px rgba(0,0,0,0.3) !important; }
    .stTabs [data-baseweb="tab-highlight"] { display:none !important; }
    .stTabs [data-baseweb="tab-border"] { display:none !important; }

    /* SCORE CARD */
    .score-card { background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:2rem 1.75rem; text-align:center; position:relative; overflow:hidden; }
    .score-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#5b7fff,#a78bfa,#34d399); }
    .score-ring-label { font-family:var(--font-mono); font-size:0.62rem; letter-spacing:0.2em; text-transform:uppercase; color:var(--text-muted); margin-bottom:0.4rem; }
    .score-number { font-family:var(--font-display); font-weight:800; font-size:4.5rem; line-height:1; letter-spacing:-0.04em; background:linear-gradient(135deg,#5b7fff,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .score-denom { font-family:var(--font-mono); font-size:1rem; color:var(--text-muted); margin-left:0.25rem; }
    .score-grade-badge { display:inline-block; margin-top:0.85rem; font-size:0.78rem; font-weight:500; padding:0.3rem 0.9rem; border-radius:99px; }

    /* METRIC GRID */
    .metric-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.75rem; margin-top:1rem; }
    .metric-card { background:var(--bg-elevated); border:1px solid var(--border-light); border-radius:var(--radius-md); padding:1.1rem 1.25rem; transition:border-color 0.2s,transform 0.2s; }
    .metric-card:hover { border-color:var(--border); transform:translateY(-1px); }
    .metric-value { font-family:var(--font-display); font-weight:700; font-size:1.85rem; letter-spacing:-0.03em; color:var(--text-primary); line-height:1; }
    .metric-label { font-family:var(--font-mono); font-size:0.6rem; letter-spacing:0.14em; text-transform:uppercase; color:var(--text-muted); margin-top:0.35rem; }

    /* PROGRESS BARS */
    .progress-wrap { background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.5rem; margin-bottom:0.75rem; }
    .progress-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:0.65rem; }
    .progress-name { font-size:0.82rem; font-weight:500; color:var(--text-secondary); }
    .progress-pct { font-family:var(--font-mono); font-size:0.78rem; color:var(--text-primary); font-weight:500; }
    .progress-track { background:var(--bg-overlay); border-radius:99px; height:6px; overflow:hidden; }
    .progress-fill { height:100%; border-radius:99px; transition:width 0.6s ease; }

    /* KEYWORD PILLS */
    .pills-container { display:flex; flex-wrap:wrap; gap:0.45rem; max-height:160px; overflow-y:auto; padding-right:0.25rem; }
    .pill { font-family:var(--font-mono); font-size:0.72rem; padding:0.3rem 0.8rem; border-radius:99px; letter-spacing:0.03em; cursor:default; transition:transform 0.15s,filter 0.15s; white-space:nowrap; }
    .pill:hover { transform:translateY(-1px); filter:brightness(1.2); }
    .pill-matched { background:var(--green-bg); color:var(--green); border:1px solid var(--green-border); }
    .pill-missing { background:var(--red-bg); color:var(--red); border:1px solid var(--red-border); }
    .pill-neutral { background:var(--accent-subtle); color:var(--accent); border:1px solid rgba(91,127,255,0.2); }
    .pill-count { font-family:var(--font-mono); font-size:0.62rem; padding:0.15rem 0.5rem; border-radius:99px; margin-left:0.4rem; vertical-align:middle; }
    .pill-count-green { background:var(--green-bg); color:var(--green); border:1px solid var(--green-border); }
    .pill-count-red { background:var(--red-bg); color:var(--red); border:1px solid var(--red-border); }

    /* SUGGESTIONS */
    .suggestion-item { background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-md); padding:1rem 1.25rem 1rem 1rem; margin-bottom:0.65rem; font-size:0.875rem; color:var(--text-secondary); line-height:1.65; display:flex; align-items:flex-start; gap:0.85rem; transition:border-color 0.2s; }
    .suggestion-item:hover { border-color:#2e3450; }
    .suggestion-index { font-family:var(--font-mono); font-size:0.65rem; color:var(--accent); background:var(--accent-subtle); border:1px solid rgba(91,127,255,0.2); border-radius:4px; padding:0.2rem 0.45rem; margin-top:0.1rem; flex-shrink:0; min-width:28px; text-align:center; }

    /* PANELS */
    .panel { background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.5rem; margin-bottom:1rem; }
    .panel-title { font-family:var(--font-display); font-weight:600; font-size:0.9rem; color:var(--text-primary); margin-bottom:1.25rem; padding-bottom:0.85rem; border-bottom:1px solid var(--border-light); display:flex; align-items:center; gap:0.5rem; }

    /* INSIGHT ROWS */
    .insight-row { display:flex; align-items:center; justify-content:space-between; padding:0.7rem 0; border-bottom:1px solid var(--border-light); }
    .insight-row:last-child { border-bottom:none; }
    .insight-label { font-size:0.82rem; color:var(--text-secondary); }
    .insight-badge { font-family:var(--font-mono); font-size:0.68rem; padding:0.25rem 0.7rem; border-radius:99px; font-weight:500; }

    /* ALERTS */
    .alert-box { background:var(--amber-bg); border:1px solid var(--amber-border); border-radius:var(--radius-md); padding:0.9rem 1.1rem; color:var(--amber); font-size:0.85rem; margin-bottom:0.6rem; display:flex; align-items:center; gap:0.6rem; }
    .alert-box-error { background:var(--red-bg); border-color:var(--red-border); color:var(--red); }

    /* EXPORT BAR */
    .export-bar { background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:1.25rem 1.5rem; display:flex; align-items:center; justify-content:space-between; margin-top:1.5rem; flex-wrap:wrap; gap:1rem; }
    .export-bar-left { display:flex; align-items:center; gap:0.75rem; }
    .export-icon { width:36px; height:36px; background:var(--accent-subtle); border:1px solid rgba(91,127,255,0.2); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1rem; }
    .export-text-title { font-family:var(--font-display); font-weight:600; font-size:0.9rem; color:var(--text-primary); }
    .export-text-sub { font-size:0.75rem; color:var(--text-muted); margin-top:0.1rem; }

    /* OPTIMIZER */
    .optimizer-hero { background:linear-gradient(135deg,rgba(91,127,255,0.06) 0%,rgba(167,139,250,0.06) 100%); border:1px solid var(--purple-border); border-radius:var(--radius-lg); padding:2rem 2rem 1.75rem; margin-bottom:1.75rem; position:relative; overflow:hidden; }
    .optimizer-hero::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#5b7fff,#a78bfa); }
    .optimizer-hero-title { font-family:var(--font-display); font-weight:700; font-size:1.25rem; letter-spacing:-0.02em; color:var(--text-primary); margin-bottom:0.4rem; }
    .optimizer-hero-sub { font-size:0.85rem; color:var(--text-secondary); line-height:1.6; max-width:620px; }
    .optimizer-feature-list { display:flex; flex-wrap:wrap; gap:0.5rem; margin-top:1.1rem; }
    .optimizer-feature-pill { font-family:var(--font-mono); font-size:0.65rem; padding:0.25rem 0.7rem; border-radius:99px; background:var(--purple-bg); color:var(--purple); border:1px solid var(--purple-border); letter-spacing:0.05em; }

    /* EMPTY STATE */
    .empty-state { text-align:center; padding:5rem 2rem; color:var(--text-muted); }
    .empty-icon { font-size:3rem; margin-bottom:1.25rem; opacity:0.3; display:block; }
    .empty-title { font-family:var(--font-display); font-size:1.1rem; font-weight:600; color:var(--text-muted); margin-bottom:0.5rem; }
    .empty-sub { font-size:0.82rem; color:var(--text-muted); opacity:0.7; max-width:380px; margin:0 auto; line-height:1.6; }
    .empty-steps { display:flex; align-items:center; justify-content:center; gap:1.5rem; margin-top:2rem; flex-wrap:wrap; }
    .empty-step { background:var(--bg-surface); border:1px solid var(--border); border-radius:var(--radius-md); padding:0.85rem 1.25rem; display:flex; align-items:center; gap:0.6rem; font-size:0.8rem; color:var(--text-secondary); }
    .empty-step-num { font-family:var(--font-mono); font-size:0.65rem; color:var(--accent); background:var(--accent-subtle); border:1px solid rgba(91,127,255,0.2); border-radius:4px; padding:0.1rem 0.4rem; min-width:22px; text-align:center; }
    .empty-arrow { color:var(--text-muted); font-size:0.7rem; opacity:0.4; }

    .stSpinner > div { border-top-color:var(--accent) !important; }
    button[kind="secondary"] { background:var(--bg-elevated) !important; color:var(--text-muted) !important; border:1px solid var(--border) !important; border-radius:var(--radius-sm) !important; font-family:var(--font-mono) !important; font-size:0.68rem !important; padding:0.3rem 0.75rem !important; box-shadow:none !important; transform:none !important; width:auto !important; }
    [data-testid="stDownloadButton"] button { background:var(--bg-elevated) !important; color:var(--text-secondary) !important; border:1px solid var(--border) !important; border-radius:var(--radius-sm) !important; font-family:var(--font-mono) !important; font-size:0.7rem !important; letter-spacing:0.08em !important; padding:0.45rem 1.1rem !important; transition:all 0.15s !important; box-shadow:none !important; }
    [data-testid="stDownloadButton"] button:hover { background:var(--bg-overlay) !important; border-color:var(--accent) !important; color:var(--text-primary) !important; transform:none !important; box-shadow:none !important; }
    [data-testid="stMetric"] { background:var(--bg-elevated); border:1px solid var(--border-light); border-radius:var(--radius-md); padding:1rem 1.25rem; }
    [data-testid="stMetric"] label { font-family:var(--font-mono) !important; font-size:0.6rem !important; letter-spacing:0.14em !important; text-transform:uppercase !important; color:var(--text-muted) !important; }
    [data-testid="stMetricValue"] { font-family:var(--font-display) !important; font-size:1.6rem !important; font-weight:700 !important; color:var(--text-primary) !important; }
    [data-testid="stMetricDelta"] { font-family:var(--font-mono) !important; font-size:0.72rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Session state bootstrap ──────────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "optimized_resume":  None,
        "opt_timestamp":     None,
        "opt_error":         None,
        "is_generating":     False,
        "opt_analysis_id":   None,
        "analysis_result":   None,   # cached parsed analysis dict
        "resume_text_cache": None,   # extracted resume text from backend
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ─── API helpers ──────────────────────────────────────────────────────────────

def _unwrap_response(raw: dict) -> dict:
    """
    Support both flat  {"ats_score": 75, ...}
    and nested         {"data": {"ats_score": 75, ...}}
    response structures from the backend.
    """
    if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
        return raw["data"]
    return raw


def _safe_list(val) -> list:
    """Return val as a list, handling None / non-list gracefully."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, (set, tuple)):
        return list(val)
    return []


def _safe_int(val, default: int = 0) -> int:
    """Coerce val to int with a fallback."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def call_analyze_api(pdf_bytes: bytes, filename: str, jd_text: str) -> dict:
    """
    POST /analyze  — multipart/form-data
    Fields: file (PDF), job_description (str)
    Returns the unwrapped data dict.
    """
    url = f"{BACKEND_URL}/analyze"
    files  = {"file": (filename, pdf_bytes, "application/pdf")}
    data   = {"job_description": jd_text}

    logger.debug("POST %s | file=%s jd_len=%d", url, filename, len(jd_text))
    resp = requests.post(url, files=files, data=data, timeout=60)
    logger.debug("Response status: %s", resp.status_code)

    try:
        raw = resp.json()
        logger.debug("Response JSON: %s", json.dumps(raw, indent=2)[:1000])
    except Exception as exc:
        logger.error("JSON decode error: %s | body: %s", exc, resp.text[:500])
        raise ValueError(f"Backend returned non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}")

    if resp.status_code != 200:
        error_msg = raw.get("detail") or raw.get("error") or raw.get("message") or str(raw)
        raise RuntimeError(f"Backend error {resp.status_code}: {error_msg}")

    return _unwrap_response(raw)


def call_optimize_api(resume_text: str, jd_text: str) -> dict:
    """
    POST /optimize  — JSON body
    Fields: resume_text, job_description
    Returns the unwrapped data dict.
    """
    url     = f"{BACKEND_URL}/optimize"
    payload = {"resume_text": resume_text, "job_description": jd_text}

    logger.debug("POST %s | resume_len=%d jd_len=%d", url, len(resume_text), len(jd_text))
    resp = requests.post(url, json=payload, timeout=120)
    logger.debug("Response status: %s", resp.status_code)

    try:
        raw = resp.json()
        logger.debug("Response JSON: %s", json.dumps(raw, indent=2)[:1000])
    except Exception as exc:
        logger.error("JSON decode error: %s | body: %s", exc, resp.text[:500])
        raise ValueError(f"Backend returned non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}")

    if resp.status_code != 200:
        error_msg = raw.get("detail") or raw.get("error") or raw.get("message") or str(raw)
        raise RuntimeError(f"Backend error {resp.status_code}: {error_msg}")

    return _unwrap_response(raw)


def parse_analysis(data: dict) -> dict:
    """
    Normalise the analysis dict so downstream code never crashes on missing keys.
    Accepts both snake_case and camelCase field names from the backend.
    """
    def _get(*keys, default=None):
        for k in keys:
            if k in data:
                return data[k]
        return default

    return {
        "ats_score":        _safe_int(_get("ats_score", "atsScore", "score"),          0),
        "semantic_score":   _safe_int(_get("semantic_score", "semanticScore"),         0),
        "keyword_score":    _safe_int(_get("keyword_score", "keywordScore"),           0),
        "matched_keywords": _safe_list(_get("matched_keywords", "matchedKeywords",
                                           "matched")),
        "missing_keywords": _safe_list(_get("missing_keywords", "missingKeywords",
                                           "missing")),
        "jd_top_keywords":  _safe_list(_get("jd_top_keywords", "jdTopKeywords",
                                           "top_keywords", "topKeywords")),
        "suggestions":      _safe_list(_get("suggestions", "improvements",
                                           "recommendations")),
        "resume_text":      _get("resume_text", "resumeText", "extracted_text", default=""),
    }

# ─── UI helpers ──────────────────────────────────────────────────────────────

def grade_info(score: int) -> tuple:
    if score >= 80:
        return (
            "Strong Match",
            "background:var(--green-bg);color:var(--green);border:1px solid var(--green-border);",
            "High ATS compatibility — strong chance of passing automated filters.",
        )
    if score >= 60:
        return (
            "Moderate Match",
            "background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-border);",
            "Reasonable alignment — targeted improvements will boost your ATS odds.",
        )
    if score >= 40:
        return (
            "Weak Match",
            "background:rgba(251,146,60,0.08);color:#fb923c;border:1px solid rgba(251,146,60,0.2);",
            "Significant gaps detected — substantial revision recommended.",
        )
    return (
        "Poor Match",
        "background:var(--red-bg);color:var(--red);border:1px solid var(--red-border);",
        "Very low alignment — consider rewriting key sections to match the JD.",
    )


def progress_color(pct: int) -> str:
    if pct >= 70:
        return "linear-gradient(90deg,#34d399,#059669)"
    if pct >= 45:
        return "linear-gradient(90deg,#fbbf24,#d97706)"
    return "linear-gradient(90deg,#f87171,#dc2626)"


def render_progress(label: str, pct: int) -> None:
    color = progress_color(pct)
    st.markdown(
        f"""
        <div class="progress-wrap">
            <div class="progress-header">
                <span class="progress-name">{label}</span>
                <span class="progress-pct">{pct}%</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{pct}%;background:{color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert(msg: str, kind: str = "warn") -> None:
    icon  = "⚠" if kind == "warn" else "✕"
    extra = "alert-box-error" if kind == "error" else ""
    st.markdown(
        f'<div class="alert-box {extra}"><span>{icon}</span>{msg}</div>',
        unsafe_allow_html=True,
    )


def build_gauge(score: int) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=score,
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#262b3d", "tickfont": {"color": "#4a5168", "size": 9}, "tickwidth": 1, "nticks": 6},
            "bar":  {"color": "rgba(0,0,0,0)", "thickness": 0},
            "bgcolor": "#0e1018", "bordercolor": "#262b3d", "borderwidth": 1,
            "steps": [
                {"range": [0,  40],  "color": "rgba(248,113,113,0.18)"},
                {"range": [40, 65],  "color": "rgba(251,191,36,0.14)"},
                {"range": [65, 100], "color": "rgba(52,211,153,0.14)"},
            ],
            "threshold": {"line": {"color": "#5b7fff", "width": 3}, "thickness": 0.82, "value": score},
        },
    ))
    fig.add_annotation(x=0.5, y=0.22, text=f"<b>{score}</b>", font=dict(size=42, color="#e8eaf0", family="Syne"), showarrow=False, xref="paper", yref="paper")
    fig.add_annotation(x=0.5, y=0.08, text="/ 100",           font=dict(size=13, color="#4a5168", family="JetBrains Mono"), showarrow=False, xref="paper", yref="paper")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=240, margin=dict(t=20, b=0, l=20, r=20))
    return fig


def _classify_api_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "rate_limit" in msg or "429" in msg:
        return "API rate limit reached. Please wait 30 seconds and try again."
    if "authentication" in msg or "401" in msg:
        return "Authentication error. Please check your API key configuration."
    if "connection" in msg or "connrefused" in msg or "refused" in msg:
        return f"Cannot connect to backend at {BACKEND_URL}. Ensure the FastAPI server is running."
    if "timeout" in msg:
        return "Request timed out. The backend may be overloaded — please retry."
    return f"Request failed: {exc}"

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

# ── Topbar ────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="topbar">
        <div class="topbar-brand">
            <div class="brand-icon">✦</div>
            <span class="brand-name">Resume<span>IQ</span></span>
        </div>
        <span class="topbar-badge">ATS Intelligence Engine</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">AI-Powered · TF-IDF + NLP + FastAPI Backend</div>
        <h1 class="hero-title">Optimize your resume<br>for any job description</h1>
        <p class="hero-sub">
            Get an ATS compatibility score, keyword gap analysis, targeted improvement
            suggestions, and a fully AI-rewritten resume — in seconds.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# INPUT SECTION
# ══════════════════════════════════════════════════════════════════════════════

col_left, col_right = st.columns(2, gap="large")

# ── Resume upload card ────────────────────────────────────────────────────────
with col_left:
    st.markdown(
        """
        <div class="input-card">
            <div class="input-card-header">
                <div class="input-card-icon-wrap">📄</div>
                <div class="input-card-label-group">
                    <span class="input-card-title">Resume</span>
                    <span class="input-card-subtitle">PDF format · max 10 MB</span>
                </div>
                <div class="input-card-status"><span class="status-dot-idle"></span></div>
            </div>
            <div class="input-card-body">
                <div class="upload-zone">
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        label="resume_upload",
        label_visibility="collapsed",
        type=["pdf"],
        help="Upload your resume as a PDF. Text-based PDFs only.",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        size_kb = round(uploaded_file.size / 1024, 1)
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:0.6rem;
                 margin-top:0.75rem;padding:0.6rem 0.85rem;
                 background:var(--green-bg);border:1px solid var(--green-border);
                 border-radius:var(--radius-sm);">
                <span style="color:var(--green);font-size:0.85rem;">✓</span>
                <span style="font-family:var(--font-mono);font-size:0.72rem;color:var(--green);
                     flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                    {uploaded_file.name}
                </span>
                <span style="font-family:var(--font-mono);font-size:0.62rem;color:var(--text-muted);
                     flex-shrink:0;">{size_kb} KB</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.65rem;padding:0 0.1rem;">
                <span style="width:4px;height:4px;border-radius:50%;background:var(--text-muted);
                     opacity:0.5;flex-shrink:0;display:inline-block;"></span>
                <span style="font-size:0.72rem;color:var(--text-muted);">
                    Drag &amp; drop or click to browse — text-layer PDFs only
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)

# ── Job description card ──────────────────────────────────────────────────────
with col_right:
    st.markdown(
        """
        <div class="input-card">
            <div class="input-card-header">
                <div class="input-card-icon-wrap">🎯</div>
                <div class="input-card-label-group">
                    <span class="input-card-title">Job Description</span>
                    <span class="input-card-subtitle">Minimum 50 characters</span>
                </div>
                <div class="input-card-status"><span class="status-dot-idle"></span></div>
            </div>
            <div class="input-card-body">
                <div class="textarea-zone">
        """,
        unsafe_allow_html=True,
    )

    jd_text = st.text_area(
        label="jd_input",
        label_visibility="collapsed",
        placeholder=(
            "Paste the full job description here...\n\n"
            "Tip: Include the responsibilities, requirements, and preferred qualifications "
            "sections for the most accurate keyword analysis."
        ),
        height=195,
        key="jd_textarea",
    )

    jd_char_count = len(jd_text) if jd_text else 0
    jd_ok = jd_char_count >= 50
    jd_counter_color = (
        "var(--green)" if jd_ok else
        ("var(--amber)" if jd_char_count > 0 else "var(--text-muted)")
    )
    jd_counter_label = "Ready" if jd_ok else f"{max(0, 50 - jd_char_count)} more chars needed"

    st.markdown(
        f"""
                </div>
                <div class="textarea-footer">
                    <span class="textarea-footer-hint">Plain text · no formatting needed</span>
                    <span style="font-family:var(--font-mono);font-size:0.65rem;color:{jd_counter_color};">
                        {jd_char_count} chars · {jd_counter_label}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Analyze button ────────────────────────────────────────────────────────────

st.markdown('<div class="btn-row-wrapper">', unsafe_allow_html=True)
_, btn_col, _ = st.columns([1.8, 1.4, 1.8])
with btn_col:
    analyze_btn = st.button("Analyze Resume →", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if not analyze_btn:
    st.markdown(
        '<div class="btn-sublabel">Upload resume + paste JD to unlock analysis</div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS LOGIC  — calls FastAPI /analyze
# ══════════════════════════════════════════════════════════════════════════════

if analyze_btn:
    errors = []
    if not uploaded_file:
        errors.append("Please upload a PDF resume to continue.")
    if not jd_text or len(jd_text.strip()) < 50:
        errors.append("Please paste a job description (minimum 50 characters).")

    if errors:
        st.markdown("<br>", unsafe_allow_html=True)
        for e in errors:
            render_alert(e, "warn")
        st.stop()

    with st.spinner("Sending to backend for analysis..."):
        try:
            pdf_bytes = uploaded_file.read()
            raw_data  = call_analyze_api(pdf_bytes, uploaded_file.name, jd_text.strip())
            analysis  = parse_analysis(raw_data)
            st.session_state.analysis_result   = analysis
            st.session_state.resume_text_cache = analysis.get("resume_text", "")
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as exc:
            render_alert(_classify_api_error(exc), "error")
            logger.error("Connection error: %s", exc)
            st.stop()
        except (ValueError, RuntimeError) as exc:
            render_alert(str(exc), "error")
            logger.error("API error: %s", exc)
            st.stop()
        except Exception as exc:
            render_alert(f"Unexpected error: {exc}", "error")
            logger.exception("Unexpected error during /analyze")
            st.stop()

# Retrieve analysis from session (handles both fresh run and re-render)
analysis = st.session_state.get("analysis_result")

if analysis is not None:

    score           = _safe_int(analysis.get("ats_score"), 0)
    projected_score = min(100, score + 20)
    grade_label, grade_style, grade_text = grade_info(score)
    timestamp = datetime.datetime.now().strftime("%d %b %Y · %H:%M")

    # Invalidate optimizer state whenever a new analysis runs
    current_analysis_id = id(analysis)
    if st.session_state.opt_analysis_id != current_analysis_id:
        st.session_state.optimized_resume = None
        st.session_state.opt_timestamp    = None
        st.session_state.opt_error        = None
        st.session_state.is_generating    = False
        st.session_state.opt_analysis_id  = current_analysis_id

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="results-header">
            <span class="results-title">Analysis Results</span>
            <span class="results-timestamp">Generated {timestamp}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─────────────────────────────────────────────────────────────────────────
    # TABS
    # ─────────────────────────────────────────────────────────────────────────
    tab_overview, tab_keywords, tab_suggestions, tab_insights, tab_optimize = st.tabs([
        "  Overview  ", "  Keywords  ", "  Suggestions  ", "  Advanced Insights  ", "  🚀 Optimize Resume  ",
    ])

    # ════════════════════════════
    # TAB 1 · Overview
    # ════════════════════════════
    with tab_overview:
        ov_left, ov_right = st.columns([1, 1.7], gap="large")
        with ov_left:
            st.markdown(
                f"""
                <div class="score-card">
                    <div class="score-ring-label">ATS Compatibility Score</div>
                    <div style="display:flex;align-items:baseline;justify-content:center;gap:0.1rem;margin-top:0.3rem;">
                        <span class="score-number">{score}</span>
                        <span class="score-denom">/ 100</span>
                    </div>
                    <span class="score-grade-badge" style="{grade_style}">{grade_label}</span>
                    <p style="font-size:0.78rem;color:var(--text-muted);margin-top:0.85rem;line-height:1.55;">{grade_text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(build_gauge(score), use_container_width=True, config={"displayModeBar": False})
        with ov_right:
            render_progress("Semantic Similarity", _safe_int(analysis.get("semantic_score"), 0))
            render_progress("Keyword Match Rate",  _safe_int(analysis.get("keyword_score"),  0))
            st.markdown("<br>", unsafe_allow_html=True)
            matched_kw = _safe_list(analysis.get("matched_keywords"))
            missing_kw = _safe_list(analysis.get("missing_keywords"))
            jd_top_kw  = _safe_list(analysis.get("jd_top_keywords"))
            suggestions = _safe_list(analysis.get("suggestions"))
            st.markdown(
                f"""
                <div class="metric-grid">
                    <div class="metric-card"><div class="metric-value">{len(matched_kw)}</div><div class="metric-label">Matched Keywords</div></div>
                    <div class="metric-card"><div class="metric-value">{len(missing_kw)}</div><div class="metric-label">Missing Keywords</div></div>
                    <div class="metric-card"><div class="metric-value">{len(jd_top_kw)}</div><div class="metric-label">JD Top Terms</div></div>
                    <div class="metric-card"><div class="metric-value">{len(suggestions)}</div><div class="metric-label">Suggestions</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ════════════════════════════
    # TAB 2 · Keywords
    # ════════════════════════════
    with tab_keywords:
        matched_kw  = _safe_list(analysis.get("matched_keywords"))
        missing_kw  = _safe_list(analysis.get("missing_keywords"))
        jd_top_kw   = _safe_list(analysis.get("jd_top_keywords"))

        kw_col1, kw_col2 = st.columns(2, gap="large")
        with kw_col1:
            mc = len(matched_kw)
            st.markdown(f'<div class="panel"><div class="panel-title">✓ Matched Keywords<span class="pill-count pill-count-green">{mc}</span></div>', unsafe_allow_html=True)
            if matched_kw:
                pills = "".join(f'<span class="pill pill-matched">{kw}</span>' for kw in matched_kw[:30])
                st.markdown(f'<div class="pills-container">{pills}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:var(--text-muted);font-size:0.82rem;">No keyword matches found.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with kw_col2:
            xc = len(missing_kw)
            st.markdown(f'<div class="panel"><div class="panel-title">✕ Missing Keywords<span class="pill-count pill-count-red">{xc}</span></div>', unsafe_allow_html=True)
            if missing_kw:
                pills = "".join(f'<span class="pill pill-missing">{kw}</span>' for kw in missing_kw)
                st.markdown(f'<div class="pills-container">{pills}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:var(--text-muted);font-size:0.82rem;">No critical missing keywords detected.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel" style="margin-top:0.5rem;"><div class="panel-title">◈ Top Keywords from Job Description</div>', unsafe_allow_html=True)
        if jd_top_kw:
            jd_pills = "".join(f'<span class="pill pill-neutral">{kw}</span>' for kw in jd_top_kw)
            st.markdown(f'<div class="pills-container" style="max-height:none;">{jd_pills}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:var(--text-muted);font-size:0.82rem;">No top keywords extracted.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════
    # TAB 3 · Suggestions
    # ════════════════════════════
    with tab_suggestions:
        suggestions = _safe_list(analysis.get("suggestions"))
        st.markdown(
            '<p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:1.25rem;">'
            'AI-generated recommendations to improve your ATS score and alignment with this role.</p>',
            unsafe_allow_html=True,
        )
        if suggestions:
            for i, s in enumerate(suggestions, 1):
                st.markdown(
                    f'<div class="suggestion-item"><span class="suggestion-index">{i:02d}</span><span>{s}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<p style="color:var(--text-muted);font-size:0.85rem;">No specific suggestions — your resume appears well-aligned.</p>',
                unsafe_allow_html=True,
            )

    # ════════════════════════════
    # TAB 4 · Advanced Insights
    # ════════════════════════════
    with tab_insights:
        matched_kw  = _safe_list(analysis.get("matched_keywords"))
        missing_kw  = _safe_list(analysis.get("missing_keywords"))
        sem_score   = _safe_int(analysis.get("semantic_score"), 0)
        kw_score    = _safe_int(analysis.get("keyword_score"),  0)

        ins_l, ins_r = st.columns(2, gap="large")
        with ins_l:
            bar_cats   = ["Semantic", "Keywords", "Overall ATS"]
            bar_vals   = [sem_score, kw_score, score]
            bar_colors = ["#5b7fff", "#a78bfa", "#34d399"]
            fig2 = go.Figure()
            for cat, val, col in zip(bar_cats, bar_vals, bar_colors):
                fig2.add_trace(go.Bar(
                    x=[val], y=[cat], orientation="h",
                    marker=dict(color=col, line=dict(width=0)),
                    text=[f"{val}%"], textposition="inside", insidetextanchor="middle",
                    textfont=dict(size=11, color="#e8eaf0", family="JetBrains Mono"),
                    showlegend=False,
                ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=160,
                xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, tickfont=dict(color="#4a5168", size=9)),
                yaxis=dict(showgrid=False, tickfont=dict(color="#8b92a8", size=11)),
                margin=dict(t=10, b=10, l=0, r=10), bargap=0.45,
            )
            st.markdown('<div class="panel"><div class="panel-title">◈ Score Breakdown</div>', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with ins_r:
            matched_n = len(matched_kw)
            missing_n = len(missing_kw)
            total_n   = max(matched_n + missing_n, 1)
            fig3 = go.Figure(go.Pie(
                values=[max(matched_n, 0), max(missing_n, 0)],
                labels=["Matched", "Missing"], hole=0.68,
                marker=dict(colors=["#34d399", "#f87171"], line=dict(color="#07080d", width=2)),
                textinfo="none", hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            ))
            fig3.add_annotation(text=f"<b>{matched_n}/{total_n}</b>", x=0.5, y=0.55, font=dict(size=20, color="#e8eaf0", family="Syne"), showarrow=False)
            fig3.add_annotation(text="keywords",               x=0.5, y=0.38, font=dict(size=10, color="#4a5168", family="JetBrains Mono"), showarrow=False)
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=200,
                margin=dict(t=10, b=10, l=0, r=0),
                legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.08, font=dict(size=10, color="#8b92a8"), bgcolor="rgba(0,0,0,0)"),
                showlegend=True,
            )
            st.markdown('<div class="panel"><div class="panel-title">◈ Keyword Coverage</div>', unsafe_allow_html=True)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        def pct_to_status(pct: int) -> tuple:
            if pct >= 70:
                return "Strong",    "background:var(--green-bg);color:var(--green);border:1px solid var(--green-border);"
            if pct >= 45:
                return "Moderate",  "background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-border);"
            return "Needs Work",    "background:var(--red-bg);color:var(--red);border:1px solid var(--red-border);"

        sem_lbl, sem_sty = pct_to_status(sem_score)
        kw_lbl,  kw_sty  = pct_to_status(kw_score)
        ats_lbl, ats_sty = pct_to_status(score)
        cov_pct = int(100 * matched_n / total_n) if total_n else 0
        cov_lbl, cov_sty = pct_to_status(cov_pct)
        n_suggestions = len(_safe_list(analysis.get("suggestions")))

        st.markdown(
            f"""
            <div class="panel" style="margin-top:0.25rem;">
                <div class="panel-title">◈ Alignment Indicators</div>
                <div class="insight-row"><span class="insight-label">Overall ATS Readiness</span><span class="insight-badge" style="{ats_sty}">{ats_lbl}</span></div>
                <div class="insight-row"><span class="insight-label">Semantic Alignment</span><span class="insight-badge" style="{sem_sty}">{sem_lbl}</span></div>
                <div class="insight-row"><span class="insight-label">Keyword Match Rate</span><span class="insight-badge" style="{kw_sty}">{kw_lbl}</span></div>
                <div class="insight-row"><span class="insight-label">Keyword Coverage Ratio</span><span class="insight-badge" style="{cov_sty}">{cov_lbl} · {cov_pct}%</span></div>
                <div class="insight-row"><span class="insight-label">Improvement Suggestions</span><span class="insight-badge" style="background:var(--accent-subtle);color:var(--accent);border:1px solid rgba(91,127,255,0.2);">{n_suggestions} action items</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ════════════════════════════
    # TAB 5 · 🚀 Optimize Resume
    # ════════════════════════════
    with tab_optimize:

        # ── Hero banner ───────────────────────────────────────────────────────
        st.markdown(
            """
            <div class="optimizer-hero">
                <div class="optimizer-hero-title">AI Resume Optimizer</div>
                <div class="optimizer-hero-sub">
                    The backend AI model rewrites your resume from scratch — tailored to this specific job description.
                    Keywords are integrated naturally, bullet points are strengthened with action verbs,
                    and achievements are quantified for maximum recruiter and ATS impact.
                </div>
                <div class="optimizer-feature-list">
                    <span class="optimizer-feature-pill">✦ Keyword Integration</span>
                    <span class="optimizer-feature-pill">✦ Action Verbs</span>
                    <span class="optimizer-feature-pill">✦ Quantified Achievements</span>
                    <span class="optimizer-feature-pill">✦ ATS-Optimized Structure</span>
                    <span class="optimizer-feature-pill">✦ Professional Summary</span>
                    <span class="optimizer-feature-pill">✦ Skills Alignment</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Score projection metrics ──────────────────────────────────────────
        m1, m2, m3 = st.columns(3, gap="medium")
        with m1:
            st.metric("Current ATS Score", f"{score}/100")
        with m2:
            st.metric(
                "Projected After Optimization",
                f"{projected_score}/100",
                delta=f"+{projected_score - score} pts estimated",
            )
        with m3:
            st.metric(
                "Missing Keywords to Fill",
                str(len(_safe_list(analysis.get("missing_keywords")))),
                delta="→ 0 after optimization",
                delta_color="inverse",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── STEP 1 — BUTTON ──────────────────────────────────────────────────
        has_result    = bool(st.session_state.optimized_resume)
        is_generating = st.session_state.is_generating
        btn_label     = "↻ Regenerate Resume" if has_result else "✦ Generate Optimized Resume"

        _, gen_col, _ = st.columns([2, 1.5, 2])
        with gen_col:
            generate_btn = st.button(
                btn_label,
                use_container_width=True,
                key="generate_optimized",
                disabled=is_generating,
            )

        # Button click: validate inputs then arm the execution block
        if generate_btn and not st.session_state.is_generating:
            resume_text_for_opt = st.session_state.get("resume_text_cache", "")
            jd_text_for_opt     = jd_text.strip() if jd_text else ""

            if not resume_text_for_opt or not resume_text_for_opt.strip():
                st.session_state.opt_error        = "Resume text could not be extracted from the backend response. Please re-analyze."
                st.session_state.optimized_resume = None
                st.session_state.opt_timestamp    = None
            elif not jd_text_for_opt or len(jd_text_for_opt) < 50:
                st.session_state.opt_error        = "Job description is too short. Please paste the full description."
                st.session_state.optimized_resume = None
                st.session_state.opt_timestamp    = None
            else:
                st.session_state.optimized_resume = None
                st.session_state.opt_timestamp    = None
                st.session_state.opt_error        = None
                st.session_state.is_generating    = True

        # ── STEP 2 — EXECUTION BLOCK ─────────────────────────────────────────
        if st.session_state.is_generating:
            resume_text_for_opt = st.session_state.get("resume_text_cache", "")
            jd_text_for_opt     = jd_text.strip() if jd_text else ""

            with st.spinner("Optimizing resume via backend API — this may take 10–30 seconds..."):
                try:
                    opt_data = call_optimize_api(resume_text_for_opt, jd_text_for_opt)

                    # Support both {"optimized_resume": "..."} and {"optimized_text": "..."}
                    result = (
                        opt_data.get("optimized_resume")
                        or opt_data.get("optimized_text")
                        or opt_data.get("result")
                        or opt_data.get("text")
                        or ""
                    )
                    logger.debug("Optimize result length: %d", len(result))

                    if result and result.strip():
                        st.session_state.optimized_resume = result
                        st.session_state.opt_timestamp    = datetime.datetime.now().strftime("%d %b %Y · %H:%M:%S")
                        st.session_state.opt_error        = None
                    else:
                        st.session_state.opt_error        = "The backend returned an empty optimization result. Please try again."
                        st.session_state.optimized_resume = None

                except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as exc:
                    st.session_state.opt_error        = _classify_api_error(exc)
                    st.session_state.optimized_resume = None
                    logger.error("Connection error during /optimize: %s", exc)
                except (ValueError, RuntimeError) as exc:
                    st.session_state.opt_error        = str(exc)
                    st.session_state.optimized_resume = None
                    logger.error("API error during /optimize: %s", exc)
                except Exception as exc:
                    st.session_state.opt_error        = f"Optimization failed unexpectedly: {exc}"
                    st.session_state.optimized_resume = None
                    logger.exception("Unexpected error during /optimize")
                finally:
                    st.session_state.is_generating = False

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Error display ─────────────────────────────────────────────────────
        if st.session_state.opt_error:
            render_alert(st.session_state.opt_error, "error")
            if st.button("✕ Dismiss", key="dismiss_opt_error"):
                st.session_state.opt_error = None

        # ── Result display ────────────────────────────────────────────────────
        elif st.session_state.optimized_resume:
            optimized_text = st.session_state.optimized_resume
            opt_ts         = st.session_state.opt_timestamp or ""
            word_count     = len(optimized_text.split())
            line_count     = optimized_text.count("\n")

            # Success banner
            st.markdown(
                f"""
                <div style="background:var(--green-bg);border:1px solid var(--green-border);
                     border-radius:var(--radius-md);padding:0.85rem 1.1rem;
                     display:flex;align-items:center;justify-content:space-between;
                     gap:1rem;flex-wrap:wrap;margin-bottom:1.25rem;">
                    <div style="display:flex;align-items:center;gap:0.65rem;">
                        <span style="color:var(--green);font-size:1rem;flex-shrink:0;">✓</span>
                        <span style="color:var(--green);font-size:0.85rem;font-weight:500;">Resume optimized successfully</span>
                        <span style="font-family:var(--font-mono);font-size:0.65rem;color:var(--green);opacity:0.7;">
                            {word_count} words · {line_count} lines
                        </span>
                    </div>
                    <span style="font-family:var(--font-mono);font-size:0.6rem;color:var(--text-muted);">Generated {opt_ts}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Output card header
            st.markdown(
                """
                <div style="background:var(--bg-elevated);border:1px solid var(--border);
                     border-radius:var(--radius-lg) var(--radius-lg) 0 0;
                     padding:0.85rem 1.25rem;
                     display:flex;align-items:center;justify-content:space-between;
                     border-bottom:1px solid var(--border-light);">
                    <span style="font-family:var(--font-display);font-weight:600;font-size:0.88rem;
                         color:var(--text-primary);display:flex;align-items:center;gap:0.55rem;">
                        ✦ Optimized Resume Output
                        <span style="font-family:var(--font-mono);font-size:0.58rem;padding:0.15rem 0.55rem;
                             border-radius:99px;background:var(--green-bg);color:var(--green);
                             border:1px solid var(--green-border);letter-spacing:0.08em;text-transform:uppercase;">
                            AI-Generated
                        </span>
                    </span>
                    <span style="font-family:var(--font-mono);font-size:0.6rem;color:var(--text-muted);">Backend AI Model</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Scrollable resume body
            safe_text = (
                optimized_text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            st.markdown(
                f"""
                <div style="background:var(--bg-base);border-left:1px solid var(--border);
                     border-right:1px solid var(--border);padding:1.5rem 1.75rem;
                     max-height:520px;overflow-y:auto;
                     box-shadow:inset 0 -24px 24px -12px rgba(7,8,13,0.6);">
                    <pre style="font-family:var(--font-mono);font-size:0.78rem;line-height:1.75;
                         color:var(--text-secondary);white-space:pre-wrap;
                         word-break:break-word;margin:0;padding:0;">{safe_text}</pre>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Card footer
            st.markdown(
                """
                <div style="background:var(--bg-elevated);border:1px solid var(--border);
                     border-top:1px solid var(--border-light);
                     border-radius:0 0 var(--radius-lg) var(--radius-lg);
                     padding:0.75rem 1.25rem;
                     display:flex;align-items:center;gap:0.5rem;">
                    <span style="font-family:var(--font-mono);font-size:0.6rem;color:var(--text-muted);
                         margin-right:auto;letter-spacing:0.08em;">EXPORT OPTIONS</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            dl1, dl2, dl3, _ = st.columns([1, 1, 1, 2])
            ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")

            with dl1:
                st.download_button(
                    label="↓ .txt",
                    data=optimized_text,
                    file_name=f"optimized_resume_{ts_str}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_opt_txt",
                )
            with dl2:
                bundle = {
                    "generated_at":               opt_ts,
                    "original_ats_score":          score,
                    "projected_ats_score":         projected_score,
                    "optimized_resume":            optimized_text,
                    "missing_keywords_addressed":  _safe_list(analysis.get("missing_keywords")),
                }
                st.download_button(
                    label="↓ .json",
                    data=json.dumps(bundle, indent=2),
                    file_name=f"optimized_resume_{ts_str}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_opt_json",
                )
            with dl3:
                md_content = f"# Optimized Resume\n_Generated {opt_ts} by ResumeIQ_\n\n---\n\n{optimized_text}"
                st.download_button(
                    label="↓ .md",
                    data=md_content,
                    file_name=f"optimized_resume_{ts_str}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="dl_opt_md",
                )

        # ── Idle / empty state ────────────────────────────────────────────────
        else:
            st.markdown(
                f"""
                <div style="background:var(--bg-surface);border:1px dashed var(--border);
                     border-radius:var(--radius-lg);padding:3.5rem 2rem;
                     text-align:center;margin-top:0.5rem;">
                    <span style="font-size:2rem;display:block;margin-bottom:1rem;opacity:0.2;">✦</span>
                    <div style="font-family:var(--font-display);font-weight:600;font-size:0.95rem;
                         color:var(--text-muted);margin-bottom:0.5rem;">
                        Your optimized resume will appear here
                    </div>
                    <p style="font-size:0.78rem;color:var(--text-muted);opacity:0.65;
                         max-width:380px;margin:0 auto;line-height:1.65;">
                        Click <strong style="color:var(--accent);">✦ Generate Optimized Resume</strong> above.
                        The AI will rewrite your resume for this role in 10–30 seconds.
                    </p>
                    <div style="margin-top:1.75rem;display:flex;align-items:center;
                         justify-content:center;gap:1.25rem;flex-wrap:wrap;">
                        <span style="font-family:var(--font-mono);font-size:0.6rem;color:var(--text-muted);
                             background:var(--bg-elevated);border:1px solid var(--border);
                             border-radius:99px;padding:0.3rem 0.85rem;">Current score: {score}/100</span>
                        <span style="font-family:var(--font-mono);font-size:0.6rem;color:var(--green);
                             background:var(--green-bg);border:1px solid var(--green-border);
                             border-radius:99px;padding:0.3rem 0.85rem;">Target after optimization: ~{projected_score}/100</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Export bar ────────────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    report_data = {
        "generated_at":       timestamp,
        "ats_score":          score,
        "grade":              grade_label,
        "semantic_score":     _safe_int(analysis.get("semantic_score"), 0),
        "keyword_score":      _safe_int(analysis.get("keyword_score"),  0),
        "matched_keywords":   _safe_list(analysis.get("matched_keywords")),
        "missing_keywords":   _safe_list(analysis.get("missing_keywords")),
        "jd_top_keywords":    _safe_list(analysis.get("jd_top_keywords")),
        "suggestions":        _safe_list(analysis.get("suggestions")),
    }
    json_str = json.dumps(report_data, indent=2)

    st.markdown(
        """
        <div class="export-bar">
            <div class="export-bar-left">
                <div class="export-icon">↓</div>
                <div>
                    <div class="export-text-title">Export Analysis Report</div>
                    <div class="export-text-sub">Download your full analysis results for sharing or reference</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    exp_col1, exp_col2, _ = st.columns([1, 1, 4])
    ts_report = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    with exp_col1:
        st.download_button(
            label="↓ Download JSON",
            data=json_str,
            file_name=f"resumeiq_report_{ts_report}.json",
            mime="application/json",
            use_container_width=True,
        )
    with exp_col2:
        txt_lines = [
            "ResumeIQ — Analysis Report",
            f"Generated: {timestamp}",
            "=" * 40,
            f"ATS Score:         {score}/100 ({grade_label})",
            f"Semantic Score:    {_safe_int(analysis.get('semantic_score'), 0)}%",
            f"Keyword Score:     {_safe_int(analysis.get('keyword_score'),  0)}%",
            "",
            "MATCHED KEYWORDS",
            ", ".join(_safe_list(analysis.get("matched_keywords"))),
            "",
            "MISSING KEYWORDS",
            ", ".join(_safe_list(analysis.get("missing_keywords"))),
            "",
            "SUGGESTIONS",
            *[f"{i}. {s}" for i, s in enumerate(_safe_list(analysis.get("suggestions")), 1)],
        ]
        st.download_button(
            label="↓ Download TXT",
            data="\n".join(txt_lines),
            file_name=f"resumeiq_report_{ts_report}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ── Empty / pre-analysis state ────────────────────────────────────────────────

if not analyze_btn and analysis is None:
    st.markdown(
        """
        <div class="empty-state">
            <span class="empty-icon">◈</span>
            <div class="empty-title">Your analysis will appear here</div>
            <p class="empty-sub">
                Upload a PDF resume and paste a job description above, then click
                <strong style="color:var(--accent)">Analyze Resume</strong> to get your ATS score,
                keyword gaps, improvement roadmap, and an AI-optimized resume.
            </p>
            <div class="empty-steps">
                <div class="empty-step"><span class="empty-step-num">01</span>Upload PDF resume</div>
                <span class="empty-arrow">→</span>
                <div class="empty-step"><span class="empty-step-num">02</span>Paste job description</div>
                <span class="empty-arrow">→</span>
                <div class="empty-step"><span class="empty-step-num">03</span>Click Analyze</div>
                <span class="empty-arrow">→</span>
                <div class="empty-step"><span class="empty-step-num">04</span>Optimize with AI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
