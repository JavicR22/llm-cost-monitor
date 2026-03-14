"""
Core proxy service — authenticate, decrypt, forward.

Latency budget: <20ms added overhead.
- Service key validation: Redis cache (~1ms) or DB (~5ms)
- Provider key decryption: Fernet in-memory (~0.2ms)
- Network to OpenAI: not in our budget
"""
import json
from typing import AsyncIterator, Optional

import httpx
import redis.asyncio as aioredis
import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.rate_limit import check_rate_limit
from app.models.api_key import ServiceAPIKey
from app.repositories.proxy_repo import get_active_provider_key, get_service_key_by_hash
from app.services.security.key_vault import get_key_vault

log = structlog.get_logger()

# Redis cache TTL for validated service keys (5 minutes)
_SERVICE_KEY_CACHE_TTL = 300

# Provider base URLs
PROVIDER_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
}


class ProxyService:
    """Stateless service — one instance shared via DI."""

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(
        self,
        raw_key: str,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> ServiceAPIKey:
        """
        Validate a service key and return the associated ServiceAPIKey row.

        Strategy:
        1. SHA-256 hash the raw key
        2. Check Redis cache (fast path)
        3. Fall back to DB lookup (slow path, then populate cache)
        """
        from app.services.security.key_vault import KeyVault

        if not raw_key.startswith("lcm_sk_live_"):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key format")

        key_hash = KeyVault.hash_service_key(raw_key)
        cache_key = f"sk_valid:{key_hash}"

        # Fast path — cache hit
        cached = await redis.get(cache_key)
        if cached:
            # Validate still active (lightweight DB check on cache hit)
            service_key = await get_service_key_by_hash(db, key_hash)
            if not service_key:
                await redis.delete(cache_key)
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key revoked")
            return service_key

        # Slow path — DB lookup
        service_key = await get_service_key_by_hash(db, key_hash)
        if not service_key:
            log.warning("proxy_auth_failed", key_prefix=raw_key[:16])
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or inactive API key")

        # Populate cache
        await redis.setex(cache_key, _SERVICE_KEY_CACHE_TTL, "1")
        log.info("proxy_auth_ok", org_id=str(service_key.organization_id))
        return service_key

    # ------------------------------------------------------------------
    # Rate limiting (delegates to the shared sliding-window function)
    # ------------------------------------------------------------------

    async def check_rate_limit(
        self,
        org_id: str,
        redis: aioredis.Redis,
    ) -> None:
        plan = await redis.get(f"org:{org_id}:plan") or "free"
        allowed, remaining = await check_rate_limit(redis, org_id, plan)
        if not allowed:
            log.warning("proxy_rate_limited", org_id=org_id)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Rate limit exceeded",
                headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
            )

    # ------------------------------------------------------------------
    # Provider key decryption
    # ------------------------------------------------------------------

    async def get_decrypted_provider_key(
        self,
        db: AsyncSession,
        org_id,
        provider: str,
    ) -> str:
        """
        Decrypt and return the provider API key.
        The decrypted value must NEVER be logged or persisted.
        """
        provider_key = await get_active_provider_key(db, org_id, provider)
        if not provider_key:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"No active {provider} API key configured for this organization. "
                "Add one via /api/v1/provider-keys.",
            )

        vault = get_key_vault()
        return vault.decrypt(provider_key.key_ciphertext)

    # ------------------------------------------------------------------
    # Forwarding — non-streaming
    # ------------------------------------------------------------------

    async def forward(
        self,
        provider: str,
        body: dict,
        api_key: str,
    ) -> dict:
        """Forward a non-streaming request and return the full JSON response."""
        url = PROVIDER_URLS[provider]
        headers = _build_headers(provider, api_key)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=body, headers=headers)

        if resp.status_code != 200:
            _raise_provider_error(provider, resp)

        return resp.json()

    # ------------------------------------------------------------------
    # Forwarding — streaming (SSE passthrough)
    # ------------------------------------------------------------------

    async def forward_stream(
        self,
        provider: str,
        body: dict,
        api_key: str,
    ) -> AsyncIterator[bytes]:
        """
        Stream SSE chunks from the provider back to the client.
        Yields raw bytes — the route handler wraps this in StreamingResponse.
        """
        url = PROVIDER_URLS[provider]
        headers = _build_headers(provider, api_key)

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                if resp.status_code != 200:
                    content = await resp.aread()
                    log.error(
                        "provider_stream_error",
                        provider=provider,
                        status=resp.status_code,
                    )
                    raise HTTPException(
                        status.HTTP_502_BAD_GATEWAY,
                        f"Provider error {resp.status_code}: {content.decode()[:200]}",
                    )
                async for chunk in resp.aiter_bytes():
                    yield chunk


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _build_headers(provider: str, api_key: str) -> dict[str, str]:
    if provider in ("openai", "google"):
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    if provider == "anthropic":
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
    return {}


def _raise_provider_error(provider: str, resp: httpx.Response) -> None:
    try:
        detail = resp.json().get("error", {}).get("message", resp.text[:200])
    except Exception:
        detail = resp.text[:200]
    log.error("provider_error", provider=provider, status=resp.status_code, detail=detail)
    raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Provider error: {detail}")


def get_proxy_service() -> ProxyService:
    """DI factory — returns the singleton ProxyService."""
    return _proxy_service


_proxy_service = ProxyService()
