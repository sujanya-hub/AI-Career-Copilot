"""
database/repositories.py
Enterprise Repository Layer — save_analysis(), save_optimized_resume(),
get_user_history() with full persistence abstraction.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from loguru import logger


# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "resumeiq.db"


# ─── Schema ───────────────────────────────────────────────────────────────────

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS analyses (
    id              TEXT PRIMARY KEY,
    user_id         TEXT,
    session_id      TEXT,
    created_at      TEXT NOT NULL,
    ats_score       INTEGER NOT NULL,
    grade           TEXT NOT NULL,
    semantic_score  INTEGER,
    keyword_score   INTEGER,
    matched_count   INTEGER,
    missing_count   INTEGER,
    suggestions_json TEXT,
    matched_kws_json TEXT,
    missing_kws_json TEXT,
    resume_snippet  TEXT,
    jd_snippet      TEXT,
    provider        TEXT DEFAULT 'local',
    meta_json       TEXT
);

CREATE TABLE IF NOT EXISTS optimized_resumes (
    id              TEXT PRIMARY KEY,
    analysis_id     TEXT,
    user_id         TEXT,
    session_id      TEXT,
    created_at      TEXT NOT NULL,
    original_score  INTEGER,
    projected_score INTEGER,
    optimized_text  TEXT NOT NULL,
    model_provider  TEXT,
    model_id        TEXT,
    tokens_used     INTEGER,
    latency_ms      INTEGER,
    word_count      INTEGER,
    missing_kws_addressed_json TEXT
);

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id      TEXT PRIMARY KEY,
    user_id         TEXT,
    created_at      TEXT NOT NULL,
    last_active     TEXT NOT NULL,
    analysis_count  INTEGER DEFAULT 0,
    optimize_count  INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_analyses_user     ON analyses(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_session  ON analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_opt_analysis      ON optimized_resumes(analysis_id);
CREATE INDEX IF NOT EXISTS idx_opt_user          ON optimized_resumes(user_id, created_at);
"""


# ─── Data objects ─────────────────────────────────────────────────────────────

@dataclass
class AnalysisRecord:
    id:              str
    user_id:         Optional[str]
    session_id:      Optional[str]
    created_at:      str
    ats_score:       int
    grade:           str
    semantic_score:  int
    keyword_score:   int
    matched_count:   int
    missing_count:   int
    suggestions:     List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    resume_snippet:  str
    jd_snippet:      str
    provider:        str = "local"
    meta:            Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizedResumeRecord:
    id:              str
    analysis_id:     str
    user_id:         Optional[str]
    session_id:      Optional[str]
    created_at:      str
    original_score:  int
    projected_score: int
    optimized_text:  str
    model_provider:  str
    model_id:        str
    tokens_used:     Optional[int]
    latency_ms:      Optional[int]
    word_count:      int
    missing_kws_addressed: List[str]


@dataclass
class UserHistoryEntry:
    analysis_id:     str
    created_at:      str
    ats_score:       int
    grade:           str
    jd_snippet:      str
    has_optimization: bool


# ─── Base repository ──────────────────────────────────────────────────────────

class BaseRepository:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_CREATE_TABLES)
        logger.debug("Repository: DB ready at {}", self._db_path)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _new_id() -> str:
        return str(uuid.uuid4())


# ─── Analysis repository ──────────────────────────────────────────────────────

