import time

import redis.asyncio as aioredis
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

log = structlog.get_logger()

# Requests per minute per plan
PLAN_LIMITS: dict[str, int] = {
    "free": 60,
    "starter": 200,
    "pro": 1000,
    "enterprise": 5000,
}

# Only rate-limit proxy endpoints — dashboard API uses JWT auth which is lighter
RATE_LIMITED_PREFIXES = ("/v1/chat/completions", "/v1/messages")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter for proxy endpoints.
    Window = 60 seconds. Key: ratelimit:{org_id}:{window_bucket}

    The plan limit is read from Redis cache (set at auth time).
    Falls back to the 'free' limit if no plan is found.
    """

    def __init__(self, app, redis_url: str = "") -> None:
        super().__init__(app)
        self._redis_url = redis_url or settings.REDIS_URL

    async def dispatch(self, request: Request, call_next) -> Response:
        if not any(request.url.path.startswith(p) for p in RATE_LIMITED_PREFIXES):
            return await call_next(request)

        org_id = request.state.__dict__.get("org_id")
        if not org_id:
            # Auth middleware hasn't run yet or key is invalid — let the endpoint handle it
            return await call_next(request)

        redis: aioredis.Redis = aioredis.from_url(self._redis_url, decode_responses=True)
        try:
            allowed, remaining = await _check_rate_limit(redis, org_id, request)
        finally:
            await redis.aclose()

        if not allowed:
            log.warning("rate_limit_exceeded", org_id=org_id, path=request.url.path)
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


async def _check_rate_limit(
    redis: aioredis.Redis,
    org_id: str,
    request: Request,
    window: int = 60,
) -> tuple[bool, int]:
    """
    Sliding window counter using Redis INCR + EXPIRE.
    Returns (allowed, remaining_requests).
    """
    plan = await redis.get(f"org:{org_id}:plan") or "free"
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    bucket = int(time.time()) // window
    key = f"ratelimit:{org_id}:{bucket}"

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window * 2)  # 2x window so the key outlives the bucket

    remaining = max(0, limit - count)
    return count <= limit, remaining


async def check_rate_limit(
    redis: aioredis.Redis,
    org_id: str,
    plan: str = "free",
    window: int = 60,
) -> tuple[bool, int]:
    """
    Standalone function for use inside proxy service (outside middleware context).
    Returns (allowed, remaining).
    """
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    bucket = int(time.time()) // window
    key = f"ratelimit:{org_id}:{bucket}"

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window * 2)

    remaining = max(0, limit - count)
    return count <= limit, remaining
