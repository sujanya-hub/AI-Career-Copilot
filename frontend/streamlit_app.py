"""
Career Copilot — Production-grade AI Resume Intelligence Platform v2.2
Upgrades: Improvement Tracking · Interactive Keywords · Advanced Recruiter Engine
NEW v2.2: Live Resume Improvement Loop
"""

import os
import json
import datetime
import logging
import time

import streamlit as st
import plotly.graph_objects as go
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("career_copilot")

st.set_page_config(
    page_title="Career Copilot · AI Resume Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,400&display=swap');

    :root {
        --bg:          #080b12;
        --bg-1:        #0d1117;
        --bg-2:        #131922;
        --bg-3:        #192030;
        --border:      rgba(255,255,255,0.07);
        --border-md:   rgba(255,255,255,0.12);
        --border-hi:   rgba(255,255,255,0.18);
        --blue:        #4f8aff;
        --blue-dim:    rgba(79,138,255,0.12);
        --blue-glow:   rgba(79,138,255,0.25);
        --cyan:        #22d3ee;
        --cyan-dim:    rgba(34,211,238,0.1);
        --green:       #10b981;
        --green-dim:   rgba(16,185,129,0.1);
        --green-glow:  rgba(16,185,129,0.2);
        --amber:       #f59e0b;
        --amber-dim:   rgba(245,158,11,0.1);
        --red:         #ef4444;
        --red-dim:     rgba(239,68,68,0.1);
        --purple:      #8b5cf6;
        --purple-dim:  rgba(139,92,246,0.1);
        --txt:         #e2e8f0;
        --txt-2:       #94a3b8;
        --txt-3:       #475569;
        --r-sm:  6px; --r-md:  12px; --r-lg:  18px; --r-xl:  24px;
        --ff-body:    'DM Sans', sans-serif;
        --ff-mono:    'DM Mono', monospace;
        --ff-display: 'Fraunces', serif;
        --shadow-sm:  0 1px 3px rgba(0,0,0,0.4);
        --shadow-md:  0 4px 16px rgba(0,0,0,0.5);
        --shadow-lg:  0 8px 32px rgba(0,0,0,0.6);
        --shadow-blue: 0 0 32px rgba(79,138,255,0.15);
    }
    *, *::before, *::after { box-sizing: border-box; }
    html, body, [class*="css"] {
        font-family: var(--ff-body) !important;
        background: var(--bg) !important;
        color: var(--txt);
        -webkit-font-smoothing: antialiased;
    }
    .stApp { background: var(--bg) !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0 !important; padding-bottom: 4rem !important; max-width: 1380px !important; }
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--bg-3); border-radius: 99px; }

    /* ── TOPBAR ── */
    .copilot-topbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 1.1rem 2.5rem;
        background: rgba(8,11,18,0.85);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border);
        position: sticky; top: 0; z-index: 100;
    }
    .copilot-brand { display: flex; align-items: center; gap: 0.75rem; }
    .copilot-logo {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #4f8aff 0%, #22d3ee 100%);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
        box-shadow: 0 0 20px rgba(79,138,255,0.4);
    }
    .copilot-wordmark { font-family: var(--ff-display); font-size: 1.2rem; font-weight: 700; color: var(--txt); letter-spacing: -0.02em; }
    .copilot-wordmark em { font-style: normal; color: var(--blue); }
    .copilot-status {
        display: flex; align-items: center; gap: 0.5rem;
        font-family: var(--ff-mono); font-size: 0.65rem; color: var(--txt-3);
        letter-spacing: 0.1em; text-transform: uppercase;
        background: var(--bg-2); border: 1px solid var(--border);
        border-radius: 99px; padding: 0.35rem 1rem;
    }
    .dot-live { width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); animation: pulse-dot 2s ease infinite; }
    @keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

    /* ── HERO ── */
    .hero-section { padding: 3.5rem 2.5rem 2.5rem; position: relative; overflow: hidden; }
    .hero-section::before {
        content: ''; position: absolute; top: -120px; left: 50%; transform: translateX(-50%);
        width: 800px; height: 400px;
        background: radial-gradient(ellipse, rgba(79,138,255,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-label {
        display: inline-flex; align-items: center; gap: 0.5rem;
        font-family: var(--ff-mono); font-size: 0.63rem; letter-spacing: 0.18em; text-transform: uppercase;
        color: var(--blue); background: var(--blue-dim); border: 1px solid rgba(79,138,255,0.2);
        border-radius: 99px; padding: 0.3rem 0.85rem; margin-bottom: 1.25rem;
    }
    .hero-title { font-family: var(--ff-display); font-size: 3.5rem; font-weight: 700; line-height: 1.05; letter-spacing: -0.03em; color: var(--txt); margin: 0 0 1rem; }
    .hero-title span { background: linear-gradient(135deg, #4f8aff 0%, #22d3ee 60%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .hero-sub { font-size: 1.05rem; color: var(--txt-2); max-width: 580px; line-height: 1.7; font-weight: 400; }
    .hero-stats { display: flex; gap: 2.5rem; margin-top: 2rem; }
    .hero-stat-val { font-family: var(--ff-display); font-size: 1.5rem; font-weight: 700; color: var(--txt); }
    .hero-stat-lbl { font-size: 0.75rem; color: var(--txt-3); margin-top: 0.15rem; }

    /* ── INPUT PANEL ── */
    .input-panel { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-xl); overflow: hidden; transition: border-color 0.3s, box-shadow 0.3s; position: relative; }
    .input-panel:hover { border-color: var(--border-md); box-shadow: var(--shadow-md); }
    .input-panel-top { display: flex; align-items: center; gap: 0.6rem; padding: 0.9rem 1.25rem; background: var(--bg-2); border-bottom: 1px solid var(--border); }
    .panel-icon { width: 28px; height: 28px; background: var(--blue-dim); border: 1px solid rgba(79,138,255,0.18); border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }
    .panel-label { font-weight: 600; font-size: 0.85rem; color: var(--txt); }
    .panel-sublabel { font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--txt-3); }
    .panel-body { padding: 1rem 1.25rem 1.25rem; }

    /* ── FILE UPLOADER ── */
    [data-testid="stFileUploader"] { background: transparent !important; border: none !important; padding: 0 !important; }
    [data-testid="stFileUploaderDropzone"] { background: var(--bg) !important; border: 1.5px dashed var(--border-md) !important; border-radius: var(--r-md) !important; padding: 1.5rem 1rem !important; min-height: 90px !important; transition: border-color 0.2s, background 0.2s !important; }
    [data-testid="stFileUploaderDropzone"]:hover { background: var(--blue-dim) !important; border-color: var(--blue) !important; }
    [data-testid="stFileDropzoneInstructions"] > div > span { font-family: var(--ff-body) !important; font-size: 0.8rem !important; color: var(--txt-3) !important; }
    [data-testid="stFileDropzoneInstructions"] > div > small { font-family: var(--ff-mono) !important; font-size: 0.62rem !important; color: var(--txt-3) !important; }
    [data-testid="stFileUploaderDropzone"] button { background: var(--bg-2) !important; color: var(--blue) !important; border: 1px solid rgba(79,138,255,0.25) !important; border-radius: var(--r-sm) !important; font-family: var(--ff-mono) !important; font-size: 0.68rem !important; padding: 0.3rem 0.85rem !important; box-shadow: none !important; transform: none !important; width: auto !important; }
    [data-testid="stFileUploaderDropzone"] button:hover { background: var(--blue-dim) !important; border-color: var(--blue) !important; transform: none !important; box-shadow: none !important; }
    [data-testid="stFileUploaderFile"] { background: var(--green-dim) !important; border: 1px solid var(--green-glow) !important; border-radius: var(--r-sm) !important; padding: 0.4rem 0.75rem !important; margin-top: 0.5rem !important; }
    [data-testid="stFileUploaderFileName"] { font-family: var(--ff-mono) !important; font-size: 0.72rem !important; color: var(--green) !important; }
    [data-testid="stFileUploaderFileData"] { font-family: var(--ff-mono) !important; font-size: 0.62rem !important; color: var(--txt-3) !important; }
    [data-testid="stFileUploaderDeleteBtn"] button { background: transparent !important; border: none !important; color: var(--txt-3) !important; box-shadow: none !important; transform: none !important; width: auto !important; padding: 0 !important; }
    [data-testid="stFileUploaderDeleteBtn"] button:hover { color: var(--red) !important; background: transparent !important; }

    /* ── TEXTAREA ── */
    .stTextArea label { display: none !important; }
    [data-testid="InputInstructions"] { display: none !important; }
    .stTextArea textarea { background: var(--bg) !important; border: 1.5px solid var(--border-md) !important; border-radius: var(--r-md) !important; color: var(--txt) !important; font-family: var(--ff-body) !important; font-size: 0.875rem !important; line-height: 1.7 !important; resize: none !important; padding: 1rem !important; transition: border-color 0.2s, box-shadow 0.2s !important; }
    .stTextArea textarea:focus { border-color: var(--blue) !important; box-shadow: 0 0 0 3px var(--blue-glow) !important; outline: none !important; }
    .stTextArea textarea::placeholder { color: var(--txt-3) !important; font-size: 0.82rem !important; }

    /* ── LIVE EDITOR textarea special ── */
    .live-editor-area textarea {
        background: var(--bg) !important;
        border: 1.5px solid rgba(79,138,255,0.2) !important;
        border-radius: var(--r-md) !important;
        color: var(--txt) !important;
        font-family: var(--ff-mono) !important;
        font-size: 0.78rem !important;
        line-height: 1.8 !important;
        padding: 1rem !important;
    }
    .live-editor-area textarea:focus {
        border-color: var(--blue) !important;
        box-shadow: 0 0 0 3px var(--blue-glow) !important;
    }

    /* ── BUTTONS ── */
    .stButton > button { background: linear-gradient(135deg, #4f8aff 0%, #22d3ee 100%) !important; color: #fff !important; border: none !important; border-radius: var(--r-md) !important; font-family: var(--ff-body) !important; font-size: 0.9rem !important; font-weight: 600 !important; padding: 0.8rem 2rem !important; cursor: pointer !important; transition: all 0.2s !important; box-shadow: 0 4px 20px rgba(79,138,255,0.35) !important; width: 100% !important; }
    .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 30px rgba(79,138,255,0.5) !important; }
    .stButton > button:disabled { background: var(--bg-2) !important; color: var(--txt-3) !important; box-shadow: none !important; transform: none !important; border: 1px solid var(--border) !important; }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] { background: var(--bg-1) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; padding: 0.3rem !important; gap: 0.1rem !important; margin-bottom: 1.75rem !important; }
    .stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--txt-3) !important; border-radius: var(--r-sm) !important; font-family: var(--ff-body) !important; font-size: 0.82rem !important; font-weight: 500 !important; padding: 0.5rem 1rem !important; border: none !important; transition: all 0.15s !important; }
    .stTabs [data-baseweb="tab"]:hover { color: var(--txt) !important; }
    .stTabs [aria-selected="true"] { background: var(--bg-3) !important; color: var(--txt) !important; box-shadow: var(--shadow-sm) !important; }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* ── CARDS ── */
    .card { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 1.5rem; position: relative; transition: border-color 0.25s, box-shadow 0.25s; }
    .card:hover { border-color: var(--border-md); }
    .card-accent-blue::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #4f8aff, #22d3ee); border-radius: var(--r-lg) var(--r-lg) 0 0; }
    .card-accent-green::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #10b981, #22d3ee); border-radius: var(--r-lg) var(--r-lg) 0 0; }
    .card-accent-purple::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #8b5cf6, #4f8aff); border-radius: var(--r-lg) var(--r-lg) 0 0; }
    .card-accent-amber::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #f59e0b, #fb923c); border-radius: var(--r-lg) var(--r-lg) 0 0; }
    .card-title { font-weight: 600; font-size: 0.88rem; color: var(--txt); display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.25rem; padding-bottom: 0.85rem; border-bottom: 1px solid var(--border); }

    /* ── SCORE DISPLAY ── */
    .score-hero { text-align: center; padding: 2rem 1.5rem; background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-xl); position: relative; overflow: hidden; }
    .score-hero::after { content: ''; position: absolute; bottom: -50px; left: 50%; transform: translateX(-50%); width: 200px; height: 100px; background: radial-gradient(ellipse, rgba(79,138,255,0.12), transparent 70%); pointer-events: none; }
    .score-num { font-family: var(--ff-display); font-size: 5.5rem; font-weight: 700; line-height: 1; letter-spacing: -0.04em; background: linear-gradient(135deg, #4f8aff, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .score-denom { font-family: var(--ff-mono); font-size: 1rem; color: var(--txt-3); }
    .score-tag { display: inline-block; margin-top: 0.75rem; padding: 0.3rem 1rem; border-radius: 99px; font-size: 0.8rem; font-weight: 500; }

    /* ── IMPROVEMENT TRACKER ── */
    .improvement-banner {
        background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-lg);
        padding: 1.1rem 1.5rem;
        display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;
        margin-bottom: 1.5rem; position: relative; overflow: hidden;
    }
    .improvement-banner::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: var(--r-lg) var(--r-lg) 0 0; }
    .improvement-banner.improved::before { background: linear-gradient(90deg, #10b981, #22d3ee); }
    .improvement-banner.declined::before { background: linear-gradient(90deg, #ef4444, #f87171); }
    .improvement-banner.same::before { background: linear-gradient(90deg, #f59e0b, #fb923c); }
    .score-compare { display: flex; align-items: center; gap: 1.5rem; }
    .score-compare-item { text-align: center; }
    .score-compare-val { font-family: var(--ff-display); font-size: 2.2rem; font-weight: 700; line-height: 1; }
    .score-compare-lbl { font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--txt-3); margin-top: 0.25rem; }
    .score-compare-arrow { font-size: 1.5rem; color: var(--txt-3); opacity: 0.4; }
    .delta-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.5rem 1.1rem; border-radius: 99px; font-family: var(--ff-display); font-size: 1.4rem; font-weight: 700; }
    .delta-up { background: var(--green-dim); color: var(--green); border: 1.5px solid var(--green-glow); }
    .delta-down { background: var(--red-dim); color: var(--red); border: 1.5px solid rgba(239,68,68,0.3); }
    .delta-same { background: var(--amber-dim); color: var(--amber); border: 1.5px solid rgba(245,158,11,0.2); }
    .delta-msg { font-size: 0.82rem; color: var(--txt-2); line-height: 1.5; max-width: 340px; }
    .delta-msg strong { color: var(--txt); }

    /* ── PROGRESS ── */
    .prog-row { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1.25rem; margin-bottom: 0.65rem; }
    .prog-header { display: flex; justify-content: space-between; margin-bottom: 0.6rem; }
    .prog-name { font-size: 0.82rem; font-weight: 500; color: var(--txt-2); }
    .prog-pct { font-family: var(--ff-mono); font-size: 0.78rem; color: var(--txt); }
    .prog-track { background: var(--bg-3); border-radius: 99px; height: 5px; overflow: hidden; }
    .prog-fill { height: 100%; border-radius: 99px; transition: width 0.8s cubic-bezier(0.16,1,0.3,1); }

    /* ── METRIC GRID ── */
    .mgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; margin-top: 0.75rem; }
    .mcard { background: var(--bg-2); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1.1rem 1.25rem; transition: border-color 0.2s; }
    .mcard:hover { border-color: var(--border-md); }
    .mcard-val { font-family: var(--ff-display); font-size: 2rem; font-weight: 700; color: var(--txt); line-height: 1; }
    .mcard-lbl { font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--txt-3); margin-top: 0.35rem; }

    /* ── KEYWORD PILLS ── */
    .pill-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .pill { font-family: var(--ff-mono); font-size: 0.7rem; padding: 0.28rem 0.75rem; border-radius: 99px; cursor: default; transition: transform 0.15s, filter 0.15s; white-space: nowrap; }
    .pill:hover { transform: translateY(-1px); filter: brightness(1.2); }
    .pill-green { background: var(--green-dim); color: var(--green); border: 1px solid var(--green-glow); }
    .pill-red { background: var(--red-dim); color: var(--red); border: 1px solid rgba(239,68,68,0.2); }
    .pill-blue { background: var(--blue-dim); color: var(--blue); border: 1px solid rgba(79,138,255,0.2); }
    .pill-purple { background: var(--purple-dim); color: var(--purple); border: 1px solid rgba(139,92,246,0.2); }
    .pill-amber { background: var(--amber-dim); color: var(--amber); border: 1px solid rgba(245,158,11,0.2); }

    /* ── INTERACTIVE KEYWORD ── */
    .kw-suggestion-card { background: var(--bg-2); border: 1px solid var(--border); border-left: 3px solid var(--blue); border-radius: 0 var(--r-md) var(--r-md) 0; padding: 1.1rem 1.25rem; margin-top: 0.85rem; animation: slideDown 0.25s cubic-bezier(0.16,1,0.3,1); }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
    .kw-suggestion-label { font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--blue); margin-bottom: 0.5rem; font-weight: 500; }
    .kw-suggestion-text { font-size: 0.87rem; color: var(--txt); line-height: 1.7; font-style: italic; margin-bottom: 0.75rem; }
    .kw-placement-chips { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
    .kw-placement-chip { font-family: var(--ff-mono); font-size: 0.62rem; padding: 0.22rem 0.6rem; border-radius: 99px; background: var(--blue-dim); color: var(--blue); border: 1px solid rgba(79,138,255,0.2); }

    /* ── LIVE EDIT PANEL ── */
    .live-edit-panel {
        background: var(--bg-1);
        border: 1px solid rgba(79,138,255,0.18);
        border-radius: var(--r-xl);
        overflow: hidden;
        position: relative;
    }
    .live-edit-panel::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, #4f8aff, #22d3ee, #8b5cf6);
    }
    .live-edit-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 1rem 1.5rem;
        background: var(--bg-2);
        border-bottom: 1px solid var(--border);
    }
    .live-edit-title {
        display: flex; align-items: center; gap: 0.65rem;
        font-weight: 600; font-size: 0.9rem; color: var(--txt);
    }
    .live-pulse {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--blue);
        box-shadow: 0 0 8px var(--blue);
        animation: pulse-dot 1.5s ease infinite;
    }
    .live-edit-meta {
        font-family: var(--ff-mono); font-size: 0.6rem;
        color: var(--txt-3); letter-spacing: 0.08em;
    }
    .live-edit-body { padding: 1.25rem 1.5rem 1.5rem; }

    /* ── RE-SCORE RESULT ── */
    .rescore-result {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: var(--r-lg);
        padding: 1.25rem 1.5rem;
        margin-top: 1rem;
        animation: slideDown 0.3s cubic-bezier(0.16,1,0.3,1);
    }
    .rescore-scores {
        display: flex; align-items: center; gap: 1.5rem;
        margin-bottom: 1rem;
    }
    .rescore-score-item { text-align: center; }
    .rescore-score-val { font-family: var(--ff-display); font-size: 3rem; font-weight: 700; line-height: 1; }
    .rescore-score-lbl { font-family: var(--ff-mono); font-size: 0.55rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--txt-3); margin-top: 0.2rem; }
    .rescore-arrow { font-size: 2rem; color: var(--txt-3); opacity: 0.3; }
    .rescore-delta { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 1rem; border-radius: 99px; font-family: var(--ff-display); font-size: 1.1rem; font-weight: 700; }

    /* ── KEYWORD DIFF ── */
    .kw-diff-row {
        display: flex; gap: 1rem; margin-top: 1rem;
    }
    .kw-diff-col { flex: 1; }
    .kw-diff-title { font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.5rem; font-weight: 500; }
    .kw-diff-title.gained { color: var(--green); }
    .kw-diff-title.lost { color: var(--red); }

    /* ── LOOP TIMELINE ── */
    .loop-timeline {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: var(--r-md);
        padding: 1rem 1.25rem;
        margin-top: 1rem;
    }
    .loop-timeline-title { font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--txt-3); margin-bottom: 0.75rem; }
    .loop-entry { display: flex; align-items: center; gap: 0.85rem; padding: 0.45rem 0; border-bottom: 1px solid var(--border); }
    .loop-entry:last-child { border-bottom: none; }
    .loop-entry-num { font-family: var(--ff-mono); font-size: 0.6rem; color: var(--txt-3); min-width: 20px; }
    .loop-entry-score { font-family: var(--ff-display); font-size: 1rem; font-weight: 700; min-width: 32px; }
    .loop-entry-bar { flex: 1; height: 4px; background: var(--bg-3); border-radius: 99px; overflow: hidden; }
    .loop-entry-fill { height: 100%; border-radius: 99px; }
    .loop-entry-delta { font-family: var(--ff-mono); font-size: 0.65rem; min-width: 50px; text-align: right; }
    .loop-entry-ts { font-family: var(--ff-mono); font-size: 0.55rem; color: var(--txt-3); min-width: 70px; text-align: right; }

    /* ── INSERT KEYWORD FLASH ── */
    @keyframes insertFlash {
        0%   { background: rgba(79,138,255,0.25); }
        100% { background: transparent; }
    }
    .keyword-inserted { animation: insertFlash 1.5s ease forwards; border-radius: 3px; }

    /* ── RECRUITER ENGINE v2 ── */
    .decision-card { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-xl); padding: 2rem; position: relative; overflow: hidden; }
    .decision-badge { display: inline-flex; align-items: center; gap: 0.65rem; padding: 0.6rem 1.25rem; border-radius: 99px; font-weight: 700; font-size: 1rem; letter-spacing: 0.01em; }
    .decision-hire { background: rgba(16,185,129,0.12); border: 1.5px solid rgba(16,185,129,0.35); color: #10b981; box-shadow: 0 0 24px rgba(16,185,129,0.15); }
    .decision-maybe { background: rgba(245,158,11,0.12); border: 1.5px solid rgba(245,158,11,0.35); color: #f59e0b; box-shadow: 0 0 24px rgba(245,158,11,0.12); }
    .decision-reject { background: rgba(239,68,68,0.12); border: 1.5px solid rgba(239,68,68,0.35); color: #ef4444; box-shadow: 0 0 24px rgba(239,68,68,0.1); }
    .decision-confidence { font-family: var(--ff-mono); font-size: 0.68rem; color: var(--txt-3); letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.5rem; }
    .recruiter-10s { background: linear-gradient(135deg, rgba(79,138,255,0.06), rgba(34,211,238,0.04)); border: 1px solid rgba(79,138,255,0.15); border-radius: var(--r-md); padding: 1.1rem 1.25rem; margin-top: 1.25rem; position: relative; }
    .recruiter-10s::before { content: '⏱ 10-Second Impression'; display: block; font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--blue); margin-bottom: 0.5rem; font-weight: 500; }
    .recruiter-10s-text { font-size: 0.9rem; color: var(--txt); line-height: 1.75; font-style: italic; }
    .strengths-weaknesses { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.25rem; }
    .sw-col { background: var(--bg-2); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1rem; }
    .sw-col-title { font-family: var(--ff-mono); font-size: 0.6rem; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.75rem; font-weight: 500; }
    .sw-col-title.green { color: var(--green); }
    .sw-col-title.red { color: var(--red); }
    .sw-item { display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 0.8rem; color: var(--txt-2); line-height: 1.55; }
    .sw-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; margin-top: 0.38rem; }
    .sw-dot.green { background: var(--green); box-shadow: 0 0 6px var(--green); }
    .sw-dot.red { background: var(--red); box-shadow: 0 0 6px var(--red); }
    .risk-indicator { display: inline-flex; align-items: center; gap: 0.5rem; margin-top: 1rem; }
    .risk-label { font-family: var(--ff-mono); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--txt-3); }
    .risk-badge { font-family: var(--ff-mono); font-size: 0.68rem; padding: 0.25rem 0.75rem; border-radius: 99px; font-weight: 500; }
    .risk-low { background: var(--green-dim); color: var(--green); border: 1px solid var(--green-glow); }
    .risk-med { background: var(--amber-dim); color: var(--amber); border: 1px solid rgba(245,158,11,0.2); }
    .risk-high { background: var(--red-dim); color: var(--red); border: 1px solid rgba(239,68,68,0.2); }

    /* ── SUGGESTIONS ── */
    .sug-item { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1rem 1.1rem; margin-bottom: 0.6rem; font-size: 0.87rem; color: var(--txt-2); line-height: 1.65; display: flex; align-items: flex-start; gap: 0.85rem; transition: border-color 0.2s, transform 0.2s; }
    .sug-item:hover { border-color: var(--border-md); transform: translateX(2px); }
    .sug-num { font-family: var(--ff-mono); font-size: 0.62rem; color: var(--blue); background: var(--blue-dim); border: 1px solid rgba(79,138,255,0.2); border-radius: 4px; padding: 0.2rem 0.45rem; margin-top: 0.1rem; flex-shrink: 0; min-width: 28px; text-align: center; }

    /* ── CHAT ── */
    .chat-wrap { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-xl); overflow: hidden; }
    .chat-messages { padding: 1.25rem; max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; }
    .chat-msg-user { align-self: flex-end; background: var(--blue-dim); border: 1px solid rgba(79,138,255,0.2); border-radius: var(--r-md) var(--r-md) 2px var(--r-md); padding: 0.75rem 1rem; max-width: 80%; font-size: 0.85rem; color: var(--txt); line-height: 1.6; }
    .chat-msg-ai { align-self: flex-start; background: var(--bg-2); border: 1px solid var(--border); border-radius: 2px var(--r-md) var(--r-md) var(--r-md); padding: 0.75rem 1rem; max-width: 85%; font-size: 0.85rem; color: var(--txt-2); line-height: 1.65; }
    .chat-msg-label { font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.35rem; }
    .lbl-user { color: var(--blue); }
    .lbl-ai { color: var(--txt-3); }

    /* ── ALERTS ── */
    .alert { border-radius: var(--r-md); padding: 0.85rem 1.1rem; font-size: 0.85rem; margin-bottom: 0.6rem; display: flex; align-items: center; gap: 0.6rem; }
    .alert-warn { background: var(--amber-dim); border: 1px solid rgba(245,158,11,0.2); color: var(--amber); }
    .alert-err  { background: var(--red-dim);   border: 1px solid rgba(239,68,68,0.2);   color: var(--red); }
    .alert-ok   { background: var(--green-dim); border: 1px solid var(--green-glow);     color: var(--green); }

    /* ── OPTIMIZER OUTPUT ── */
    .opt-output { background: var(--bg); border: 1px solid var(--border); border-radius: var(--r-lg); font-family: var(--ff-mono); font-size: 0.77rem; line-height: 1.8; color: var(--txt-2); padding: 1.5rem 1.75rem; max-height: 520px; overflow-y: auto; white-space: pre-wrap; word-break: break-word; }

    /* ── JOB FIT ── */
    .fit-row { display: flex; align-items: center; gap: 1rem; background: var(--bg-2); border: 1px solid var(--border); border-radius: var(--r-md); padding: 0.85rem 1.1rem; margin-bottom: 0.55rem; transition: border-color 0.2s, transform 0.2s; }
    .fit-row:hover { border-color: var(--border-md); transform: translateX(2px); }
    .fit-role { flex: 1; font-weight: 500; font-size: 0.88rem; color: var(--txt); }
    .fit-co { font-size: 0.75rem; color: var(--txt-3); margin-top: 0.1rem; }
    .fit-pct { font-family: var(--ff-mono); font-size: 0.8rem; font-weight: 500; padding: 0.25rem 0.7rem; border-radius: 99px; }

    /* ── INSIGHT ROWS ── */
    .insight-row { display: flex; align-items: center; justify-content: space-between; padding: 0.7rem 0; border-bottom: 1px solid var(--border); }
    .insight-row:last-child { border-bottom: none; }
    .insight-label { font-size: 0.82rem; color: var(--txt-2); }
    .insight-badge { font-family: var(--ff-mono); font-size: 0.68rem; padding: 0.25rem 0.7rem; border-radius: 99px; font-weight: 500; }

    /* ── DOWNLOAD BUTTONS ── */
    [data-testid="stDownloadButton"] button { background: var(--bg-2) !important; color: var(--txt-2) !important; border: 1px solid var(--border-md) !important; border-radius: var(--r-sm) !important; font-family: var(--ff-mono) !important; font-size: 0.7rem !important; letter-spacing: 0.06em !important; padding: 0.45rem 1rem !important; transition: all 0.15s !important; box-shadow: none !important; }
    [data-testid="stDownloadButton"] button:hover { background: var(--bg-3) !important; border-color: var(--blue) !important; color: var(--txt) !important; transform: none !important; box-shadow: none !important; }

    /* ── METRIC (native) ── */
    [data-testid="stMetric"] { background: var(--bg-2); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1rem 1.25rem; }
    [data-testid="stMetric"] label { font-family: var(--ff-mono) !important; font-size: 0.6rem !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; color: var(--txt-3) !important; }
    [data-testid="stMetricValue"] { font-family: var(--ff-display) !important; font-size: 1.6rem !important; font-weight: 700 !important; color: var(--txt) !important; }
    [data-testid="stMetricDelta"] { font-family: var(--ff-mono) !important; font-size: 0.72rem !important; }

    /* ── SPINNER ── */
    .stSpinner > div { border-top-color: var(--blue) !important; }

    /* ── STAGED LOADER ── */
    .loader-step { display: flex; align-items: center; gap: 0.85rem; padding: 0.65rem 0; }
    .loader-step-icon { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0; transition: all 0.3s; }
    .loader-step-icon.done { background: var(--green-dim); border: 1px solid var(--green-glow); color: var(--green); }
    .loader-step-icon.active { background: var(--blue-dim); border: 1px solid rgba(79,138,255,0.3); color: var(--blue); animation: pulse-dot 1.2s ease infinite; }
    .loader-step-icon.pending { background: var(--bg-3); border: 1px solid var(--border); color: var(--txt-3); }
    .loader-step-text { font-size: 0.85rem; text-align: left; }
    .loader-step-text.done { color: var(--txt-2); }
    .loader-step-text.active { color: var(--txt); font-weight: 500; }
    .loader-step-text.pending { color: var(--txt-3); }

    /* ── EMPTY STATE ── */
    .empty-state { text-align: center; padding: 5rem 2rem; }
    .empty-icon { font-size: 2.5rem; opacity: 0.15; display: block; margin-bottom: 1.25rem; }
    .empty-title { font-family: var(--ff-display); font-size: 1.15rem; font-weight: 700; color: var(--txt-3); margin-bottom: 0.5rem; }
    .empty-sub { font-size: 0.82rem; color: var(--txt-3); max-width: 380px; margin: 0 auto; line-height: 1.65; }
    .empty-steps { display: flex; align-items: center; justify-content: center; gap: 1rem; margin-top: 2rem; flex-wrap: wrap; }
    .empty-step { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--r-md); padding: 0.75rem 1.1rem; font-size: 0.78rem; color: var(--txt-2); display: flex; align-items: center; gap: 0.5rem; }
    .empty-num { font-family: var(--ff-mono); font-size: 0.6rem; color: var(--blue); background: var(--blue-dim); border: 1px solid rgba(79,138,255,0.2); border-radius: 4px; padding: 0.1rem 0.4rem; min-width: 22px; text-align: center; }
    .empty-arrow { color: var(--txt-3); opacity: 0.4; font-size: 0.7rem; }

    /* ── KEYWORD GROUP ── */
    .kw-group { background: var(--bg-2); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1rem; margin-bottom: 0.65rem; }
    .kw-group-title { font-family: var(--ff-mono); font-size: 0.62rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--txt-3); margin-bottom: 0.65rem; display: flex; align-items: center; gap: 0.4rem; }

    /* ── MISC ── */
    .divider { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
    .section-hdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.75rem; }
    .section-title { font-family: var(--ff-display); font-size: 1.45rem; font-weight: 700; letter-spacing: -0.02em; color: var(--txt); }
    .section-ts { font-family: var(--ff-mono); font-size: 0.63rem; color: var(--txt-3); letter-spacing: 0.08em; }
    .content-pad { padding: 0 2.5rem; }
    .recruiter-note { background: var(--bg-2); border: 1px solid var(--border); border-left: 3px solid var(--blue); border-radius: 0 var(--r-sm) var(--r-sm) 0; padding: 1rem 1.25rem; margin-top: 1.25rem; font-size: 0.85rem; color: var(--txt-2); line-height: 1.7; font-style: italic; }
    .recruiter-note::before { content: 'Recruiter Note'; display: block; font-family: var(--ff-mono); font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--blue); margin-bottom: 0.5rem; font-style: normal; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "analysis_result":       None,
        "resume_text_cache":     None,
        "optimized_resume":      None,
        "opt_timestamp":         None,
        "opt_error":             None,
        "is_generating":         False,
        "chat_history":          [],
        "backend_ok":            None,
        # Improvement tracking
        "previous_score":        None,
        "previous_analysis":     None,
        "analysis_count":        0,
        # Interactive keywords
        "selected_keyword":      None,
        "kw_suggestion_cache":   {},
        # ── v2.2 Live Loop
        "live_resume_text":      None,   # current editable text
        "live_rescore_result":   None,   # last re-score analysis dict
        "live_rescore_prev_score": None, # score before last rescore
        "score_history":         [],     # [{score, ts, delta}]
        "pending_kw_insert":     None,   # keyword sentence to inject
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# API HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _unwrap(raw: dict) -> dict:
    if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
        return raw["data"]
    return raw

