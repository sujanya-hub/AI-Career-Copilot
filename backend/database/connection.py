"""
SQLAlchemy database connection layer.
Provides SQLite engine, session management, ORM models, and get_db() dependency.
"""

import os
from datetime import datetime
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from configs.logging_config import get_logger

logger = get_logger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "resume_analyzer.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# ── Engine & Session Factory ──────────────────────────────────────────────

os.makedirs(DB_DIR, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,                                  # Set True to log all SQL queries
    pool_pre_ping=True,                          # Validate connections before use
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ── ORM Models ────────────────────────────────────────────────────────────

class AnalysisResult(Base):
    """
    Stores each resume analysis result for history retrieval.
    """
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resume_snippet = Column(String(300), nullable=False)
    job_description_snippet = Column(String(300), nullable=False)
    ats_score = Column(Float, nullable=False, default=0.0)
    matched_keywords = Column(Text, nullable=True)
    missing_keywords = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<AnalysisResult id={self.id} "
            f"ats_score={self.ats_score} "
            f"created_at={self.created_at}>"
        )


# ── Database Initialization ───────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables defined in the ORM models.
    Safe to call multiple times — won't drop existing data.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables created/verified at: {os.path.abspath(DB_PATH)}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


# ── FastAPI Dependency ────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per request,
    and ensures it is closed after the request completes.

    Usage in endpoint:
        @app.get("/route")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        logger.debug("DB session opened.")
        yield db
        db.commit()
        logger.debug("DB session committed.")
    except Exception as e:
        db.rollback()
        logger.warning(f"DB session rolled back due to error: {e}")
        raise
    finally:
        db.close()
        logger.debug("DB session closed.")


# ── Context Manager (non-FastAPI use) ─────────────────────────────────────

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for using DB sessions outside of FastAPI
    (e.g., scripts, tests, background tasks).

    Usage:
        with get_db_context() as db:
            db.query(AnalysisResult).all()
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Context manager DB rollback: {e}")
        raise
    finally:
        db.close()