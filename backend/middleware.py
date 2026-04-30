"""
backend/middleware.py
Enterprise Middleware Layer — structured logging, JWT auth, request tracing,
global exception handling, and CORS for the ResumeIQ backend.
"""

from __future__ import annotations

import functools
import time
import traceback
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, Optional

from loguru import logger


# ─── Request context ──────────────────────────────────────────────────────────

class RequestContext:
    """
    Lightweight per-request context object.
    Attach to each incoming request for tracing and logging correlation.
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint: str = "unknown",
        ip_address: Optional[str] = None,
    ) -> None:
        self.request_id  = request_id or str(uuid.uuid4())
        self.user_id     = user_id
        self.endpoint    = endpoint
        self.ip_address  = ip_address
        self.started_at  = time.monotonic()
        self._extras: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._extras[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._extras.get(key, default)

    @property
    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.started_at) * 1000)

    def log_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id":    self.user_id,
            "endpoint":   self.endpoint,
            "ip":         self.ip_address,
            "elapsed_ms": self.elapsed_ms,
            **self._extras,
        }


# ─── Logging middleware ───────────────────────────────────────────────────────

class LoggingMiddleware:
    """
    Structured request/response logging middleware.
    Logs request entry, exit, and any exceptions with correlation IDs.
    """

    def log_request(self, ctx: RequestContext, **kwargs) -> None:
        logger.info(
            "→ REQUEST | rid={} endpoint={} user={} ip={}",
            ctx.request_id, ctx.endpoint, ctx.user_id or "anon", ctx.ip_address or "unknown",
        )

    def log_response(
        self, ctx: RequestContext, success: bool, status: str = "ok", **kwargs
    ) -> None:
        level = "info" if success else "warning"
        getattr(logger, level)(
            "← RESPONSE | rid={} endpoint={} status={} elapsed={}ms",
            ctx.request_id, ctx.endpoint, status, ctx.elapsed_ms,
        )

    def log_exception(self, ctx: RequestContext, exc: Exception) -> None:
        logger.error(
            "✕ EXCEPTION | rid={} endpoint={} type={} msg={} elapsed={}ms\n{}",
            ctx.request_id,
            ctx.endpoint,
            type(exc).__name__,
            str(exc),
            ctx.elapsed_ms,
            traceback.format_exc(),
        )


# ─── JWT auth middleware ──────────────────────────────────────────────────────

class JWTAuthMiddleware:
    """
    JWT validation middleware.
    Decodes and validates JWTs from an Authorization: Bearer header.
    Falls back gracefully when PyJWT is not installed.
    """

    def __init__(self, secret_key: str = "", algorithm: str = "HS256") -> None:
        self._secret    = secret_key
        self._algorithm = algorithm
        try:
            import jwt  # PyJWT
            self._jwt = jwt
            self._available = True
        except ImportError:
            logger.warning("PyJWT not installed — JWT validation disabled.")
            self._available = False

    def validate(self, token: Optional[str]) -> Dict[str, Any]:
        """
        Returns the decoded JWT payload or raises AuthenticationError.
        If JWT is unavailable (no secret set or PyJWT missing), returns empty dict.
        """
        if not self._available or not self._secret:
            return {}

        if not token:
            raise AuthenticationError("Missing authentication token.")

        bearer = token.removeprefix("Bearer ").strip()
        if not bearer:
            raise AuthenticationError("Empty Bearer token.")

        try:
            payload = self._jwt.decode(bearer, self._secret, algorithms=[self._algorithm])
            return payload
        except self._jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired.")
        except self._jwt.InvalidTokenError as exc:
            raise AuthenticationError(f"Invalid token: {exc}")

    def create_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        """Mint a new JWT (for testing / auth service use)."""
        if not self._available:
            raise RuntimeError("PyJWT not installed.")
        import datetime
        exp_payload = {
            **payload,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
            "iat": datetime.datetime.utcnow(),
        }
        return self._jwt.encode(exp_payload, self._secret, algorithm=self._algorithm)


class AuthenticationError(Exception):
    pass


# ─── Exception handler ────────────────────────────────────────────────────────

class GlobalExceptionHandler:
    """
    Centralized exception handler.
    Maps known exception types to structured error payloads.
    """

    # (exception_class, status_hint, user_message)
    _MAPPINGS = [
        (ValueError,         "validation_error",    "Invalid input provided."),
        (FileNotFoundError,  "not_found",            "Requested resource was not found."),
        (PermissionError,    "forbidden",            "You do not have permission to perform this action."),
        (TimeoutError,       "timeout",              "The operation timed out. Please try again."),
        (MemoryError,        "server_error",         "Server ran out of memory processing this request."),
        (ConnectionError,    "service_unavailable",  "Could not reach an external service."),
    ]

    def handle(self, exc: Exception, ctx: Optional[RequestContext] = None) -> Dict[str, Any]:
        if ctx:
            LoggingMiddleware().log_exception(ctx, exc)

        for exc_class, status_hint, user_message in self._MAPPINGS:
            if isinstance(exc, exc_class):
                return self._build(user_message, status_hint, ctx)

        # Unhandled — generic 500
        logger.critical(
            "Unhandled exception: type={} msg={}\n{}",
            type(exc).__name__, str(exc), traceback.format_exc(),
        )
        return self._build(
            "An unexpected error occurred. Please try again.",
            "internal_server_error",
            ctx,
        )

    @staticmethod
    def _build(msg: str, hint: str, ctx: Optional[RequestContext]) -> Dict[str, Any]:
        return {
            "success":    False,
            "errors":     [msg],
            "status":     hint,
            "request_id": ctx.request_id if ctx else "unknown",
        }


# ─── Timing decorator ─────────────────────────────────────────────────────────

def timed(label: Optional[str] = None):
    """
    Decorator that logs the execution time of any function.

    @timed("pdf_extraction")
    def extract_pdf(data): ...
    """
    def decorator(func: Callable) -> Callable:
        _label = label or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                elapsed = int((time.monotonic() - start) * 1000)
                logger.debug("⏱  {} completed in {}ms", _label, elapsed)
                return result
            except Exception as exc:
                elapsed = int((time.monotonic() - start) * 1000)
                logger.warning("⏱  {} FAILED after {}ms | {}", _label, elapsed, exc)
                raise
        return wrapper
    return decorator


# ─── Context manager for request lifecycle ────────────────────────────────────

@contextmanager
def request_lifecycle(
    endpoint: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Generator[RequestContext, None, None]:
    """
    Context manager that wraps a request in full middleware chain:
    logging → exception handling → cleanup.

    Usage:
        with request_lifecycle("analyze", user_id="u123") as ctx:
            result = do_analysis(ctx.request_id)
    """
    ctx     = RequestContext(endpoint=endpoint, user_id=user_id, ip_address=ip_address)
    logging = LoggingMiddleware()
    exc_hdl = GlobalExceptionHandler()

    logging.log_request(ctx)
    try:
        yield ctx
        logging.log_response(ctx, success=True)
    except AuthenticationError:
        logging.log_response(ctx, success=False, status="auth_error")
        raise
    except Exception as exc:
        logging.log_exception(ctx, exc)
        logging.log_response(ctx, success=False, status="error")
        raise