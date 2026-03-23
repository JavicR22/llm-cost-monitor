# LLM Cost Monitor

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

B2B Micro-SaaS proxy that sits between your app and LLM providers. Monitor costs, enforce budget limits, and attribute spend per project, team, and developer — without changing a single line of your existing code.

## How it works

```
Your App  →  POST http://localhost:8000/v1/chat/completions
                      ↓
             [Validate key] [Rate limit] [Budget check]
                      ↓
             Forward to OpenAI / Google Gemini
                      ↓
             Stream response back (same format, same SDK)
                      ↓  (background)
             Log usage, calculate cost, evaluate alerts
```

You only change the `base_url`. The rest of your code stays the same.

## Supported Providers

| Provider | Status | Proxy endpoint |
|----------|--------|----------------|
| OpenAI | ✅ Active | `/v1/chat/completions` |
| Google Gemini | ✅ Active | `/v1/chat/completions` (OpenAI-compatible) |
| Anthropic | 🔜 Coming soon | — |
| Mistral | 🔜 Coming soon | — |

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS + Shadcn UI |
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 15 (Supabase in prod) |
| Cache | Redis 7 (Upstash in prod) |
| Auth | JWT RS256 + bcrypt |
| Encryption | Fernet (AES-128-CBC + HMAC) for API keys at rest |
| Deploy | Railway (backend) + Vercel (frontend) |

## Local Development

### Prerequisites
- Docker + Docker Compose
- Python 3.12
- Node.js 20+

### 1. Clone and configure

```bash
git clone https://github.com/your-username/llm-cost-monitor.git
cd llm-cost-monitor

cp backend/.env.example backend/.env
# Fill in the required secrets (see Environment Variables section below)
```

### 2. Generate required secrets

```bash
# Master encryption key (for provider API keys at rest)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# RSA key pair (for JWT RS256)
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
# Paste contents into .env as single-line with \n separators
```

### 3. Start with Docker Compose

```bash
docker compose up -d
```

Services:
- Backend API: http://localhost:8000
- Postgres: localhost:5432
- Redis: localhost:6379

### 4. Run database migrations

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL="postgresql+asyncpg://llmcost:llmcost@localhost:5432/llmcost" alembic upgrade head
```

### 5. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

## Backend Development (without Docker)

```bash
cd backend
source .venv/bin/activate

# Run server with hot reload
uvicorn app.main:app --reload --port 8000

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/unit/test_key_vault.py -v

# Generate a new migration after model changes
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Project Structure

```
llm-cost-monitor/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   │   ├── auth.py      # Login, register, /me
│   │   │   ├── service_keys.py
│   │   │   ├── projects.py  # FinOps: projects + teams CRUD
│   │   │   ├── members.py   # Org member management (owner only)
│   │   │   ├── analytics.py # Aggregated spend/usage stats
│   │   │   └── reports.py   # FinOps spend reports by project/team/member
│   │   ├── api/proxy/       # Drop-in LLM proxy (OpenAI, Google)
│   │   ├── core/            # Config, security, DB, dependencies
│   │   ├── middleware/       # Security headers, rate limiting
│   │   ├── models/          # SQLAlchemy models
│   │   │   ├── user.py      # User + roles + last_login_at
│   │   │   ├── api_key.py   # ServiceAPIKey (project/team/owner attribution)
│   │   │   ├── project.py   # Project model
│   │   │   ├── team.py      # Team model
│   │   │   └── usage_log.py # Per-request cost log (partitioned)
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── repositories/    # DB queries (never called from routes)
│   │   ├── services/        # Business logic
│   │   │   ├── auth/        # Login, register, token refresh
│   │   │   ├── keys/        # Service key creation + assignment
│   │   │   ├── finops/      # Project, team, report services
│   │   │   ├── security/    # KeyVault (Fernet + SHA-256)
│   │   │   ├── proxy/       # Forward requests to LLM providers
│   │   │   ├── metering/    # Token counting + cost calculation
│   │   │   └── alerts/      # Alert engine + circuit breaker
│   │   └── tasks/           # Background jobs
│   ├── alembic/             # DB migrations
│   └── tests/
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   │   └── (dashboard)/
│   │       ├── dashboard/
│   │       │   ├── page.tsx       # Main dashboard
│   │       │   ├── keys/          # API Keys management (owner only)
│   │       │   ├── projects/      # Projects list + detail with Teams/Developers tabs
│   │       │   └── members/       # Org members (owner only)
│   │       └── layout.tsx         # Auth guard + role-based route protection
│   ├── components/
│   │   ├── layout/          # Sidebar (role-filtered nav), TopBar
│   │   ├── keys/            # ServiceKeysList, RawKeyModal
│   │   └── finops/          # BudgetBar, NewProjectModal
│   └── lib/
│       ├── api.ts           # Typed HTTP client
│       ├── hooks/
│       │   ├── useKeys.ts   # Service keys SWR hooks
│       │   └── useFinOps.ts # Projects, teams, members, reports hooks
│       ├── design-tokens.ts # Color/spacing constants
│       └── utils.ts         # cn() and helpers
├── docs/specs/              # Architecture diagrams and specs
├── docker-compose.yml
└── CLAUDE.md                # AI assistant instructions
```