def _safe_list(val) -> list:
    if val is None: return []
    if isinstance(val, list): return val
    if isinstance(val, (set, tuple)): return list(val)
    return []

def _safe_int(val, default=0) -> int:
    try: return int(val)
    except: return default


def call_analyze_api(pdf_bytes: bytes, filename: str, jd_text: str) -> dict:
    url  = f"{BACKEND_URL}/analyze"
    resp = requests.post(url, files={"file": (filename, pdf_bytes, "application/pdf")},
                         data={"job_description": jd_text}, timeout=60)
    try:
        raw = resp.json()
    except Exception as e:
        raise ValueError(f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}")
    if resp.status_code != 200:
        msg = raw.get("detail") or raw.get("error") or str(raw)
        raise RuntimeError(f"Backend error {resp.status_code}: {msg}")
    return _unwrap(raw)


def call_optimize_api(resume_text: str, jd_text: str) -> dict:
    url  = f"{BACKEND_URL}/optimize"
    resp = requests.post(url, json={"resume_text": resume_text, "job_description": jd_text}, timeout=120)
    try:
        raw = resp.json()
    except Exception as e:
        raise ValueError(f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}")
    if resp.status_code != 200:
        msg = raw.get("detail") or raw.get("error") or str(raw)
        raise RuntimeError(f"Backend error {resp.status_code}: {msg}")
    return _unwrap(raw)


