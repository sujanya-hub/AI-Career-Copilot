"""
configs/settings.py
Centralized configuration management.
Loads from environment variables + .env file with typed defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from loguru import logger


# ─── Try to load .env if present ─────────────────────────────────────────────

def _load_dotenv() -> None:
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        logger.debug("Settings: loaded .env from {}", env_file)
    except Exception as exc:
        logger.warning("Settings: could not load .env: {}", exc)


_load_dotenv()


# ─── Config dataclasses ──────────────────────────────────────────────────────

@dataclass
class AIConfig:
    # Groq
    groq_api_key:        Optional[str] = field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    groq_model:          str           = field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama3-70b-8192"))
    groq_max_tokens:     int           = field(default_factory=lambda: int(os.getenv("GROQ_MAX_TOKENS", "4096")))
    groq_temperature:    float         = field(default_factory=lambda: float(os.getenv("GROQ_TEMPERATURE", "0.4")))

    # OpenAI (fallback)
    openai_api_key:      Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model:        str           = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_max_tokens:   int           = field(default_factory=lambda: int(os.getenv("OPENAI_MAX_TOKENS", "4096")))

    # Common
    ai_timeout_seconds:  int           = field(default_factory=lambda: int(os.getenv("AI_TIMEOUT", "60")))
    ai_max_retries:      int           = field(default_factory=lambda: int(os.getenv("AI_MAX_RETRIES", "3")))
    enable_streaming:    bool          = field(default_factory=lambda: os.getenv("AI_STREAMING", "true").lower() == "true")
    preferred_provider:  str           = field(default_factory=lambda: os.getenv("AI_PROVIDER", "groq"))

    @property
    def groq_available(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def openai_available(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def any_ai_available(self) -> bool:
        return self.groq_available or self.openai_available


@dataclass
class DatabaseConfig:
    db_url:              str  = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    db_path:             str  = field(default_factory=lambda: os.getenv("DB_PATH", "data/resumeiq.db"))
    pool_size:           int  = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5")))
    echo_sql:            bool = field(default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true")
    run_migrations:      bool = field(default_factory=lambda: os.getenv("RUN_MIGRATIONS", "true").lower() == "true")

    @property
    def resolved_path(self) -> Path:
        return Path(self.db_path)


@dataclass
class SecurityConfig:
    jwt_secret:          str  = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-secret-change-in-production"))
    jwt_algorithm:       str  = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_expiry_seconds:  int  = field(default_factory=lambda: int(os.getenv("JWT_EXPIRY", "3600")))
    allowed_origins:     List[str] = field(default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(","))
    enable_auth:         bool = field(default_factory=lambda: os.getenv("ENABLE_AUTH", "false").lower() == "true")

    @property
    def is_production_secret(self) -> bool:
        return self.jwt_secret != "dev-secret-change-in-production"


@dataclass
class RateLimitConfig:
    analyze_rpm:         int  = field(default_factory=lambda: int(os.getenv("RATE_ANALYZE_RPM", "20")))
    optimize_rpm:        int  = field(default_factory=lambda: int(os.getenv("RATE_OPTIMIZE_RPM", "5")))
    upload_rpm:          int  = field(default_factory=lambda: int(os.getenv("RATE_UPLOAD_RPM", "30")))
    global_rpm:          int  = field(default_factory=lambda: int(os.getenv("RATE_GLOBAL_RPM", "60")))
    enable_rate_limiting: bool = field(default_factory=lambda: os.getenv("ENABLE_RATE_LIMIT", "true").lower() == "true")


@dataclass
class LoggingConfig:
    level:               str  = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format:              str  = field(default_factory=lambda: os.getenv("LOG_FORMAT", "json"))
    log_file:            Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))
    rotation:            str  = field(default_factory=lambda: os.getenv("LOG_ROTATION", "100 MB"))
    retention:           str  = field(default_factory=lambda: os.getenv("LOG_RETENTION", "30 days"))
    enable_request_log:  bool = field(default_factory=lambda: os.getenv("LOG_REQUESTS", "true").lower() == "true")


@dataclass
class FileConfig:
    max_upload_mb:       int  = field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_MB", "10")))
    allowed_extensions:  List[str] = field(default_factory=lambda: [".pdf"])
    upload_temp_dir:     str  = field(default_factory=lambda: os.getenv("UPLOAD_TEMP_DIR", "/tmp/resumeiq"))

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@dataclass
class FeatureFlags:
    enable_history:      bool = field(default_factory=lambda: os.getenv("FEATURE_HISTORY", "true").lower() == "true")
    enable_comparison:   bool = field(default_factory=lambda: os.getenv("FEATURE_COMPARISON", "true").lower() == "true")
    enable_cover_letter: bool = field(default_factory=lambda: os.getenv("FEATURE_COVER_LETTER", "false").lower() == "true")
    enable_interview_q:  bool = field(default_factory=lambda: os.getenv("FEATURE_INTERVIEW_Q", "false").lower() == "true")
    enable_job_search:   bool = field(default_factory=lambda: os.getenv("FEATURE_JOB_SEARCH", "false").lower() == "true")
    debug_mode:          bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")


# ─── Master settings ──────────────────────────────────────────────────────────

@dataclass
class Settings:
    ai:           AIConfig        = field(default_factory=AIConfig)
    database:     DatabaseConfig  = field(default_factory=DatabaseConfig)
    security:     SecurityConfig  = field(default_factory=SecurityConfig)
    rate_limit:   RateLimitConfig = field(default_factory=RateLimitConfig)
    logging:      LoggingConfig   = field(default_factory=LoggingConfig)
    files:        FileConfig      = field(default_factory=FileConfig)
    features:     FeatureFlags    = field(default_factory=FeatureFlags)

    app_name:     str = "ResumeIQ"
    app_version:  str = "2.0.0"
    environment:  str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    def validate(self) -> List[str]:
        """Return a list of critical configuration warnings."""
        warnings: List[str] = []
        if not self.ai.any_ai_available:
            warnings.append("No AI API keys configured — AI optimization will be disabled.")
        if not self.security.is_production_secret and self.is_production:
            warnings.append("JWT secret is using the default dev value in production!")
        if self.database.echo_sql and self.is_production:
            warnings.append("SQL echo is enabled in production — disable for performance.")
        if self.features.debug_mode and self.is_production:
            warnings.append("Debug mode is enabled in production.")
        return warnings

    def log_startup(self) -> None:
        logger.info(
            "Settings loaded | app={} version={} env={} ai_provider={} ai_available={}",
            self.app_name,
            self.app_version,
            self.environment,
            self.ai.preferred_provider,
            self.ai.any_ai_available,
        )
        for warning in self.validate():
            logger.warning("⚠ Config warning: {}", warning)


# ─── Module-level singleton ────────────────────────────────────────────────────

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Force re-load settings (useful in tests)."""
    global _settings
    _settings = None