## Roles & Permissions

| Role | Description | Access |
|------|-------------|--------|
| **Owner** | Organization administrator | Full access: API Keys, Projects, Members, Analytics, Settings |
| **Admin** | Developer / team member | Dashboard, Alerts, Suggestions, Models, personal Settings |

Owners manage the organization. Admins are developers who use the proxy and see only their own usage.

Route protection is enforced both in the sidebar (items hidden per role) and at the layout level (direct URL access redirected).

### Personal API Key — auto-provisioning

When an **Admin** user logs in for the **first time**, the system automatically:

1. Creates a Service API Key named `{Full Name} - Personal Key`
2. Sets the `owner_user_id` attribution to that user
3. Shows the raw key **once** via a secure modal (copy + confirmation required)
4. Marks `last_login_at` so the flow does not repeat

This key then appears in the Owner's API Keys list with developer attribution, and in any Project's **Developers** tab — even before the developer has made a single request.

```
Admin logs in (first time)
  ↓
Auto-create: "Jhoiman Gonzalez - Personal Key"  lcm_sk_live_...XXXX
  owner_user_id = Jhoiman.id
  ↓
Modal shown once → user copies key → redirected to Dashboard
```

## FinOps Cost Attribution

Track LLM spend across a 4-level hierarchy: **Org → Project → Team → Developer**

- Every Service API Key can be assigned to a Project, Team, and Developer (owner)
- Usage logs propagate these fields automatically via the proxy (background, non-blocking)
- Project detail page shows:
  - **Teams tab**: spend and requests per team, even with $0 activity
  - **Developers tab**: all developers with an attributed key, even before any usage

Owners can create Projects and Teams from the dashboard. Assigning a developer's key to a project/team is done from the API Keys view (inline layer assignment).

## Adding Developers to your Organization

Owners can add Admin (developer) users from the **Members** section:

1. Go to **Members** in the sidebar
2. Click **Invite Member**, fill in name, email, password, and set role to `Admin`
3. Share the credentials with the developer
4. On their **first login**, the system automatically creates a personal Service API Key for them and shows it once via a secure modal
5. The developer copies their key and uses it as `Authorization: Bearer <key>` when calling the proxy

After this, the Owner will see that developer's usage under any Project they are assigned to.

## Alert Engine

The system evaluates 4 protection layers on every proxied request:

| Layer | Trigger | Action |
|-------|---------|--------|
| **Rate limit** | Requests per minute exceed threshold | Returns `429` with `Retry-After` |
| **Budget soft limit** | Spend reaches 80% of budget | Sends alert notification |
| **Budget hard limit** | Spend reaches 100% of budget | Blocks all requests |
| **Anomaly detection** | Spend last hour > 3× 7-day hourly average | Sends alert (non-blocking) |
| **Circuit breaker** | Spend in 5-min window exceeds threshold | Auto-blocks; manual unlock required |

All alert checks run in the request path with <20ms added latency. Usage logging runs in background (non-blocking).

## Roadmap

### Phase 1 — Current (MVP)
- [x] Proxy for OpenAI and Google Gemini
- [x] Cost tracking per request with token counting
- [x] FinOps attribution: Org → Project → Team → Developer
- [x] Budget limits (soft + hard) with alerts
- [x] Role-based access (Owner / Admin)
- [x] Personal API Key auto-provisioning on first login

### Phase 2 — Intelligence Engine *(waiting for real usage data)*
- [ ] Rule-based task classifier (prompt → task type)
- [ ] Daily optimization suggestions when projected savings > $10/month
- [ ] Model benchmarking: compare quality vs cost across providers
- [ ] Shadow testing: run requests against a cheaper model silently and compare outputs
- [ ] ML classifier for task categorization (trained on org's own usage)

## Security Model

- **Provider API keys** (OpenAI/Anthropic keys): encrypted with Fernet before storing, never returned in API responses
- **Service API keys** (proxy auth): only SHA-256 hash stored, shown to user once at creation
- **Master Key**: lives only in environment variables, never in code or DB
- **JWT**: RS256, 24h expiry, refresh tokens with 7-day rotation

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg driver) |
| `REDIS_URL` | Redis connection string |
| `MASTER_ENCRYPTION_KEY` | Fernet key for encrypting provider API keys |
| `JWT_PRIVATE_KEY` | RSA private key PEM (single line with `\n`) |
| `JWT_PUBLIC_KEY` | RSA public key PEM (single line with `\n`) |
| `CORS_ORIGINS` | JSON array: `["https://your-frontend.com"]` |
| `DEBUG` | `true` enables `/docs` and `/redoc` |