def call_rescore_api(resume_text: str, jd_text: str) -> dict:
    """Re-score by posting updated text. Reuses the analyze endpoint via text injection."""
    url  = f"{BACKEND_URL}/analyze"
    # Send as a synthetic "text-only" PDF using the text endpoint if available,
    # otherwise POST as multipart with a .txt file so backend can handle it.
    # Try /rescore first (text-only endpoint), fall back to /analyze with text file.
    rescore_url = f"{BACKEND_URL}/rescore"
    try:
        resp = requests.post(rescore_url,
                             json={"resume_text": resume_text, "job_description": jd_text},
                             timeout=60)
        if resp.status_code == 200:
            return _unwrap(resp.json())
    except Exception:
        pass
    # Fallback: wrap text as a fake PDF upload
    fake_txt = resume_text.encode("utf-8")
    resp = requests.post(url,
                         files={"file": ("resume_edit.txt", fake_txt, "text/plain")},
                         data={"job_description": jd_text}, timeout=60)
    try:
        raw = resp.json()
    except Exception as e:
        raise ValueError(f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}")
    if resp.status_code != 200:
        msg = raw.get("detail") or raw.get("error") or str(raw)
        raise RuntimeError(f"Backend error {resp.status_code}: {msg}")
    return _unwrap(raw)


def parse_analysis(data: dict) -> dict:
    def _get(*keys, default=None):
        for k in keys:
            if k in data: return data[k]
        return default
    return {
        "ats_score":        _safe_int(_get("ats_score","atsScore","score"), 0),
        "semantic_score":   _safe_int(_get("semantic_score","semanticScore"), 0),
        "keyword_score":    _safe_int(_get("keyword_score","keywordScore"), 0),
        "matched_keywords": _safe_list(_get("matched_keywords","matchedKeywords","matched")),
        "missing_keywords": _safe_list(_get("missing_keywords","missingKeywords","missing")),
        "jd_top_keywords":  _safe_list(_get("jd_top_keywords","jdTopKeywords","top_keywords","topKeywords")),
        "suggestions":      _safe_list(_get("suggestions","improvements","recommendations")),
        "resume_text":      _get("resume_text","resumeText","extracted_text", default=""),
    }


def classify_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "rate_limit" in msg or "429" in msg:
        return "API rate limit reached. Please wait 30 seconds and try again."
    if "authentication" in msg or "401" in msg:
        return "Authentication error. Check your API key configuration."
    if "connection" in msg or "connrefused" in msg or "refused" in msg:
        return f"Cannot reach backend at {BACKEND_URL}. Make sure FastAPI is running."
    if "timeout" in msg:
        return "Request timed out. The backend may be overloaded — please retry."
    return f"Request failed: {exc}"


def check_backend_health() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return r.status_code == 200
    except:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def grade_tag(score: int) -> tuple:
    if score >= 80: return ("Strong Match", "background:var(--green-dim);color:var(--green);border:1px solid var(--green-glow);")
    if score >= 60: return ("Moderate Match", "background:var(--amber-dim);color:var(--amber);border:1px solid rgba(245,158,11,0.2);")
    if score >= 40: return ("Weak Match", "background:rgba(251,146,60,0.08);color:#fb923c;border:1px solid rgba(251,146,60,0.2);")
    return ("Poor Match", "background:var(--red-dim);color:var(--red);border:1px solid rgba(239,68,68,0.2);")


def prog_color(pct: int) -> str:
    if pct >= 70: return "linear-gradient(90deg,#10b981,#22d3ee)"
    if pct >= 45: return "linear-gradient(90deg,#f59e0b,#fb923c)"
    return "linear-gradient(90deg,#ef4444,#f87171)"


