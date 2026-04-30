"""
backend/utils/rate_limiter.py
Token-bucket rate limiter for API protection.
Supports per-endpoint and per-user rate limits.
"""

from __future__ import annotations

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

from loguru import logger


@dataclass
class RateLimitConfig:
    max_requests:    int    # max requests per window
    window_seconds:  int    # rolling window in seconds
    burst:           int    # max burst above sustained limit


@dataclass
class BucketState:
    tokens:          float
    last_refill:     float = field(default_factory=time.monotonic)
    request_count:   int   = 0
    blocked_until:   float = 0.0


class RateLimiter:
    """
    Thread-safe token-bucket rate limiter.

    Usage:
        limiter = RateLimiter(RateLimitConfig(max_requests=10, window_seconds=60, burst=3))
        allowed, retry_after = limiter.check("user:123")
        if not allowed:
            raise TooManyRequestsError(retry_after)
    """

    # Pre-configured profiles for common endpoints
    PROFILES: Dict[str, RateLimitConfig] = {
        "analyze":   RateLimitConfig(max_requests=20, window_seconds=60,  burst=3),
        "optimize":  RateLimitConfig(max_requests=5,  window_seconds=60,  burst=1),
        "upload":    RateLimitConfig(max_requests=30, window_seconds=60,  burst=5),
        "default":   RateLimitConfig(max_requests=60, window_seconds=60,  burst=10),
    }

    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        self._config = config or self.PROFILES["default"]
        self._buckets: Dict[str, BucketState] = defaultdict(
            lambda: BucketState(tokens=self._config.burst)
        )
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def check(self, key: str) -> Tuple[bool, float]:
        """
        Returns (allowed: bool, retry_after_seconds: float).
        retry_after is 0 when allowed=True.
        """
        with self._lock:
            return self._check_internal(key)

    def reset(self, key: str) -> None:
        """Reset the bucket for a specific key (e.g., after admin action)."""
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]
        logger.info("RateLimiter: bucket reset for key={}", key)

    def remaining(self, key: str) -> int:
        """Tokens remaining without consuming any."""
        with self._lock:
            state = self._buckets[key]
            self._refill(state)
            return int(state.tokens)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _check_internal(self, key: str) -> Tuple[bool, float]:
        cfg   = self._config
        state = self._buckets[key]
        now   = time.monotonic()

        # Blocked?
        if state.blocked_until > now:
            retry = round(state.blocked_until - now, 2)
            logger.warning("RateLimiter: key={} blocked for {}s", key, retry)
            return False, retry

        # Refill tokens
        self._refill(state)

        if state.tokens >= 1.0:
            state.tokens       -= 1.0
            state.request_count += 1
            return True, 0.0
        else:
            # Compute wait time until next token
            rate       = cfg.max_requests / cfg.window_seconds
            wait_time  = round((1.0 - state.tokens) / rate, 2)
            logger.warning("RateLimiter: key={} throttled, wait={}s", key, wait_time)
            return False, wait_time

    def _refill(self, state: BucketState) -> None:
        cfg  = self._config
        now  = time.monotonic()
        elapsed = now - state.last_refill
        refill  = elapsed * (cfg.max_requests / cfg.window_seconds)
        state.tokens      = min(cfg.burst, state.tokens + refill)
        state.last_refill = now


class MultiEndpointRateLimiter:
    """
    Manages separate rate limiters per endpoint profile.
    Designed to be instantiated once and shared application-wide.
    """

    def __init__(self) -> None:
        self._limiters: Dict[str, RateLimiter] = {
            name: RateLimiter(config)
            for name, config in RateLimiter.PROFILES.items()
        }

    def check(self, endpoint: str, key: str) -> Tuple[bool, float]:
        limiter = self._limiters.get(endpoint, self._limiters["default"])
        return limiter.check(key)

    def remaining(self, endpoint: str, key: str) -> int:
        limiter = self._limiters.get(endpoint, self._limiters["default"])
        return limiter.remaining(key)


# ── Decorator helper ──────────────────────────────────────────────────────────

def rate_limit(endpoint: str, key_fn: Callable[..., str]):
    """
    Decorator to apply rate limiting to any callable.

    Example:
        @rate_limit("optimize", key_fn=lambda user_id: f"user:{user_id}")
        def generate_resume(user_id: str, ...):
            ...
    """
    _limiter = RateLimiter(RateLimiter.PROFILES.get(endpoint, RateLimiter.PROFILES["default"]))

    def decorator(func: Callable) -> Callable:
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            allowed, retry_after = _limiter.check(key)
            if not allowed:
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Retry in {retry_after:.1f}s.",
                    retry_after=retry_after,
                )
            return func(*args, **kwargs)

        return wrapper
    return decorator


class RateLimitExceededError(Exception):
    def __init__(self, message: str, retry_after: float = 0.0) -> None:
        super().__init__(message)
        self.retry_after = retry_after