# LLM Cost Monitor

B2B Micro-SaaS proxy that sits between your app and LLM providers (OpenAI, Anthropic, Google Gemini, Mistral). Monitor costs, enforce budget limits, and get optimization suggestions — without changing a single line of your existing code.

## How it works

```
Your App  →  POST https://api.llm-cost-monitor.com/v1/chat/completions
                      ↓
             [Validate key] [Rate limit] [Budget check]
                      ↓
             Forward to OpenAI / Anthropic / Google / Mistral
                      ↓
             Stream response back (same format, same SDK)
                      ↓  (background)
             Log usage, calculate cost, evaluate alerts
```

You only change the `base_url`. The rest of your code stays the same.

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
# Edit backend/.env and fill in the required keys (see below)
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
│   │   ├── api/proxy/       # Drop-in LLM proxy endpoints
│   │   ├── core/            # Config, security, DB, dependencies
│   │   ├── middleware/       # Security headers, rate limiting
│   │   ├── models/          # SQLAlchemy models (15 tables)
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   │   ├── auth/
│   │   │   ├── security/    # KeyVault (Fernet + SHA-256)
│   │   │   ├── proxy/       # Forward requests to LLM providers
│   │   │   ├── metering/    # Token counting + cost calculation
│   │   │   └── alerts/      # Alert engine + circuit breaker
│   │   └── tasks/           # Background jobs
│   ├── alembic/             # DB migrations
│   └── tests/
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   │   ├── ui/              # Shadcn base components
│   │   ├── layout/          # Sidebar, TopBar
│   │   └── dashboard/       # Dashboard widgets
│   └── lib/
│       ├── api.ts           # Typed HTTP client
│       ├── design-tokens.ts # Color/spacing constants
│       └── utils.ts         # cn() and helpers
├── docs/specs/              # Architecture diagrams and specs
├── docker-compose.yml
└── CLAUDE.md                # AI assistant instructions
```

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