def render_progress(label: str, pct: int):
    color = prog_color(pct)
    st.markdown(f"""
    <div class="prog-row">
        <div class="prog-header">
            <span class="prog-name">{label}</span>
            <span class="prog-pct">{pct}%</span>
        </div>
        <div class="prog-track">
            <div class="prog-fill" style="width:{pct}%;background:{color};"></div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_alert(msg: str, kind="warn"):
    icon = {"warn": "⚠", "err": "✕", "ok": "✓"}.get(kind, "·")
    cls  = {"warn": "alert-warn", "err": "alert-err", "ok": "alert-ok"}.get(kind, "alert-warn")
    st.markdown(f'<div class="alert {cls}"><span>{icon}</span>{msg}</div>', unsafe_allow_html=True)


def build_gauge(score: int) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge", value=score,
        gauge={
            "axis": {"range": [0,100], "tickcolor": "#1e2a3a", "tickfont": {"color":"#475569","size":9}, "nticks":6},
            "bar": {"color":"rgba(0,0,0,0)", "thickness":0},
            "bgcolor":"#0d1117", "bordercolor":"rgba(255,255,255,0.07)", "borderwidth":1,
            "steps": [
                {"range":[0,40],   "color":"rgba(239,68,68,0.15)"},
                {"range":[40,65],  "color":"rgba(245,158,11,0.12)"},
                {"range":[65,100], "color":"rgba(16,185,129,0.12)"},
            ],
            "threshold":{"line":{"color":"#4f8aff","width":3},"thickness":0.82,"value":score},
        }
    ))
    fig.add_annotation(x=0.5, y=0.2, text=f"<b>{score}</b>",
                       font=dict(size=40, color="#e2e8f0", family="Fraunces"),
                       showarrow=False, xref="paper", yref="paper")
    fig.add_annotation(x=0.5, y=0.06, text="/ 100",
                       font=dict(size=12, color="#475569", family="DM Mono"),
                       showarrow=False, xref="paper", yref="paper")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=230, margin=dict(t=20,b=0,l=20,r=20))
    return fig


def group_keywords(keywords: list) -> dict:
    tools_kw = {"python","java","javascript","typescript","sql","go","rust","scala","r",
                "tensorflow","pytorch","keras","sklearn","langchain","faiss","pandas","numpy",
                "spark","kafka","airflow","dbt","react","docker","kubernetes","aws","gcp","azure",
                "git","linux","bash","fastapi","flask","django","node","vue","angular"}
    skills_kw = {"machine learning","deep learning","nlp","computer vision","rag","llm","gpt",
                 "transformer","bert","embeddings","fine-tuning","prompt engineering",
                 "data science","analytics","statistics","optimization","a/b testing",
                 "product management","agile","scrum","ci/cd","devops","mlops"}
    groups = {"⚙️  Tools & Technologies": [], "🧠  Skills & Methods": [], "📋  Other": []}
    for kw in keywords:
        kl = kw.lower()
        if any(t in kl for t in tools_kw):
            groups["⚙️  Tools & Technologies"].append(kw)
        elif any(s in kl for s in skills_kw):
            groups["🧠  Skills & Methods"].append(kw)
        else:
            groups["📋  Other"].append(kw)
    return {k: v for k, v in groups.items() if v}


def infer_job_fits(analysis: dict) -> list:
    matched = " ".join(analysis.get("matched_keywords", [])).lower()
    fits = []
    role_map = [
        (["machine learning","deep learning","tensorflow","pytorch","model"], "Machine Learning Engineer", "FAANG / AI Labs"),
        (["rag","llm","langchain","embeddings","gpt","prompt"], "Generative AI Engineer", "AI-first Startups"),
        (["data science","analytics","statistics","sql","pandas","tableau"], "Data Scientist", "Product Companies"),
        (["mlops","kubernetes","docker","pipeline","airflow","ci/cd"], "MLOps / AI Platform Engineer", "Platform Teams"),
        (["react","node","typescript","frontend","api","fastapi","backend"], "Full Stack AI Engineer", "Startups / FAANG"),
        (["product","roadmap","stakeholder","agile","sprint","kpi"], "AI Product Manager", "Tech Cos"),
        (["cv","yolo","object detection","segmentation","computer vision"], "Computer Vision Engineer", "Robotics / Auto"),
        (["nlp","bert","transformers","text","classification","ner"], "NLP Engineer", "Enterprise AI"),
    ]
    for keywords, role, company_type in role_map:
        hits = sum(1 for kw in keywords if kw in matched)
        if hits >= 2:
            pct = min(95, 55 + hits * 8)
            fits.append({"role": role, "company": company_type, "pct": pct})
    fits.sort(key=lambda x: x["pct"], reverse=True)
    return fits[:5]


def pct_badge_style(pct: int) -> str:
    if pct >= 75: return "background:var(--green-dim);color:var(--green);border:1px solid var(--green-glow);"
    if pct >= 55: return "background:var(--amber-dim);color:var(--amber);border:1px solid rgba(245,158,11,0.2);"
    return "background:var(--red-dim);color:var(--red);border:1px solid rgba(239,68,68,0.2);"


def insight_badge(pct: int) -> tuple:
    if pct >= 70: return "Strong",   "background:var(--green-dim);color:var(--green);border:1px solid var(--green-glow);"
    if pct >= 45: return "Moderate", "background:var(--amber-dim);color:var(--amber);border:1px solid rgba(245,158,11,0.2);"
    return "Needs Work", "background:var(--red-dim);color:var(--red);border:1px solid rgba(239,68,68,0.2);"


# ══════════════════════════════════════════════════════════════════════════════
# IMPROVEMENT TRACKING (v2.1)
# ══════════════════════════════════════════════════════════════════════════════
def update_score_history(new_score: int):
    if st.session_state.analysis_result is not None:
        st.session_state.previous_score    = st.session_state.analysis_result.get("ats_score", None)
        st.session_state.previous_analysis = st.session_state.analysis_result
    st.session_state.analysis_count += 1


def render_improvement_tracker(current_score: int):
    prev = st.session_state.previous_score
    if prev is None:
        return
    delta = current_score - prev
    if delta > 0:
        kind, delta_cls, delta_str = "improved", "delta-up", f"+{delta}"
        msg_strong, msg = "ATS score improved", f"Your resume is now a stronger match — {delta} points gained since last analysis."
    elif delta < 0:
        kind, delta_cls, delta_str = "declined", "delta-down", str(delta)
        msg_strong, msg = "Score dropped", f"Your ATS score decreased by {abs(delta)} points. Consider reverting changes or re-optimizing."
    else:
        kind, delta_cls, delta_str = "same", "delta-same", "→ 0"
        msg_strong, msg = "No change detected", "Your score is unchanged. Try incorporating more missing keywords."

    prev_color = "#10b981" if prev >= 70 else ("#f59e0b" if prev >= 45 else "#ef4444")
    curr_color = "#10b981" if current_score >= 70 else ("#f59e0b" if current_score >= 45 else "#ef4444")

    st.markdown(f"""
    <div class="improvement-banner {kind}">
        <div style="display:flex;align-items:center;gap:0.75rem;">
            <div style="font-family:var(--ff-mono);font-size:0.58rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--txt-3);">Score History</div>
            <div class="score-compare">
                <div class="score-compare-item">
                    <div class="score-compare-val" style="color:{prev_color};">{prev}</div>
                    <div class="score-compare-lbl">Previous</div>
                </div>
                <span class="score-compare-arrow">→</span>
                <div class="score-compare-item">
                    <div class="score-compare-val" style="color:{curr_color};">{current_score}</div>
                    <div class="score-compare-lbl">Current</div>
                </div>
            </div>
            <div class="delta-badge {delta_cls}" style="margin-left:0.5rem;">{delta_str} pts</div>
        </div>
        <div class="delta-msg"><strong>{msg_strong}:</strong> {msg}</div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE KEYWORDS (v2.1)
# ══════════════════════════════════════════════════════════════════════════════
KW_SUGGESTIONS = {
    "python":           ("Skills / Projects", "Developed end-to-end ML pipelines in Python, reducing data processing time by 40%."),
    "tensorflow":       ("Skills / Projects", "Built and fine-tuned computer vision models using TensorFlow, achieving 94% validation accuracy."),
    "pytorch":          ("Skills / Experience", "Implemented transformer-based architectures in PyTorch for production NLP classification tasks."),
    "docker":           ("Skills / Experience", "Containerized microservices using Docker, enabling consistent deployments across dev and prod environments."),
    "kubernetes":       ("Skills / Experience", "Orchestrated containerized ML workloads on Kubernetes, supporting 99.9% uptime SLA."),
    "aws":              ("Skills / Experience", "Deployed scalable data pipelines on AWS (S3, Lambda, SageMaker), cutting inference latency by 35%."),
    "gcp":              ("Skills / Experience", "Leveraged Google Cloud Platform (BigQuery, Vertex AI) to build and serve production ML models."),
    "sql":              ("Skills / Experience", "Designed and optimized complex SQL queries against multi-TB databases, improving report generation speed by 60%."),
    "spark":            ("Skills / Experience", "Processed 5TB+ daily event data with Apache Spark, enabling real-time personalization features."),
    "kafka":            ("Skills / Experience", "Built event-driven architectures using Apache Kafka, supporting 100K+ messages per second."),
    "airflow":          ("Experience", "Orchestrated ML training and data workflows using Apache Airflow, ensuring reliable daily model retraining."),
    "langchain":        ("Projects / Skills", "Built a production RAG pipeline using LangChain and FAISS, reducing hallucination rate by 28%."),
    "react":            ("Skills / Projects", "Developed responsive front-end dashboards in React, improving user engagement metrics by 22%."),
    "fastapi":          ("Skills / Projects", "Designed RESTful model-serving APIs with FastAPI, handling 2K+ RPS with <50ms p99 latency."),
    "machine learning": ("Summary / Experience", "Applied machine learning techniques (classification, regression, clustering) to solve business problems across 3 product verticals."),
    "deep learning":    ("Skills / Projects", "Designed and trained deep learning architectures (CNNs, LSTMs, Transformers) for vision and NLP tasks."),
    "nlp":              ("Skills / Experience", "Developed NLP solutions including entity recognition, semantic search, and text summarization at scale."),
    "llm":              ("Summary / Projects", "Fine-tuned and deployed large language models (LLMs) for domain-specific Q&A and content generation."),
    "rag":              ("Projects / Skills", "Engineered a Retrieval-Augmented Generation (RAG) system improving answer accuracy by 31% over baseline."),
    "mlops":            ("Skills / Experience", "Implemented MLOps practices including model versioning, A/B testing, and automated retraining pipelines."),
    "a/b testing":      ("Experience / Projects", "Designed and analyzed A/B tests across product features, driving a 15% lift in key conversion metrics."),
    "agile":            ("Experience / Summary", "Led cross-functional teams in Agile sprints, delivering features 20% ahead of roadmap schedule."),
    "ci/cd":            ("Skills / Experience", "Automated model deployment using CI/CD pipelines (GitHub Actions, Jenkins), reducing release cycle from days to hours."),
    "data science":     ("Summary", "Data scientist with 4+ years of experience building ML models and data-driven products across e-commerce and fintech domains."),
    "computer vision":  ("Skills / Projects", "Built computer vision pipelines for real-time object detection and image segmentation using YOLOv8 and OpenCV."),
    "prompt engineering":("Skills / Projects", "Designed structured prompt templates for LLM-based agents, improving task completion accuracy by 25%."),
}
DEFAULT_SUGGESTION = ("Skills / Experience", "Incorporate '{kw}' naturally into your skills section or within a bullet point describing a relevant project or role.")


def get_kw_suggestion(keyword: str) -> tuple:
    kl = keyword.lower().strip()
    if kl in KW_SUGGESTIONS:
        return KW_SUGGESTIONS[kl]
    for key, val in KW_SUGGESTIONS.items():
        if key in kl or kl in key:
            return val
    placement, template = DEFAULT_SUGGESTION
    return placement, template.replace("{kw}", keyword)


# ══════════════════════════════════════════════════════════════════════════════
# ADVANCED RECRUITER ENGINE (v2.1)
# ══════════════════════════════════════════════════════════════════════════════
def advanced_recruiter_decision(analysis: dict, score: int) -> dict:
    matched = _safe_list(analysis.get("matched_keywords"))
    missing = _safe_list(analysis.get("missing_keywords"))
    sem     = _safe_int(analysis.get("semantic_score"), 0)
    kws     = _safe_int(analysis.get("keyword_score"), 0)
    sugs    = _safe_list(analysis.get("suggestions"))
    mn, xn  = len(matched), len(missing)
    total   = max(mn + xn, 1)
    cov_pct = int(100 * mn / total)

    if score >= 78:
        decision, d_cls = "Strong Hire", "decision-hire"
        confidence = min(97, score + 5)
        risk, risk_cls = "Low", "risk-low"
    elif score >= 55:
        decision, d_cls = "Borderline — Needs Review", "decision-maybe"
        confidence = score + 2
        risk, risk_cls = "Medium", "risk-med"
    else:
        decision, d_cls = "Low ATS Fit", "decision-reject"
        confidence = max(60, 100 - score)
        risk, risk_cls = "High", "risk-high"

    if score >= 78:
        impression = (f"Strong resume — immediately clear alignment with the role. "
                      f"{mn} keywords hit, semantic match is {'strong' if sem >= 70 else 'decent'} at {sem}%. "
                      f"This is the kind of resume I'd shortlist without hesitation.")
    elif score >= 55:
        impression = (f"Decent background, but the resume isn't speaking the language of this JD. "
                      f"Only {cov_pct}% keyword coverage — {xn} critical terms missing. "
                      f"I'd probably give it 15 seconds before moving on.")
    else:
        impression = (f"Resume doesn't clear the bar for this role as written. "
                      f"With just {mn}/{total} keywords matched and an ATS score of {score}, "
                      f"it would likely be filtered before reaching a human.")

    strengths = []
    if sem >= 65: strengths.append(f"Strong semantic alignment with the JD ({sem}% similarity score)")
    if mn >= 8:   strengths.append(f"Good keyword density — {mn} role-relevant terms detected")
    if kws >= 65: strengths.append(f"Keyword match rate of {kws}% clears the ATS threshold")
    if cov_pct >= 60: strengths.append(f"Covers {cov_pct}% of the JD's critical terminology")
    if score >= 75: strengths.append("Overall profile competitive for automated screening")
    if not strengths: strengths = ["Resume structure is parseable by ATS systems", "Some relevant experience detected"]

    weaknesses = []
    if xn >= 5:
        weaknesses.append(f"{xn} critical keywords absent — notably: {', '.join(missing[:3])}")
    if sem < 55: weaknesses.append(f"Semantic similarity low ({sem}%) — language doesn't mirror the JD")
    if kws < 50: weaknesses.append(f"Keyword score below ATS threshold ({kws}% vs 55% minimum)")
    if cov_pct < 50: weaknesses.append(f"Only {cov_pct}% of role-critical terms are present")
    if sugs and len(sugs) >= 3: weaknesses.append(f"{len(sugs)} actionable improvement areas identified by AI")
    if not weaknesses: weaknesses = ["Minor keyword gaps remain", "Could benefit from more quantified impact statements"]

    return {
        "decision": decision, "d_cls": d_cls, "confidence": f"{confidence}%",
        "risk": risk, "risk_cls": risk_cls, "impression": impression,
        "strengths": strengths[:4], "weaknesses": weaknesses[:4],
    }


# ══════════════════════════════════════════════════════════════════════════════
# STAGED LOADING
# ══════════════════════════════════════════════════════════════════════════════
def run_analysis_with_stages(pdf_bytes: bytes, filename: str, jd_text: str):
    STAGES = [
        ("📄", "Extracting resume data…"),
        ("🔍", "Matching with job description…"),
        ("🧠", "Scoring ATS compatibility…"),
        ("✦",  "Generating intelligence report…"),
    ]
    placeholder = st.empty()

    def render_stages(active: int):
        rows = ""
        for i, (icon, label) in enumerate(STAGES):
            if i < active:   cls, icon_c = "done",    "✓"
            elif i == active: cls, icon_c = "active",  icon
            else:             cls, icon_c = "pending", icon
            rows += f'<div class="loader-step"><div class="loader-step-icon {cls}">{icon_c}</div><span class="loader-step-text {cls}">{label}</span></div>'
        placeholder.markdown(f"""
        <div style="background:var(--bg-1);border:1px solid var(--border);border-radius:var(--r-xl);
             padding:2rem 2.5rem;max-width:480px;margin:1.5rem auto;">
            <div style="font-family:var(--ff-mono);font-size:0.6rem;letter-spacing:0.15em;
                 text-transform:uppercase;color:var(--blue);margin-bottom:1.25rem;">Analyzing your resume</div>
            {rows}
        </div>""", unsafe_allow_html=True)

    render_stages(0); time.sleep(0.4)
    render_stages(1); time.sleep(0.3)
    render_stages(2)
    try:
        raw    = call_analyze_api(pdf_bytes, filename, jd_text)
        parsed = parse_analysis(raw)
    except Exception as exc:
        placeholder.empty()
        raise exc
    render_stages(3); time.sleep(0.4)
    placeholder.empty()
    return parsed


# ══════════════════════════════════════════════════════════════════════════════
# ✨ v2.2 — LIVE RESUME IMPROVEMENT LOOP
# ══════════════════════════════════════════════════════════════════════════════

def _record_loop_entry(score: int, prev_score: int | None):
    """Append entry to the in-session score timeline."""
    ts    = datetime.datetime.now().strftime("%H:%M:%S")
    delta = (score - prev_score) if prev_score is not None else 0
    st.session_state.score_history.append({
        "score": score, "ts": ts, "delta": delta,
        "n": len(st.session_state.score_history) + 1,
    })


def _diff_keywords(old_analysis: dict, new_analysis: dict) -> tuple[list, list]:
    """Return (newly_gained, newly_lost) keyword lists."""
    old_matched = set(kw.lower() for kw in _safe_list(old_analysis.get("matched_keywords")))
    new_matched = set(kw.lower() for kw in _safe_list(new_analysis.get("matched_keywords")))
    gained = sorted(new_matched - old_matched)
    lost   = sorted(old_matched - new_matched)
    return gained, lost


def render_loop_timeline():
    """Mini score timeline for the live loop."""
    history = st.session_state.score_history
    if len(history) < 2:
        return
    st.markdown(f"""
    <div class="loop-timeline">
        <div class="loop-timeline-title">◈ Score Timeline · {len(history)} iterations</div>""",
    unsafe_allow_html=True)
    for entry in history[-6:]:  # show last 6
        score  = entry["score"]
        delta  = entry["delta"]
        bar_w  = score
        bar_c  = prog_color(score)
        d_col  = "var(--green)" if delta > 0 else ("var(--red)" if delta < 0 else "var(--txt-3)")
        d_str  = f"+{delta}" if delta > 0 else (str(delta) if delta != 0 else "—")
        s_col  = "#10b981" if score >= 70 else ("#f59e0b" if score >= 45 else "#ef4444")
        st.markdown(f"""
        <div class="loop-entry">
            <span class="loop-entry-num">#{entry['n']}</span>
            <span class="loop-entry-score" style="color:{s_col};">{score}</span>
            <div class="loop-entry-bar">
                <div class="loop-entry-fill" style="width:{bar_w}%;background:{bar_c};"></div>
            </div>
            <span class="loop-entry-delta" style="color:{d_col};">{d_str}</span>
            <span class="loop-entry-ts">{entry['ts']}</span>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_rescore_result(new_analysis: dict, old_analysis: dict):
    """Show score comparison + keyword diff after a re-score."""
    new_score  = _safe_int(new_analysis.get("ats_score"), 0)
    old_score  = _safe_int(old_analysis.get("ats_score"), 0)
    delta      = new_score - old_score
    gained, lost = _diff_keywords(old_analysis, new_analysis)

    n_col = "#10b981" if new_score >= 70 else ("#f59e0b" if new_score >= 45 else "#ef4444")
    o_col = "#10b981" if old_score >= 70 else ("#f59e0b" if old_score >= 45 else "#ef4444")
    d_cls = "delta-up" if delta > 0 else ("delta-down" if delta < 0 else "delta-same")
    d_str = f"+{delta}" if delta > 0 else (str(delta) if delta != 0 else "±0")

    new_sem = _safe_int(new_analysis.get("semantic_score"), 0)
    new_kws = _safe_int(new_analysis.get("keyword_score"), 0)
    old_sem = _safe_int(old_analysis.get("semantic_score"), 0)
    old_kws = _safe_int(old_analysis.get("keyword_score"), 0)
    sem_d = new_sem - old_sem
    kws_d = new_kws - old_kws

    def _mini_delta(d):
        if d > 0:  return f'<span style="color:var(--green);font-size:0.65rem;">▲ +{d}</span>'
        if d < 0:  return f'<span style="color:var(--red);font-size:0.65rem;">▼ {d}</span>'
        return '<span style="color:var(--txt-3);font-size:0.65rem;">—</span>'

    # Keyword diff pills
    gained_pills = "".join(f'<span class="pill pill-green">{kw}</span>' for kw in gained[:12]) if gained else '<span style="color:var(--txt-3);font-size:0.75rem;">None gained</span>'
    lost_pills   = "".join(f'<span class="pill pill-red">{kw}</span>' for kw in lost[:12])   if lost   else '<span style="color:var(--txt-3);font-size:0.75rem;">None lost</span>'

    st.markdown(f"""
    <div class="rescore-result">
        <!-- Score comparison -->
        <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;margin-bottom:1.25rem;">
            <div class="rescore-scores">
                <div class="rescore-score-item">
                    <div class="rescore-score-val" style="color:{o_col};">{old_score}</div>
                    <div class="rescore-score-lbl">Before edit</div>
                </div>
                <span class="rescore-arrow">→</span>
                <div class="rescore-score-item">
                    <div class="rescore-score-val" style="color:{n_col};">{new_score}</div>
                    <div class="rescore-score-lbl">After edit</div>
                </div>
            </div>
            <div class="delta-badge {d_cls}">{d_str} pts</div>
        </div>

        <!-- Sub-score deltas -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.65rem;margin-bottom:1.25rem;">
            <div class="mcard" style="padding:0.85rem 1rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.78rem;color:var(--txt-2);">Semantic Similarity</span>
                    {_mini_delta(sem_d)}
                </div>
                <div style="font-family:var(--ff-display);font-size:1.5rem;font-weight:700;color:var(--txt);margin-top:0.25rem;">{new_sem}%</div>
            </div>
            <div class="mcard" style="padding:0.85rem 1rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.78rem;color:var(--txt-2);">Keyword Match</span>
                    {_mini_delta(kws_d)}
                </div>
                <div style="font-family:var(--ff-display);font-size:1.5rem;font-weight:700;color:var(--txt);margin-top:0.25rem;">{new_kws}%</div>
            </div>
        </div>

        <!-- Keyword diff -->
        <div class="kw-diff-row">
            <div class="kw-diff-col">
                <div class="kw-diff-title gained">✦ Keywords Gained ({len(gained)})</div>
                <div class="pill-row">{gained_pills}</div>
            </div>
            <div class="kw-diff-col">
                <div class="kw-diff-title lost">✕ Keywords Lost ({len(lost)})</div>
                <div class="pill-row">{lost_pills}</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_tab_live_loop(analysis: dict, jd_text: str):
    """
    NEW TAB — Live Resume Improvement Loop
    Edit → Re-score → Improve → Repeat
    """
    orig_score = _safe_int(analysis.get("ats_score"), 0)

    # Seed live_resume_text on first load of this tab
    if st.session_state.live_resume_text is None:
        rt = st.session_state.get("resume_text_cache", "") or ""
        st.session_state.live_resume_text = rt
        # Seed timeline with original score if empty
        if not st.session_state.score_history:
            _record_loop_entry(orig_score, None)

    # ── HEADER
    st.markdown("""
    <div class="live-edit-panel" style="margin-bottom:1.5rem;">
        <div class="live-edit-header">
            <div class="live-edit-title">
                <div class="live-pulse"></div>
                Live Resume Editor
            </div>
            <span class="live-edit-meta">Edit · Re-score · Improve · Repeat</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Instructions row
    st.markdown("""
    <div style="background:var(--bg-2);border:1px solid var(--border);border-radius:var(--r-md);
         padding:0.85rem 1.25rem;margin-bottom:1.25rem;
         display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:var(--txt-2);">
            <span style="font-family:var(--ff-mono);font-size:0.65rem;background:var(--blue-dim);color:var(--blue);
                 border:1px solid rgba(79,138,255,0.2);border-radius:4px;padding:0.1rem 0.45rem;">01</span>
            Edit resume text below
        </div>
        <span style="color:var(--border-md);">·</span>
        <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:var(--txt-2);">
            <span style="font-family:var(--ff-mono);font-size:0.65rem;background:var(--blue-dim);color:var(--blue);
                 border:1px solid rgba(79,138,255,0.2);border-radius:4px;padding:0.1rem 0.45rem;">02</span>
            Click a missing keyword → inject sentence
        </div>
        <span style="color:var(--border-md);">·</span>
        <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:var(--txt-2);">
            <span style="font-family:var(--ff-mono);font-size:0.65rem;background:var(--blue-dim);color:var(--blue);
                 border:1px solid rgba(79,138,255,0.2);border-radius:4px;padding:0.1rem 0.45rem;">03</span>
            Hit Re-analyze Instantly
        </div>
        <span style="color:var(--border-md);">·</span>
        <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.8rem;color:var(--txt-2);">
            <span style="font-family:var(--ff-mono);font-size:0.65rem;background:var(--blue-dim);color:var(--blue);
                 border:1px solid rgba(79,138,255,0.2);border-radius:4px;padding:0.1rem 0.45rem;">04</span>
            See score delta in real time
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Two-column layout: editor left, controls right
    ed_col, ctrl_col = st.columns([1.6, 1], gap="large")

    with ed_col:
        # ── Quick inject bar (missing keywords)
        missing = _safe_list(analysis.get("missing_keywords"))
        if missing:
            st.markdown("""
            <div style="font-family:var(--ff-mono);font-size:0.6rem;letter-spacing:0.12em;
                 text-transform:uppercase;color:var(--txt-3);margin-bottom:0.5rem;">
                ⚡ Quick Inject — click to add keyword sentence
            </div>""", unsafe_allow_html=True)
            inject_cols = st.columns(min(len(missing[:8]), 4))
            for idx, kw in enumerate(missing[:8]):
                with inject_cols[idx % 4]:
                    if st.button(f"+ {kw}", key=f"inject_{kw.replace(' ','_').replace('/','_')}",
                                 use_container_width=True,
                                 help=f"Append a suggested sentence using '{kw}'"):
                        _, sentence = get_kw_suggestion(kw)
                        current_text = st.session_state.live_resume_text or ""
                        # Append with section hint
                        separator = "\n\n" if current_text and not current_text.endswith("\n\n") else ""
                        st.session_state.live_resume_text = current_text + separator + sentence
                        st.rerun()

        # ── Editable text area — seeded from session
        st.markdown('<div class="live-editor-area">', unsafe_allow_html=True)
        edited_text = st.text_area(
            label="live_editor_label",
            label_visibility="collapsed",
            value=st.session_state.live_resume_text or "",
            height=520,
            key="live_editor_widget",
            placeholder="Your resume text will appear here after the initial analysis.\nEdit freely — add keywords, rewrite bullets, update the summary.",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Sync edits back to session
        if edited_text != st.session_state.live_resume_text:
            st.session_state.live_resume_text = edited_text

        # ── Word count row
        wc  = len(edited_text.split()) if edited_text else 0
        lc  = edited_text.count("\n") if edited_text else 0
        orig_wc = len((st.session_state.resume_text_cache or "").split())
        wc_delta = wc - orig_wc
        wc_col  = "var(--green)" if wc_delta >= 0 else "var(--red)"
        wc_str  = f"+{wc_delta}" if wc_delta >= 0 else str(wc_delta)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1.25rem;margin-top:0.5rem;
             font-family:var(--ff-mono);font-size:0.62rem;color:var(--txt-3);">
            <span>{wc} words</span>
            <span style="color:{wc_col};">{wc_str} vs original</span>
            <span>{lc} lines</span>
            <span style="margin-left:auto;font-size:0.58rem;color:var(--txt-3);opacity:0.6;">
                Live editor · changes tracked
            </span>
        </div>""", unsafe_allow_html=True)

    with ctrl_col:
        # ── Current score mini display
        rescore_res = st.session_state.live_rescore_result
        display_score = _safe_int(
            (rescore_res or analysis).get("ats_score"), 0
        )
        g_label, g_style = grade_tag(display_score)
        score_color = "#10b981" if display_score >= 70 else ("#f59e0b" if display_score >= 45 else "#ef4444")
        loop_count = len(st.session_state.score_history)

        st.markdown(f"""
        <div style="background:var(--bg-1);border:1px solid var(--border);border-radius:var(--r-lg);
             padding:1.5rem;text-align:center;margin-bottom:1rem;position:relative;overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:2px;
                 background:linear-gradient(90deg,#4f8aff,#22d3ee);"></div>
            <div style="font-family:var(--ff-mono);font-size:0.58rem;letter-spacing:0.12em;
                 text-transform:uppercase;color:var(--txt-3);margin-bottom:0.5rem;">Live ATS Score</div>
            <div style="font-family:var(--ff-display);font-size:4rem;font-weight:700;line-height:1;
                 color:{score_color};">{display_score}</div>
            <span class="score-tag" style="{g_style};margin-top:0.5rem;display:inline-block;">{g_label}</span>
            <div style="font-family:var(--ff-mono);font-size:0.6rem;color:var(--txt-3);margin-top:0.75rem;">
                {loop_count} iteration{"s" if loop_count != 1 else ""} · Original: {orig_score}
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Re-analyze button
        jd = jd_text.strip() if jd_text else ""
        rescore_disabled = not edited_text or len(edited_text.strip()) < 50 or not jd

        if st.button("⚡ Re-analyze Instantly", use_container_width=True, key="rescore_btn",
                     disabled=rescore_disabled):
            with st.spinner("Scoring updated resume…"):
                try:
                    raw    = call_rescore_api(edited_text, jd)
                    parsed = parse_analysis(raw)
                    prev_a = st.session_state.live_rescore_result or analysis
                    prev_s = _safe_int(prev_a.get("ats_score"), 0)
                    st.session_state.live_rescore_prev_score  = prev_s
                    st.session_state.live_rescore_result      = parsed
                    # Update main cache so other tabs reflect the edit
                    st.session_state.resume_text_cache        = edited_text
                    _record_loop_entry(_safe_int(parsed.get("ats_score"), 0), prev_s)
                    st.rerun()
                except Exception as exc:
                    render_alert(classify_error(exc), "err")

        if rescore_disabled and not edited_text:
            st.markdown('<p style="font-size:0.72rem;color:var(--txt-3);text-align:center;margin-top:0.5rem;">Run initial analysis first to populate editor</p>', unsafe_allow_html=True)

        # ── Reset to original
        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
        if st.button("↺ Reset to Original", use_container_width=True, key="reset_btn"):
            st.session_state.live_resume_text   = st.session_state.resume_text_cache or ""
            st.session_state.live_rescore_result = None
            st.session_state.live_rescore_prev_score = None
            st.session_state.score_history = []
            _record_loop_entry(orig_score, None)
            st.rerun()

        # ── Score timeline
        render_loop_timeline()

        # ── Quick keyword status (which missing kws are now present after edit)
        if edited_text and missing:
            now_present = [kw for kw in missing if kw.lower() in edited_text.lower()]
            still_missing = [kw for kw in missing if kw.lower() not in edited_text.lower()]
            st.markdown(f"""
            <div style="background:var(--bg-2);border:1px solid var(--border);
                 border-radius:var(--r-md);padding:1rem;margin-top:1rem;">
                <div style="font-family:var(--ff-mono);font-size:0.58rem;letter-spacing:0.12em;
                     text-transform:uppercase;color:var(--txt-3);margin-bottom:0.65rem;">
                    Keyword Status (live)
                </div>
                <div style="margin-bottom:0.5rem;">
                    <div style="font-family:var(--ff-mono);font-size:0.58rem;color:var(--green);margin-bottom:0.35rem;">
                        ✓ Now present ({len(now_present)})
                    </div>
                    <div class="pill-row">
                        {"".join(f'<span class="pill pill-green">{kw}</span>' for kw in now_present[:10]) or '<span style="color:var(--txt-3);font-size:0.72rem;">None yet</span>'}
                    </div>
                </div>
                <div>
                    <div style="font-family:var(--ff-mono);font-size:0.58rem;color:var(--red);margin-bottom:0.35rem;">
                        ✕ Still missing ({len(still_missing)})
                    </div>
                    <div class="pill-row">
                        {"".join(f'<span class="pill pill-red">{kw}</span>' for kw in still_missing[:10]) or '<span style="color:var(--green);font-size:0.72rem;">All covered!</span>'}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Re-score result (shown below both columns)
    if st.session_state.live_rescore_result:
        st.markdown('<div style="margin-top:1.25rem;">', unsafe_allow_html=True)
        prev_analysis_for_diff = st.session_state.get("previous_analysis") or analysis
        render_rescore_result(st.session_state.live_rescore_result, prev_analysis_for_diff)

        # Offer to apply to main analysis
        st.markdown("<div style='margin-top:1rem;'>", unsafe_allow_html=True)
        apply_col, _ = st.columns([1, 3])
        with apply_col:
            if st.button("✓ Apply as Main Analysis", key="apply_rescore", use_container_width=True):
                new_a = st.session_state.live_rescore_result
                st.session_state.previous_score    = _safe_int(analysis.get("ats_score"), 0)
                st.session_state.previous_analysis = analysis
                st.session_state.analysis_result   = new_a
                st.session_state.analysis_count   += 1
                st.session_state.live_rescore_result = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# EXISTING TABS (unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def render_tab_decision(analysis: dict, score: int):
    rd = advanced_recruiter_decision(analysis, score)
    g_label, g_style = grade_tag(score)
    render_improvement_tracker(score)

    col1, col2 = st.columns([1, 1.8], gap="large")
    with col1:
        st.markdown(f"""
        <div class="score-hero card-accent-blue">
            <div style="font-family:var(--ff-mono);font-size:0.6rem;letter-spacing:0.18em;text-transform:uppercase;color:var(--txt-3);margin-bottom:0.35rem;">ATS Score</div>
            <div style="display:flex;align-items:baseline;justify-content:center;gap:0.1rem;margin-top:0.2rem;">
                <span class="score-num">{score}</span><span class="score-denom">/ 100</span>
            </div>
            <span class="score-tag" style="{g_style}">{g_label}</span>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(build_gauge(score), use_container_width=True, config={"displayModeBar":False})

    with col2:
        st.markdown(f"""
        <div class="decision-card card-accent-green">
            <div style="font-family:var(--ff-mono);font-size:0.6rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--txt-3);margin-bottom:0.85rem;">🤖 Recruiter Decision Engine v2</div>
            <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
                <div class="decision-badge {rd['d_cls']}">
                    <span style="font-size:1.2rem;">{'✓' if 'Hire' in rd['decision'] else ('?' if 'Borderline' in rd['decision'] else '✗')}</span>
                    {rd['decision']}
                </div>
                <div>
                    <div class="decision-confidence">Confidence: {rd['confidence']}</div>
                    <div class="risk-indicator" style="margin-top:0.35rem;">
                        <span class="risk-label">Risk:</span>
                        <span class="risk-badge {rd['risk_cls']}">{rd['risk']} Risk</span>
                    </div>
                </div>
            </div>
            <div class="recruiter-10s"><div class="recruiter-10s-text">{rd['impression']}</div></div>
            <div class="strengths-weaknesses">
                <div class="sw-col">
                    <div class="sw-col-title green">✦ Top Strengths</div>
                    {''.join(f'<div class="sw-item"><div class="sw-dot green"></div><span>{s}</span></div>' for s in rd['strengths'])}
                </div>
                <div class="sw-col">
                    <div class="sw-col-title red">⚠ Critical Weaknesses</div>
                    {''.join(f'<div class="sw-item"><div class="sw-dot red"></div><span>{w}</span></div>' for w in rd['weaknesses'])}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem;'>", unsafe_allow_html=True)
    render_progress("Semantic Similarity", _safe_int(analysis.get("semantic_score"), 0))
    render_progress("Keyword Match Rate",  _safe_int(analysis.get("keyword_score"), 0))
    render_progress("Overall ATS Score",   score)
    st.markdown("</div>", unsafe_allow_html=True)

    matched = _safe_list(analysis.get("matched_keywords"))
    missing = _safe_list(analysis.get("missing_keywords"))
    jd_top  = _safe_list(analysis.get("jd_top_keywords"))
    sugs    = _safe_list(analysis.get("suggestions"))
    st.markdown(f"""
    <div class="mgrid" style="grid-template-columns:repeat(4,1fr);margin-top:1.5rem;">
        <div class="mcard"><div class="mcard-val">{len(matched)}</div><div class="mcard-lbl">Matched Keywords</div></div>
        <div class="mcard"><div class="mcard-val">{len(missing)}</div><div class="mcard-lbl">Missing Keywords</div></div>
        <div class="mcard"><div class="mcard-val">{len(jd_top)}</div><div class="mcard-lbl">JD Top Terms</div></div>
        <div class="mcard"><div class="mcard-val">{len(sugs)}</div><div class="mcard-lbl">Action Items</div></div>
    </div>""", unsafe_allow_html=True)


def render_tab_keywords(analysis: dict):
    matched = _safe_list(analysis.get("matched_keywords"))
    missing = _safe_list(analysis.get("missing_keywords"))
    jd_top  = _safe_list(analysis.get("jd_top_keywords"))

    col1, col2 = st.columns(2, gap="large")

    with col1:
        mc = len(matched)
        st.markdown(f"""
        <div class="card card-accent-green">
            <div class="card-title"><span>✓ Matched Keywords</span><span class="pill pill-green">{mc} found</span></div>""",
        unsafe_allow_html=True)
        if matched:
            pills = "".join(f'<span class="pill pill-green">{kw}</span>' for kw in matched[:35])
            st.markdown(f'<div class="pill-row" style="max-height:160px;overflow-y:auto;">{pills}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:var(--txt-3);font-size:0.82rem;">No matches found.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        xc = len(missing)
        st.markdown(f"""
        <div class="card" style="border-color:rgba(239,68,68,0.15);">
            <div class="card-title"><span>✕ Missing Keywords</span><span class="pill pill-red">{xc} gaps</span></div>
            <p style="font-size:0.75rem;color:var(--txt-3);margin-bottom:0.85rem;">
                Click any keyword to see a suggested sentence and placement advice.
            </p>""", unsafe_allow_html=True)
        if missing:
            groups = group_keywords(missing)
            for group_name, kws in groups.items():
                st.markdown(f'<div class="kw-group"><div class="kw-group-title">{group_name}</div></div>', unsafe_allow_html=True)
                cols_per_row = 3
                for i in range(0, len(kws), cols_per_row):
                    row_kws = kws[i:i+cols_per_row]
                    cols = st.columns(len(row_kws))
                    for col, kw in zip(cols, row_kws):
                        with col:
                            is_selected = st.session_state.selected_keyword == kw
                            if st.button(f"{'◉' if is_selected else '○'} {kw}",
                                         key=f"kw_{kw.replace(' ','_').replace('/','_')}",
                                         use_container_width=True):
                                st.session_state.selected_keyword = None if is_selected else kw
                                st.rerun()
            sel = st.session_state.selected_keyword
            if sel and sel in missing:
                placement, sentence = get_kw_suggestion(sel)
                placement_chips = "".join(f'<span class="kw-placement-chip">📌 {p.strip()}</span>' for p in placement.split("/"))
                safe_sentence = sentence.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                st.markdown(f"""
                <div class="kw-suggestion-card">
                    <div class="kw-suggestion-label">Keyword: {sel}</div>
                    <div class="kw-suggestion-text">"{safe_sentence}"</div>
                    <div class="kw-placement-chips"><span style="font-family:var(--ff-mono);font-size:0.6rem;color:var(--txt-3);margin-right:0.25rem;">Add to:</span>{placement_chips}</div>
                </div>""", unsafe_allow_html=True)
                st.code(sentence, language=None)
                st.markdown('<p style="font-size:0.7rem;color:var(--txt-3);margin-top:-0.5rem;">↑ Click the copy icon to copy · or use Quick Inject in the Live Loop tab</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:var(--txt-3);font-size:0.82rem;">No critical gaps — well aligned!</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card" style="margin-top:0.75rem;"><div class="card-title">◈ Top Keywords from Job Description</div>', unsafe_allow_html=True)
    if jd_top:
        pills = "".join(f'<span class="pill pill-blue">{kw}</span>' for kw in jd_top)
        st.markdown(f'<div class="pill-row">{pills}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:var(--txt-3);font-size:0.82rem;">No top keywords extracted.</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_tab_suggestions(analysis: dict):
    sugs = _safe_list(analysis.get("suggestions"))
    st.markdown('<p style="font-size:0.85rem;color:var(--txt-2);margin-bottom:1.25rem;">AI-generated action items to boost your ATS compatibility and recruiter appeal.</p>', unsafe_allow_html=True)
    if sugs:
        for i, s in enumerate(sugs, 1):
            st.markdown(f'<div class="sug-item"><span class="sug-num">{i:02d}</span><span>{s}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:var(--txt-3);font-size:0.85rem;">No suggestions — your resume looks well-aligned for this role.</p>', unsafe_allow_html=True)


def render_tab_job_fit(analysis: dict, score: int):
    st.markdown('<p style="font-size:0.85rem;color:var(--txt-2);margin-bottom:1.25rem;">Based on your matched keywords, here are the roles you\'re most competitive for:</p>', unsafe_allow_html=True)
    fits = infer_job_fits(analysis)
    if fits:
        for f in fits:
            style = pct_badge_style(f["pct"])
            st.markdown(f"""
            <div class="fit-row">
                <div><div class="fit-role">{f['role']}</div><div class="fit-co">{f['company']}</div></div>
                <span class="fit-pct" style="{style}">{f['pct']}% fit</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:var(--txt-3);font-size:0.84rem;">Not enough keyword data to infer role fit.</p>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:1.75rem;">', unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")
    with col1:
        sem = _safe_int(analysis.get("semantic_score"), 0)
        kws = _safe_int(analysis.get("keyword_score"),  0)
        fig = go.Figure()
        for cat, val, col in zip(["Semantic","Keywords","Overall ATS"],[sem,kws,score],["#4f8aff","#22d3ee","#10b981"]):
            fig.add_trace(go.Bar(x=[val],y=[cat],orientation="h",marker=dict(color=col,line=dict(width=0)),
                                 text=[f"{val}%"],textposition="inside",insidetextanchor="middle",
                                 textfont=dict(size=11,color="#e2e8f0",family="DM Mono"),showlegend=False))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=160,
                          xaxis=dict(range=[0,100],showgrid=False,zeroline=False,tickfont=dict(color="#475569",size=9)),
                          yaxis=dict(showgrid=False,tickfont=dict(color="#94a3b8",size=11)),
                          margin=dict(t=5,b=5,l=0,r=5),bargap=0.45)
        st.markdown('<div class="card"><div class="card-title">◈ Score Breakdown</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        mn = len(_safe_list(analysis.get("matched_keywords")))
        xn = len(_safe_list(analysis.get("missing_keywords")))
        total = max(mn+xn,1)
        fig2 = go.Figure(go.Pie(values=[max(mn,0),max(xn,0)],labels=["Matched","Missing"],hole=0.65,
                                marker=dict(colors=["#10b981","#ef4444"],line=dict(color="#080b12",width=2)),textinfo="none"))
        fig2.add_annotation(text=f"<b>{mn}/{total}</b>",x=0.5,y=0.55,font=dict(size=20,color="#e2e8f0",family="Fraunces"),showarrow=False)
        fig2.add_annotation(text="keywords",x=0.5,y=0.38,font=dict(size=10,color="#475569",family="DM Mono"),showarrow=False)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=200,
                           margin=dict(t=10,b=10,l=0,r=0),
                           legend=dict(orientation="h",x=0.5,xanchor="center",y=-0.08,font=dict(size=10,color="#94a3b8"),bgcolor="rgba(0,0,0,0)"))
        st.markdown('<div class="card"><div class="card-title">◈ Keyword Coverage</div>', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    sem = _safe_int(analysis.get("semantic_score"),0)
    kws = _safe_int(analysis.get("keyword_score"),0)
    mn  = len(_safe_list(analysis.get("matched_keywords")))
    xn  = len(_safe_list(analysis.get("missing_keywords")))
    cov = int(100*mn/max(mn+xn,1))
    ns  = len(_safe_list(analysis.get("suggestions")))
    rows = [("Overall ATS Readiness",insight_badge(score)),("Semantic Alignment",insight_badge(sem)),
            ("Keyword Match Rate",insight_badge(kws)),("Keyword Coverage Ratio",insight_badge(cov))]
    html = '<div class="card" style="margin-top:0.75rem;"><div class="card-title">◈ Alignment Indicators</div>'
    for label,(lbl,sty) in rows:
        html += f'<div class="insight-row"><span class="insight-label">{label}</span><span class="insight-badge" style="{sty}">{lbl}</span></div>'
    html += f'<div class="insight-row"><span class="insight-label">Improvement Suggestions</span><span class="insight-badge" style="background:var(--blue-dim);color:var(--blue);border:1px solid rgba(79,138,255,0.2);">{ns} action items</span></div></div>'
    st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_tab_optimizer(analysis: dict, score: int, jd_text: str):
    projected = min(100, score + 20)
    missing   = _safe_list(analysis.get("missing_keywords"))
    st.markdown("""
    <div class="card card-accent-purple" style="margin-bottom:1.5rem;">
        <div style="font-family:var(--ff-display);font-weight:700;font-size:1.2rem;color:var(--txt);margin-bottom:0.4rem;">AI Resume Optimizer</div>
        <div style="font-size:0.85rem;color:var(--txt-2);line-height:1.65;max-width:620px;">The backend AI rewrites your resume, tailored to this job description. Keywords integrated naturally · Action verbs strengthened · Achievements quantified.</div>
        <div class="pill-row" style="margin-top:1rem;">
            <span class="pill pill-purple">✦ Keyword Integration</span>
            <span class="pill pill-purple">✦ Action Verbs</span>
            <span class="pill pill-purple">✦ Quantified Impact</span>
            <span class="pill pill-purple">✦ ATS-Optimized Structure</span>
            <span class="pill pill-purple">✦ Professional Summary</span>
        </div>
    </div>""", unsafe_allow_html=True)
    m1,m2,m3 = st.columns(3,gap="medium")
    with m1: st.metric("Current ATS Score",f"{score}/100")
    with m2: st.metric("Projected Score",f"{projected}/100",delta=f"+{projected-score} pts estimated")
    with m3: st.metric("Keyword Gaps",str(len(missing)),delta="→ 0 after optimization",delta_color="inverse")
    st.markdown("<div style='height:1.25rem;'></div>",unsafe_allow_html=True)

    has_result    = bool(st.session_state.optimized_resume)
    is_generating = st.session_state.is_generating
    btn_label     = "↻ Regenerate Resume" if has_result else "✦ Generate Optimized Resume"
    _,gc,_ = st.columns([2,1.5,2])
    with gc:
        gen_btn = st.button(btn_label, use_container_width=True, key="gen_opt", disabled=is_generating)

    if gen_btn and not st.session_state.is_generating:
        rt = st.session_state.get("resume_text_cache","")
        jd = jd_text.strip() if jd_text else ""
        if not rt or not rt.strip():
            st.session_state.opt_error = "Resume text not extracted. Please re-analyze."
        elif not jd or len(jd)<50:
            st.session_state.opt_error = "Job description too short."
        else:
            st.session_state.optimized_resume = None
            st.session_state.opt_error        = None
            st.session_state.is_generating    = True

    if st.session_state.is_generating:
        rt = st.session_state.get("resume_text_cache","")
        jd = jd_text.strip() if jd_text else ""
        with st.spinner("Generating optimized resume via backend AI — 10–30 seconds…"):
            try:
                data   = call_optimize_api(rt, jd)
                result = (data.get("optimized_resume") or data.get("optimized_text") or data.get("result") or data.get("text") or "")
                if result and result.strip():
                    st.session_state.optimized_resume = result
                    st.session_state.opt_timestamp    = datetime.datetime.now().strftime("%d %b %Y · %H:%M:%S")
                    st.session_state.opt_error        = None
                else:
                    st.session_state.opt_error = "Backend returned empty result. Please retry."
            except Exception as exc:
                st.session_state.opt_error = classify_error(exc)
            finally:
                st.session_state.is_generating = False

    st.markdown("<div style='height:1rem;'></div>",unsafe_allow_html=True)
    if st.session_state.opt_error:
        render_alert(st.session_state.opt_error,"err")
    elif st.session_state.optimized_resume:
        opt_text = st.session_state.optimized_resume
        opt_ts   = st.session_state.opt_timestamp or ""
        wc = len(opt_text.split()); lc = opt_text.count("\n")
        safe_text = opt_text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        render_alert(f"Resume optimized · {wc} words · {lc} lines · Generated {opt_ts}","ok")
        st.markdown(f"""
        <div style="background:var(--bg-2);border:1px solid var(--border);border-radius:var(--r-md) var(--r-md) 0 0;padding:0.85rem 1.25rem;display:flex;align-items:center;justify-content:space-between;">
            <span style="font-weight:600;font-size:0.88rem;color:var(--txt);display:flex;align-items:center;gap:0.5rem;">
                ✦ Optimized Resume <span class="pill pill-green" style="font-size:0.58rem;text-transform:uppercase;">AI-Generated</span>
            </span>
            <span style="font-family:var(--ff-mono);font-size:0.6rem;color:var(--txt-3);">Backend LLM</span>
        </div>
        <div class="opt-output" style="border-radius:0 0 var(--r-md) var(--r-md);border-top:none;">{safe_text}</div>""",
        unsafe_allow_html=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        dl1,dl2,dl3,_ = st.columns([1,1,1,2])
        with dl1: st.download_button("↓ .txt",opt_text,file_name=f"optimized_{ts}.txt",mime="text/plain",use_container_width=True,key="dl_txt")
        with dl2:
            bundle={"generated_at":opt_ts,"original_ats":score,"projected_ats":projected,"optimized_resume":opt_text,"gaps_addressed":missing}
            st.download_button("↓ .json",json.dumps(bundle,indent=2),file_name=f"optimized_{ts}.json",mime="application/json",use_container_width=True,key="dl_json")
        with dl3:
            md=f"# Optimized Resume\n_Generated {opt_ts}_\n\n---\n\n{opt_text}"
            st.download_button("↓ .md",md,file_name=f"optimized_{ts}.md",mime="text/markdown",use_container_width=True,key="dl_md")
    else:
        st.markdown(f"""
        <div style="background:var(--bg-1);border:1.5px dashed var(--border);border-radius:var(--r-xl);padding:3rem 2rem;text-align:center;margin-top:0.5rem;">
            <span style="font-size:2rem;display:block;margin-bottom:1rem;opacity:0.12;">✦</span>
            <div style="font-family:var(--ff-display);font-weight:700;font-size:0.95rem;color:var(--txt-3);margin-bottom:0.5rem;">Your optimized resume will appear here</div>
            <div style="margin-top:1.5rem;display:flex;justify-content:center;gap:1rem;flex-wrap:wrap;">
                <span class="pill pill-blue">Current: {score}/100</span>
                <span class="pill pill-green">Target: ~{projected}/100</span>
            </div>
        </div>""", unsafe_allow_html=True)


def render_tab_chat(analysis: dict, jd_text: str):
    st.markdown('<p style="font-size:0.85rem;color:var(--txt-2);margin-bottom:1.25rem;">Ask anything about your resume, missing skills, or how to improve for this specific role.</p>', unsafe_allow_html=True)
    PROMPTS = ["How can I improve my resume for this role?","What skills am I missing?","Rewrite my summary for FAANG","What are my strongest sections?","How do I pass ATS for this JD?"]
    cols = st.columns(len(PROMPTS))
    selected_prompt = None
    for i,(col,p) in enumerate(zip(cols,PROMPTS)):
        with col:
            if st.button(p[:30]+"…" if len(p)>30 else p, key=f"qp_{i}", use_container_width=True):
                selected_prompt = p

    chat_html = '<div class="chat-messages">'
    if not st.session_state.chat_history:
        chat_html += '<div class="chat-msg-ai"><div class="chat-msg-label lbl-ai">Career Copilot</div>Hi! I\'ve analyzed your resume. Ask me anything about improving keywords, sections, or positioning for this role.</div>'
    else:
        for msg in st.session_state.chat_history:
            rc = "chat-msg-user" if msg["role"]=="user" else "chat-msg-ai"
            lc = "lbl-user" if msg["role"]=="user" else "lbl-ai"
            lt = "You" if msg["role"]=="user" else "Career Copilot"
            chat_html += f'<div class="{rc}"><div class="chat-msg-label {lc}">{lt}</div>{msg["content"]}</div>'
    chat_html += '</div>'
    st.markdown(f'<div class="chat-wrap">{chat_html}</div>', unsafe_allow_html=True)

    user_input = st.text_input("Ask Career Copilot…", key="chat_input",
                                placeholder="e.g. 'What skills should I add for this ML role?'",
                                label_visibility="collapsed")
    send_input = selected_prompt or (user_input if user_input else None)

    if send_input:
        context = f"""You are Career Copilot, an expert AI career advisor.
ATS Score: {analysis.get('ats_score','N/A')}/100
Semantic Score: {analysis.get('semantic_score','N/A')}%
Matched Keywords: {', '.join(_safe_list(analysis.get('matched_keywords'))[:15])}
Missing Keywords: {', '.join(_safe_list(analysis.get('missing_keywords'))[:15])}
Suggestions: {'; '.join(_safe_list(analysis.get('suggestions'))[:5])}
JD snippet: {jd_text[:400] if jd_text else 'Not provided'}
Answer concisely and actionably. Reference the actual data above."""
        with st.spinner("Career Copilot is thinking…"):
            try:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"Content-Type":"application/json"},
                    json={"model":"claude-sonnet-4-20250514","max_tokens":600,"system":context,
                          "messages":[*[{"role":m["role"],"content":m["content"]} for m in st.session_state.chat_history[-6:]],
                                      {"role":"user","content":send_input}]},
                    timeout=30)
                data = resp.json()
                ai_reply = data.get("content",[{}])[0].get("text","I couldn't generate a response.")
            except Exception:
                ai_reply = "I'm having trouble connecting right now. Please retry."
        st.session_state.chat_history.append({"role":"user","content":send_input})
        st.session_state.chat_history.append({"role":"assistant","content":ai_reply})
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR + HERO + INPUT
# ══════════════════════════════════════════════════════════════════════════════
def render_topbar():
    ok = st.session_state.backend_ok
    if ok is None:
        ok = check_backend_health()
        st.session_state.backend_ok = ok
    health_html = '<span class="dot-live"></span>Backend Live' if ok else '<span style="color:var(--red)">✕ Backend Offline</span>'
    st.markdown(f"""
    <div class="copilot-topbar">
        <div class="copilot-brand">
            <div class="copilot-logo">✦</div>
            <span class="copilot-wordmark">Career<em>Copilot</em></span>
        </div>
        <div style="display:flex;align-items:center;gap:0.75rem;">
            <span class="copilot-status">{health_html}</span>
            <span class="copilot-status">AI Resume Intelligence · v2.2</span>
        </div>
    </div>""", unsafe_allow_html=True)


def render_hero():
    count = st.session_state.analysis_count
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-label">✦ AI-Powered · TF-IDF + Semantic NLP + LLM</div>
        <h1 class="hero-title">Your AI-powered<br><span>career intelligence</span><br>copilot</h1>
        <p class="hero-sub">Analyze · edit · re-score · repeat. Get your resume to a Strong Match before you apply.</p>
        <div class="hero-stats">
            <div><div class="hero-stat-val">5</div><div class="hero-stat-lbl">Analysis Dimensions</div></div>
            <div><div class="hero-stat-val">AI</div><div class="hero-stat-lbl">Resume Optimizer</div></div>
            <div><div class="hero-stat-val">{'∞' if count == 0 else count}</div><div class="hero-stat-lbl">{'Iterations' if count == 0 else 'Analyses This Session'}</div></div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_input_section():
    st.markdown('<div class="content-pad">', unsafe_allow_html=True)
    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        st.markdown("""
        <div class="input-panel"><div class="input-panel-top">
            <div class="panel-icon">📄</div>
            <div><div class="panel-label">Resume</div><div class="panel-sublabel">PDF · Max 10 MB · Text-layer only</div></div>
        </div><div class="panel-body">""", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(label="resume_upload", label_visibility="collapsed", type=["pdf"])
        if uploaded_file:
            kb = round(uploaded_file.size/1024,1)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.6rem;margin-top:0.6rem;padding:0.55rem 0.85rem;
                 background:var(--green-dim);border:1px solid var(--green-glow);border-radius:var(--r-sm);">
                <span style="color:var(--green);">✓</span>
                <span style="font-family:var(--ff-mono);font-size:0.72rem;color:var(--green);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{uploaded_file.name}</span>
                <span style="font-family:var(--ff-mono);font-size:0.62rem;color:var(--txt-3);">{kb} KB</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    with col_r:
        st.markdown("""
        <div class="input-panel"><div class="input-panel-top">
            <div class="panel-icon">🎯</div>
            <div><div class="panel-label">Job Description</div><div class="panel-sublabel">Minimum 50 characters</div></div>
        </div><div class="panel-body">""", unsafe_allow_html=True)
        jd_text = st.text_area(label="jd_input", label_visibility="collapsed",
                               placeholder="Paste the full job description here…",
                               height=180, key="jd_textarea")
        n  = len(jd_text) if jd_text else 0
        ok = n >= 50
        cc = "var(--green)" if ok else ("var(--amber)" if n>0 else "var(--txt-3)")
        cl = "Ready ✓" if ok else f"{max(0,50-n)} chars needed"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.4rem;padding-top:0.4rem;border-top:1px solid var(--border);">
            <span style="font-family:var(--ff-mono);font-size:0.58rem;letter-spacing:0.1em;text-transform:uppercase;color:var(--txt-3);">Plain text · no formatting</span>
            <span style="font-family:var(--ff-mono);font-size:0.63rem;color:{cc};">{n} chars · {cl}</span>
        </div></div></div>""", unsafe_allow_html=True)

    st.markdown('<div style="margin-top:1.5rem;">', unsafe_allow_html=True)
    _,btn_c,_ = st.columns([2,1.4,2])
    with btn_c:
        analyze_btn = st.button("Analyze Resume →", use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)
    return uploaded_file, jd_text, analyze_btn


def render_export_bar(analysis: dict, score: int, grade_label: str, timestamp: str):
    matched = _safe_list(analysis.get("matched_keywords"))
    missing = _safe_list(analysis.get("missing_keywords"))
    jd_top  = _safe_list(analysis.get("jd_top_keywords"))
    sugs    = _safe_list(analysis.get("suggestions"))
    report  = {"generated_at":timestamp,"ats_score":score,"grade":grade_label,
               "semantic_score":_safe_int(analysis.get("semantic_score"),0),
               "keyword_score":_safe_int(analysis.get("keyword_score"),0),
               "matched_keywords":matched,"missing_keywords":missing,"jd_top_keywords":jd_top,"suggestions":sugs}
    st.markdown("""
    <div style="background:var(--bg-1);border:1px solid var(--border);border-radius:var(--r-xl);
         padding:1.25rem 1.5rem;display:flex;align-items:center;gap:0.75rem;">
        <div style="width:36px;height:36px;background:var(--blue-dim);border:1px solid rgba(79,138,255,0.2);
             border-radius:8px;display:flex;align-items:center;justify-content:center;">↓</div>
        <div>
            <div style="font-weight:600;font-size:0.88rem;color:var(--txt);">Export Analysis Report</div>
            <div style="font-size:0.73rem;color:var(--txt-3);margin-top:0.1rem;">Full results for sharing or reference</div>
        </div>
    </div>""", unsafe_allow_html=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    ec1,ec2,_ = st.columns([1,1,4])
    with ec1:
        st.download_button("↓ JSON Report",json.dumps(report,indent=2),file_name=f"copilot_report_{ts}.json",mime="application/json",use_container_width=True)
    with ec2:
        txt="\n".join(["Career Copilot — Analysis Report",f"Generated: {timestamp}","="*40,
                       f"ATS Score: {score}/100 ({grade_label})",
                       f"Semantic:  {_safe_int(analysis.get('semantic_score'),0)}%",
                       f"Keywords:  {_safe_int(analysis.get('keyword_score'),0)}%",
                       "","MATCHED",", ".join(matched),"","MISSING",", ".join(missing),
                       "","SUGGESTIONS",*[f"{i}. {s}" for i,s in enumerate(sugs,1)]])
        st.download_button("↓ TXT Report",txt,file_name=f"copilot_report_{ts}.txt",mime="text/plain",use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()
    init_state()
    render_topbar()
    render_hero()

    uploaded_file, jd_text, analyze_btn = render_input_section()
    st.markdown('<div class="content-pad">', unsafe_allow_html=True)

    if analyze_btn:
        errors = []
        if not uploaded_file:  errors.append("Please upload a PDF resume.")
        if not jd_text or len(jd_text.strip()) < 50: errors.append("Please paste a job description (min 50 chars).")
        if errors:
            for e in errors: render_alert(e, "warn")
        else:
            try:
                pdf_bytes = uploaded_file.read()
                update_score_history(0)
                parsed = run_analysis_with_stages(pdf_bytes, uploaded_file.name, jd_text.strip())
                st.session_state.analysis_result   = parsed
                st.session_state.resume_text_cache = parsed.get("resume_text","")
                # Seed / reset live editor
                st.session_state.live_resume_text  = parsed.get("resume_text","")
                st.session_state.live_rescore_result      = None
                st.session_state.live_rescore_prev_score  = None
                st.session_state.score_history     = []
                _record_loop_entry(_safe_int(parsed.get("ats_score"),0), None)
                # Reset others
                st.session_state.chat_history      = []
                st.session_state.selected_keyword  = None
                st.session_state.optimized_resume  = None
                st.session_state.opt_error         = None
                st.session_state.is_generating     = False
                st.rerun()
            except (requests.ConnectionError, requests.ConnectTimeout) as exc:
                render_alert(classify_error(exc), "err"); st.stop()
            except (ValueError, RuntimeError) as exc:
                render_alert(str(exc), "err"); st.stop()
            except Exception as exc:
                render_alert(f"Unexpected error: {exc}", "err"); st.stop()

    analysis = st.session_state.get("analysis_result")

    if analysis is not None:
        score      = _safe_int(analysis.get("ats_score"), 0)
        g_label, _ = grade_tag(score)
        timestamp  = datetime.datetime.now().strftime("%d %b %Y · %H:%M")
        count      = st.session_state.analysis_count
        loop_iters = len(st.session_state.score_history)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="section-hdr">
            <span class="section-title">Intelligence Report</span>
            <div style="display:flex;align-items:center;gap:0.75rem;">
                <span class="copilot-status" style="font-size:0.6rem;">Analysis #{count}</span>
                {'<span class="copilot-status" style="font-size:0.6rem;background:var(--blue-dim);border-color:rgba(79,138,255,0.2);color:var(--blue);">⚡ ' + str(loop_iters) + ' loop iterations</span>' if loop_iters > 1 else ''}
                <span style="font-family:var(--ff-mono);font-size:0.63rem;color:var(--txt-3);">Generated {timestamp}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "  🎯 Decision Engine  ",
            "  🔑 Keywords  ",
            "  💡 Suggestions  ",
            "  📊 Job Fit  ",
            "  ✨ Optimizer  ",
            "  ⚡ Live Loop  ",   # ← NEW
            "  💬 Copilot Chat  ",
        ])

        with tab1: render_tab_decision(analysis, score)
        with tab2: render_tab_keywords(analysis)
        with tab3: render_tab_suggestions(analysis)
        with tab4: render_tab_job_fit(analysis, score)
        with tab5: render_tab_optimizer(analysis, score, jd_text)
        with tab6: render_tab_live_loop(analysis, jd_text)   # ← NEW
        with tab7: render_tab_chat(analysis, jd_text)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        render_export_bar(analysis, score, g_label, timestamp)

    elif not analyze_btn:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-icon">◈</span>
            <div class="empty-title">Your intelligence report will appear here</div>
            <p class="empty-sub">Upload a PDF resume and paste a job description above, then click Analyze Resume.</p>
            <div class="empty-steps">
                <div class="empty-step"><span class="empty-num">01</span>Upload PDF</div>
                <span class="empty-arrow">→</span>
                <div class="empty-step"><span class="empty-num">02</span>Paste JD</div>
                <span class="empty-arrow">→</span>
                <div class="empty-step"><span class="empty-num">03</span>Analyze</div>
                <span class="empty-arrow">→</span>
                <div class="empty-step"><span class="empty-num">04</span>Live Loop</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()