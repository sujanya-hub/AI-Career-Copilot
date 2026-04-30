"""
Centralized logging configuration using Loguru.
Provides console + rotating file logging with clean formatting.
"""

import sys
import os
from loguru import logger

# ── Constants ────────────────────────────────────────────────────────────────

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "resume_analyzer.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)

# ── Setup ────────────────────────────────────────────────────────────────────

def setup_logging() -> None:
    """
    Configure Loguru with:
    - Colored console output
    - Rotating file output (10 MB per file, 7-day retention)
    - Clean, readable format for both sinks
    """
    # Remove default Loguru handler
    logger.remove()

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Console sink — colored, human-readable
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format=CONSOLE_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=False,
    )

    # File sink — rotating, plain text
    logger.add(
        LOG_FILE,
        level="DEBUG",
        format=FILE_FORMAT,
        rotation="10 MB",        # Rotate when file hits 10 MB
        retention="7 days",      # Keep logs for 7 days
        compression="zip",       # Compress rotated files
        backtrace=True,
        diagnose=True,
        enqueue=True,            # Thread-safe async writing
        encoding="utf-8",
    )

    logger.info(
        f"Logging initialized — level={LOG_LEVEL}, "
        f"file={os.path.abspath(LOG_FILE)}"
    )


def get_logger(name: str):
    """
    Return a contextualized Loguru logger bound to a module name.

    Usage:
        from configs.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Hello!")
    """
    return logger.bind(module=name)


# ── Auto-initialize on import ─────────────────────────────────────────────

setup_logging()