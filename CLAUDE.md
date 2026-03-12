# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

LLM Cost Monitor is a B2B Micro-SaaS proxy that sits between client apps and LLM providers (OpenAI, Anthropic, Google Gemini, Mistral). It intercepts API calls to track costs, enforce budget limits, and suggest optimizations. The client only changes their `base_url` — all request/response formats are preserved exactly.

## Development Commands

### Backend (FastAPI + Python 3.12)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload --port 8000

# Run all tests
pytest

# Run a single test file
pytest tests/unit/test_key_vault.py -v

# Run a single test
pytest tests/unit/test_proxy.py::test_rate_limit_exceeded -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend (Next.js 14+ App Router)
```bash
cd frontend
npm install

# Dev server
npm run dev

# Type check
npm run type-check   # or: npx tsc --noEmit

# Lint
npm run lint

# Build
npm run build
```

### Local Environment
```bash
# Start all services (PostgreSQL + Redis + backend)
docker-compose up -d

# Generate a new Master Encryption Key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Required env vars: `MASTER_ENCRYPTION_KEY`, `DATABASE_URL`, `REDIS_URL`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`

## Architecture

### Request Flow (the core product)
```
Client App → POST /v1/chat/completions (with lcm_sk_live_... key)
           → Validate service key (SHA-256 hash lookup, Redis cache)
           → Rate limit check (Redis sliding window)
           → Budget limit check (Redis counter, soft 80% / hard 100%)
           → Decrypt provider API key (Fernet, lives in memory ~100ms)
           → Forward to LLM provider (httpx async, same request format)
           → Stream response back to client (SSE passthrough)
           → [Background] Log usage, calculate cost, evaluate alerts
```

**Latency budget: <20ms added.** All logging is async via `BackgroundTasks`. Never block the response path for DB writes.

### Backend Layer Pattern
```
API Routes (app/api/)          — Pydantic validation only, no business logic
    ↓
Service Layer (app/services/)  — All business logic, orchestrates repos
    ↓
Repository + Models (app/models/) — SQLAlchemy queries, never called from routes
```

### Key Security Invariants
- **Provider API keys** (OpenAI/Anthropic keys from clients): encrypted at rest with Fernet (AES-128-CBC + HMAC). Column: `provider_api_keys.key_ciphertext`. Never returned in API responses — only the prefix.
- **Service API keys** (our proxy auth keys): only SHA-256 hash stored. Full key shown once at creation. Format: `lcm_sk_live_<32 random bytes>`.
- `MASTER_ENCRYPTION_KEY` lives only in env vars, never in code or commits.

### Alert Engine (4 levels, evaluated per request)
1. **Rate limiting** — Redis sliding window, returns 429 with `Retry-After`
2. **Budget limits** — Redis counter; soft limit (80%) sends alert, hard limit (100%) blocks
3. **Anomaly detection** — if spend last hour > 3× 7-day hourly average, alert (doesn't block)
4. **Circuit breaker** — if spend in 5-min window > threshold → auto-block, manual unlock only

### Database (13 tables, see `docs/specs/database-er.mermaid`)
Core: `organizations`, `users`, `tags`
Security: `service_api_keys`, `provider_api_keys`
Providers: `providers`, `models` (with per-token prices)
Logs: `usage_logs` (partitioned by date)
Intelligence: `model_benchmarks`, `optimization_suggestions`, `shadow_test_results`
Alerts: `alert_rules`, `alert_events`, `notification_channels`
Audit: `audit_logs`

### Intelligence Engine (Phase 2, post-MVP)
Activated only when real usage data exists. Three levels: rule-based task classifier → ML classifier → LLM-as-classifier. Suggestion engine runs daily, compares client's model usage against `model_benchmarks` and creates `optimization_suggestions` only when projected savings > $10/month.

## Coding Rules

**Backend:**
- All I/O must be `async`. No sync DB calls.
- Use `structlog` for logging. Never `print()`.
- Repository pattern: services never write SQLAlchemy queries directly.
- Config via `pydantic-settings` in `app/core/config.py`.
- Errors via `HTTPException` with correct HTTP codes.
- Never log, return, or commit API keys (full values).

**Frontend:**
- TypeScript strict mode. Never `any`.
- Data fetching via SWR or Server Components. No `useEffect` for fetching.
- Design tokens from `lib/design-tokens.ts` — never hardcode colors.
- Imports via `@/` absolute paths.
- Components max ~150 lines; extract sub-components when larger.

## Specialized Agents

Use these for focused work:
- `.claude/agents/backend-specialist.md` — API, proxy, business logic
- `.claude/agents/frontend-specialist.md` — UI/UX, React components
- `.claude/agents/security-specialist.md` — encryption, auth, abuse protection
- `.claude/agents/datascience-specialist.md` — intelligence engine (Phase 2 only)

Skills in `.claude/skills/` cover proxy implementation, key management, and alert engine patterns.
