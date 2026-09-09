"""
Procura — Sliding Window Rate Limiting Middleware

Enforces requests-per-minute (RPM) limits per client IP address.
Provides rate-limiting headers:
  - X-RateLimit-Limit
  - X-RateLimit-Remaining
  - X-RateLimit-Reset
  - Retry-After
Returns HTTP 429 (Too Many Requests) when the threshold is exceeded.
"""

import time
from collections import defaultdict
from typing import Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter.
    Tracks timestamps per IP over a 60-second window.
    """

    def __init__(
        self,
        app,
        rpm: int = 160,
        exempt_paths: Optional[Set[str]] = None,
        exempt_prefixes: Optional[tuple[str, ...]] = None,
    ):
        super().__init__(app)
        self.rpm = rpm
        self.window_seconds = 60.0
        self.exempt_paths = exempt_paths or {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        }
        self.exempt_prefixes = exempt_prefixes or (
            "/api/query/status",
            "/api/tenders/status",
        )
        self._ip_history: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        """Extract the true client IP, respecting proxy headers if present."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

    def _is_exempt(self, path: str) -> bool:
        """Check if request path is exempt from rate limiting."""
        if path in self.exempt_paths:
            return True
        for prefix in self.exempt_prefixes:
            if path.startswith(prefix):
                return True
        return False

    def _cleanup_stale_records(self, now: float) -> None:
        """Periodic cleanup of timestamps older than the window to prevent memory leaks."""
        if now - self._last_cleanup > 300.0:  # Every 5 minutes
            threshold = now - self.window_seconds
            dead_ips = []
            for ip, timestamps in self._ip_history.items():
                self._ip_history[ip] = [t for t in timestamps if t > threshold]
                if not self._ip_history[ip]:
                    dead_ips.append(ip)
            for ip in dead_ips:
                del self._ip_history[ip]
            self._last_cleanup = now

    async def dispatch(self, request: Request, call_next) -> Response:
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return await call_next(request)

        path = request.url.path
        method = request.method.upper()

        # Check exemptions:
        # 1. Static/meta/health endpoints
        # 2. Polling endpoints (GET /api/query/{id} and GET /api/tenders/{id}/status)
        #    so active frontend progress polling does not exhaust the 10 RPM submission quota
        is_polling_check = (
            method == "GET"
            and (
                path.startswith("/api/query/")
                or path.startswith("/api/tenders/")
            )
            and (
                "/status" in path
                or path.endswith("/report")
                or path.count("/") == 3  # e.g., /api/query/<id>
            )
        )

        if self._is_exempt(path) or is_polling_check:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()
        threshold = now - self.window_seconds
        rpm = getattr(settings, "RATE_LIMIT_RPM", self.rpm)

        self._cleanup_stale_records(now)

        # Get existing timestamps within the 60s sliding window
        timestamps = [t for t in self._ip_history[client_ip] if t > threshold]

        if len(timestamps) >= rpm:
            oldest = timestamps[0]
            retry_after = max(1, int(oldest + self.window_seconds - now))
            logger.warning(
                f"[RATE_LIMIT] Client {client_ip} exceeded {rpm} RPM limit on {method} {path}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Maximum {rpm} requests per minute allowed.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rpm),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(oldest + self.window_seconds)),
                },
            )

        # Record this request
        timestamps.append(now)
        self._ip_history[client_ip] = timestamps

        remaining = max(0, rpm - len(timestamps))
        reset_time = int(timestamps[0] + self.window_seconds)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        return response