class AnalysisRepository(BaseRepository):
    """Persists and retrieves resume analysis results."""

    def save_analysis(
        self,
        ats_score:       int,
        grade:           str,
        semantic_score:  int,
        keyword_score:   int,
        matched_keywords: List[str],
        missing_keywords: List[str],
        suggestions:     List[str],
        resume_text:     str,
        jd_text:         str,
        user_id:         Optional[str] = None,
        session_id:      Optional[str] = None,
        meta:            Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist a completed analysis. Returns the new analysis ID."""
        analysis_id = self._new_id()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO analyses (
                    id, user_id, session_id, created_at,
                    ats_score, grade, semantic_score, keyword_score,
                    matched_count, missing_count,
                    suggestions_json, matched_kws_json, missing_kws_json,
                    resume_snippet, jd_snippet, meta_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    analysis_id, user_id, session_id, self._now(),
                    ats_score, grade, semantic_score, keyword_score,
                    len(matched_keywords), len(missing_keywords),
                    json.dumps(suggestions),
                    json.dumps(matched_keywords),
                    json.dumps(missing_keywords),
                    resume_text[:500],
                    jd_text[:500],
                    json.dumps(meta or {}),
                ),
            )
        logger.info("AnalysisRepository: saved analysis {} score={}", analysis_id, ats_score)
        self._update_session_stats(session_id, "analysis_count")
        return analysis_id

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_analysis(row)

    def get_recent_analyses(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[AnalysisRecord]:
        if user_id:
            query = "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"
            params = (user_id, limit)
        elif session_id:
            query = "SELECT * FROM analyses WHERE session_id = ? ORDER BY created_at DESC LIMIT ?"
            params = (session_id, limit)
        else:
            return []

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_analysis(r) for r in rows]

    def delete_analysis(self, analysis_id: str) -> bool:
        with self._connect() as conn:
            result = conn.execute(
                "DELETE FROM analyses WHERE id = ?", (analysis_id,)
            )
        return result.rowcount > 0

    @staticmethod
    def _row_to_analysis(row: sqlite3.Row) -> AnalysisRecord:
        return AnalysisRecord(
            id=row["id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            created_at=row["created_at"],
            ats_score=row["ats_score"],
            grade=row["grade"],
            semantic_score=row["semantic_score"] or 0,
            keyword_score=row["keyword_score"] or 0,
            matched_count=row["matched_count"] or 0,
            missing_count=row["missing_count"] or 0,
            suggestions=json.loads(row["suggestions_json"] or "[]"),
            matched_keywords=json.loads(row["matched_kws_json"] or "[]"),
            missing_keywords=json.loads(row["missing_kws_json"] or "[]"),
            resume_snippet=row["resume_snippet"] or "",
            jd_snippet=row["jd_snippet"] or "",
            provider=row["provider"] or "local",
            meta=json.loads(row["meta_json"] or "{}"),
        )


# ─── Optimized resume repository ─────────────────────────────────────────────

class OptimizedResumeRepository(BaseRepository):
    """Persists and retrieves AI-optimized resumes."""

    def save_optimized_resume(
        self,
        analysis_id:         str,
        original_score:      int,
        projected_score:     int,
        optimized_text:      str,
        missing_kws_addressed: List[str],
        model_provider:      str = "groq",
        model_id:            str = "llama3-70b-8192",
        tokens_used:         Optional[int] = None,
        latency_ms:          Optional[int] = None,
        user_id:             Optional[str] = None,
        session_id:          Optional[str] = None,
    ) -> str:
        """Persist an optimized resume. Returns the record ID."""
        record_id  = self._new_id()
        word_count = len(optimized_text.split())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO optimized_resumes (
                    id, analysis_id, user_id, session_id, created_at,
                    original_score, projected_score, optimized_text,
                    model_provider, model_id, tokens_used, latency_ms,
                    word_count, missing_kws_addressed_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record_id, analysis_id, user_id, session_id, self._now(),
                    original_score, projected_score, optimized_text,
                    model_provider, model_id, tokens_used, latency_ms,
                    word_count, json.dumps(missing_kws_addressed),
                ),
            )
        logger.info("OptimizedResumeRepository: saved {} words={}", record_id, word_count)
        self._update_session_stats(session_id, "optimize_count")
        return record_id

    def get_for_analysis(self, analysis_id: str) -> Optional[OptimizedResumeRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM optimized_resumes WHERE analysis_id = ? ORDER BY created_at DESC LIMIT 1",
                (analysis_id,),
            ).fetchone()
        return self._row_to_opt(row) if row else None

    def get_recent_optimized(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[OptimizedResumeRecord]:
        if user_id:
            query = "SELECT * FROM optimized_resumes WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"
            params = (user_id, limit)
        elif session_id:
            query = "SELECT * FROM optimized_resumes WHERE session_id = ? ORDER BY created_at DESC LIMIT ?"
            params = (session_id, limit)
        else:
            return []

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_opt(r) for r in rows]

    @staticmethod
    def _row_to_opt(row: sqlite3.Row) -> OptimizedResumeRecord:
        return OptimizedResumeRecord(
            id=row["id"],
            analysis_id=row["analysis_id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            created_at=row["created_at"],
            original_score=row["original_score"],
            projected_score=row["projected_score"],
            optimized_text=row["optimized_text"],
            model_provider=row["model_provider"],
            model_id=row["model_id"],
            tokens_used=row["tokens_used"],
            latency_ms=row["latency_ms"],
            word_count=row["word_count"],
            missing_kws_addressed=json.loads(row["missing_kws_addressed_json"] or "[]"),
        )


# ─── User history repository ─────────────────────────────────────────────────

class UserHistoryRepository(BaseRepository):
    """Aggregated user history queries."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        super().__init__(db_path)
        self._analysis_repo  = AnalysisRepository(db_path)
        self._optimized_repo = OptimizedResumeRepository(db_path)

    def get_user_history(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[UserHistoryEntry]:
        """
        Returns paginated history with basic metadata + optimization status.
        """
        analyses  = self._analysis_repo.get_recent_analyses(user_id, session_id, limit)
        opt_ids   = {
            r.analysis_id
            for r in self._optimized_repo.get_recent_optimized(user_id, session_id, limit)
        }
        return [
            UserHistoryEntry(
                analysis_id=a.id,
                created_at=a.created_at,
                ats_score=a.ats_score,
                grade=a.grade,
                jd_snippet=a.jd_snippet[:120] + "…" if len(a.jd_snippet) > 120 else a.jd_snippet,
                has_optimization=a.id in opt_ids,
            )
            for a in analyses
        ]

    def get_score_trend(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Returns chronological score data for trend charts."""
        analyses = self._analysis_repo.get_recent_analyses(user_id, session_id, limit)
        return [
            {
                "date":     a.created_at[:10],
                "score":    a.ats_score,
                "grade":    a.grade,
                "analysis_id": a.id,
            }
            for a in reversed(analyses)
        ]

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM user_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if not row:
            return None
        return {
            "session_id":      row["session_id"],
            "analysis_count":  row["analysis_count"],
            "optimize_count":  row["optimize_count"],
            "created_at":      row["created_at"],
            "last_active":     row["last_active"],
        }

    def _update_session_stats(self, session_id: Optional[str], counter: str) -> None:
        if not session_id:
            return
        now = self._now()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT session_id FROM user_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    f"UPDATE user_sessions SET {counter} = {counter} + 1, last_active = ? "
                    f"WHERE session_id = ?",
                    (now, session_id),
                )
            else:
                init = {"analysis_count": 0, "optimize_count": 0}
                init[counter] = 1
                conn.execute(
                    "INSERT INTO user_sessions (session_id, created_at, last_active, analysis_count, optimize_count) "
                    "VALUES (?,?,?,?,?)",
                    (session_id, now, now, init["analysis_count"], init["optimize_count"]),
                )