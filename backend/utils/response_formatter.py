"""
backend/utils/response_formatter.py
Consistent API Response Formatter.
Ensures every response from the system follows a uniform envelope structure.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar

from loguru import logger

T = TypeVar("T")


# ─── Response envelope ────────────────────────────────────────────────────────

@dataclass
class APIResponse:
    success:    bool
    request_id: str
    timestamp:  str
    data:       Optional[Any]         = None
    errors:     List[str]             = field(default_factory=list)
    warnings:   List[str]             = field(default_factory=list)
    meta:       Dict[str, Any]        = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success":    self.success,
            "request_id": self.request_id,
            "timestamp":  self.timestamp,
            "data":       self.data,
            "errors":     self.errors,
            "warnings":   self.warnings,
            "meta":       self.meta,
        }


@dataclass
class PaginatedResponse:
    items:      List[Any]
    total:      int
    page:       int
    page_size:  int
    has_next:   bool
    has_prev:   bool


# ─── Formatter ────────────────────────────────────────────────────────────────

class ResponseFormatter:
    """
    Builds standardised API response envelopes.

    Example:
        fmt = ResponseFormatter()
        return fmt.success(data=analysis_result, warnings=["Short resume"])
    """

    def __init__(self) -> None:
        self._start_times: Dict[str, float] = {}

    # ── Core factories ────────────────────────────────────────────────────────

    def success(
        self,
        data: Any = None,
        warnings: Optional[List[str]] = None,
        meta: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> APIResponse:
        rid = request_id or self._new_request_id()
        elapsed = self._elapsed(rid)
        return APIResponse(
            success=True,
            request_id=rid,
            timestamp=self._iso_now(),
            data=data,
            warnings=warnings or [],
            meta={**(meta or {}), "processing_ms": elapsed},
        )

    def error(
        self,
        errors: List[str],
        status_hint: str = "error",
        warnings: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> APIResponse:
        rid = request_id or self._new_request_id()
        logger.warning("ResponseFormatter.error: rid={} errors={}", rid, errors)
        return APIResponse(
            success=False,
            request_id=rid,
            timestamp=self._iso_now(),
            data=None,
            errors=errors,
            warnings=warnings or [],
            meta={"status_hint": status_hint},
        )

    def validation_error(
        self,
        errors: List[str],
        warnings: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> APIResponse:
        return self.error(
            errors=errors,
            status_hint="validation_error",
            warnings=warnings,
            request_id=request_id,
        )

    def rate_limit_error(
        self, retry_after: float, request_id: Optional[str] = None
    ) -> APIResponse:
        return self.error(
            errors=[f"Rate limit exceeded. Retry after {retry_after:.1f}s."],
            status_hint="rate_limit_exceeded",
            request_id=request_id,
            warnings=[],
        )

    def not_found(
        self, resource: str, request_id: Optional[str] = None
    ) -> APIResponse:
        return self.error(
            errors=[f"{resource} not found."],
            status_hint="not_found",
            request_id=request_id,
        )

    def paginated(
        self,
        items: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
        warnings: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> APIResponse:
        data = PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_prev=page > 1,
        )
        return self.success(
            data={
                "items":     items,
                "total":     total,
                "page":      page,
                "page_size": page_size,
                "has_next":  data.has_next,
                "has_prev":  data.has_prev,
            },
            warnings=warnings,
            request_id=request_id,
        )

    # ── Timing helpers ────────────────────────────────────────────────────────

    def start_timer(self, request_id: str) -> str:
        self._start_times[request_id] = time.monotonic()
        return request_id

    def new_timed_request(self) -> str:
        rid = self._new_request_id()
        return self.start_timer(rid)

    def _elapsed(self, request_id: str) -> int:
        """Elapsed milliseconds since start_timer was called, or 0."""
        start = self._start_times.pop(request_id, None)
        if start is None:
            return 0
        return int((time.monotonic() - start) * 1000)

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _new_request_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _iso_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Dataclass serialisation ───────────────────────────────────────────────

    @staticmethod
    def serialise(obj: Any) -> Any:
        """
        Recursively convert dataclasses and custom objects to dicts.
        Falls back gracefully to str() for non-serialisable types.
        """
        if hasattr(obj, "__dataclass_fields__"):
            return {k: ResponseFormatter.serialise(v) for k, v in asdict(obj).items()}
        if isinstance(obj, list):
            return [ResponseFormatter.serialise(i) for i in obj]
        if isinstance(obj, dict):
            return {k: ResponseFormatter.serialise(v) for k, v in obj.items()}
        if isinstance(obj, set):
            return [ResponseFormatter.serialise(i) for i in sorted(obj)]
        if isinstance(obj, (int, float, bool, str, type(None))):
            return obj
        return str(obj)


# ── Module-level singleton ────────────────────────────────────────────────────

_formatter = ResponseFormatter()


def ok(data: Any = None, **kwargs) -> Dict[str, Any]:
    return _formatter.success(data=data, **kwargs).to_dict()


def err(errors: List[str], **kwargs) -> Dict[str, Any]:
    return _formatter.error(errors=errors, **kwargs).to_dict()