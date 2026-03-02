"""In-memory rate limiting middleware."""

from collections import deque
from dataclasses import dataclass
from time import monotonic

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


@dataclass(frozen=True)
class RateLimitPolicy:
    """Rate limit policy for a route category."""

    name: str
    limit: int
    window_seconds: int


AUTH_LOGIN_POLICY = RateLimitPolicy("auth_login", limit=5, window_seconds=60)
AUTH_REGISTER_POLICY = RateLimitPolicy("auth_register", limit=3, window_seconds=60)
INGEST_POLICY = RateLimitPolicy("vault_ingest", limit=2, window_seconds=3600)
SEARCH_POLICY = RateLimitPolicy("search", limit=30, window_seconds=60)
DEFAULT_POLICY = RateLimitPolicy("default", limit=100, window_seconds=60)


def get_rate_limit_policy(path: str) -> RateLimitPolicy:
    """Select rate limit policy based on request path."""
    if path == "/auth/login":
        return AUTH_LOGIN_POLICY
    if path == "/auth/register":
        return AUTH_REGISTER_POLICY
    if path.startswith("/vaults/") and path.endswith("/ingest"):
        return INGEST_POLICY
    if path.startswith("/vaults/") and "/search/" in path:
        return SEARCH_POLICY
    return DEFAULT_POLICY


def get_client_key(request: Request) -> str:
    """Build a stable client key for rate limiting."""
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        # Use a small token prefix to avoid storing full tokens in memory.
        token_prefix = auth_header[7:39]
        return f"token:{token_prefix}"

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",", 1)[0].strip()
        if first_ip:
            return f"ip:{first_ip}"

    if request.client and request.client.host:
        return f"ip:{request.client.host}"

    return "ip:unknown"


class InMemoryRateLimiter:
    """Simple in-memory sliding-window limiter."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}

    def check(self, client_key: str, policy: RateLimitPolicy) -> tuple[bool, int, int]:
        """Check and register a hit.

        Returns:
            Tuple of (allowed, remaining, retry_after_seconds)
        """
        now = monotonic()
        window_start = now - policy.window_seconds
        bucket_key = f"{policy.name}:{client_key}"
        hits = self._hits.setdefault(bucket_key, deque())

        while hits and hits[0] <= window_start:
            hits.popleft()

        if len(hits) >= policy.limit:
            retry_after = max(1, int(policy.window_seconds - (now - hits[0])))
            return False, 0, retry_after

        hits.append(now)
        remaining = max(0, policy.limit - len(hits))
        return True, remaining, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply endpoint-specific in-memory rate limits."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._limiter = InMemoryRateLimiter()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        policy = get_rate_limit_policy(request.url.path)
        client_key = get_client_key(request)
        allowed, remaining, retry_after = self._limiter.check(client_key, policy)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded",
                    "details": {
                        "limit": policy.limit,
                        "window_seconds": policy.window_seconds,
                        "retry_after_seconds": retry_after,
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(policy.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(policy.window_seconds),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(policy.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(policy.window_seconds)
        return response
