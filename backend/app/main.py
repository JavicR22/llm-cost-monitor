import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.proxy.openai import router as proxy_router
from app.api.proxy.google import router as google_proxy_router
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

log = structlog.get_logger()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Middleware stack — applied in reverse order (last added = first executed)
# Order: CORS → RateLimit → SecurityHeaders → route handler
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    log.info("startup", app=settings.APP_NAME)


@app.on_event("shutdown")
async def shutdown() -> None:
    log.info("shutdown")


app.include_router(v1_router)
app.include_router(proxy_router)         # OpenAI proxy at /v1/chat/completions
app.include_router(google_proxy_router)  # Gemini proxy at /v1/google/chat/completions


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
