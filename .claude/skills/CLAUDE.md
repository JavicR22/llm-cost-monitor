# LLM Cost Monitor — Proyecto Principal

## Visión General
LLM Cost Monitor es un Micro-SaaS B2B que funciona como proxy inteligente entre las aplicaciones de los clientes y los proveedores de LLM (OpenAI, Anthropic, Google Gemini, Mistral). Monitorea, alerta y optimiza el gasto en APIs de IA.

## Stack Tecnológico
- **Frontend:** Next.js 14+ (App Router) + TypeScript + Tailwind CSS + Shadcn UI + Recharts
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + Alembic + httpx
- **Base de Datos:** PostgreSQL (Supabase) + Redis (Upstash)
- **Seguridad:** Fernet (AES-128-CBC + HMAC) para API Keys, JWT RS256 para auth, SHA-256 para service keys
- **Deploy:** Railway (backend) + Vercel (frontend) + Supabase (DB) + Upstash (Redis)

## Estructura del Proyecto
```
llm-cost-monitor/
├── frontend/                 # Next.js App
│   ├── app/                  # App Router pages
│   ├── components/           # Componentes React reutilizables
│   │   ├── ui/               # Shadcn UI components
│   │   ├── dashboard/        # Dashboard widgets
│   │   ├── alerts/           # Alert management components
│   │   ├── suggestions/      # Optimization suggestions
│   │   ├── models/           # Model comparator
│   │   ├── keys/             # API Key management
│   │   ├── settings/         # Settings components
│   │   └── layout/           # Sidebar, TopBar, shared layout
│   ├── lib/                  # Utilities, API client, auth
│   └── styles/               # Global styles, design tokens
├── backend/                  # FastAPI App
│   ├── app/
│   │   ├── api/              # Endpoints REST
│   │   │   ├── v1/           # API v1 routes
│   │   │   └── proxy/        # Proxy endpoints (drop-in replacement)
│   │   ├── core/             # Config, security, dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic layer
│   │   │   ├── proxy/        # Proxy service (forward to LLM providers)
│   │   │   ├── metering/     # Token counting & cost calculation
│   │   │   ├── alerts/       # Alert engine & circuit breaker
│   │   │   ├── suggestions/  # Intelligence engine
│   │   │   ├── security/     # Key encryption/decryption
│   │   │   └── notifications/ # Slack, Email, SMS
│   │   ├── tasks/            # Background jobs (scheduler)
│   │   └── middleware/       # Auth, rate limiting, CORS
│   ├── alembic/              # Database migrations
│   └── tests/                # Unit & integration tests
├── docs/                     # Documentation
│   └── specs/                # Technical specifications
└── docker-compose.yml        # Local development
```

## Design System
- **Background:** Deep navy #0F172A (main), #1E293B (cards/sidebar)
- **Primary accent:** Electric blue #3B82F6
- **Success:** Emerald green #10B981
- **Warning:** Amber #F59E0B
- **Danger:** Red #EF4444
- **Text primary:** White #F8FAFC
- **Text secondary:** Slate gray #94A3B8
- **Typography:** Inter font family
- **Cards:** Rounded corners 12px, subtle border #334155

## Principios de Desarrollo
1. **Código limpio:** Funciones pequeñas, nombres descriptivos, sin código muerto
2. **Seguridad primero:** Las API Keys se cifran SIEMPRE, Master Key en env vars
3. **Latencia mínima:** El proxy no debe agregar >20ms, logging asíncrono
4. **Separación de responsabilidades:** Cada servicio tiene su dominio claro
5. **Testing:** Cada feature debe tener tests unitarios mínimos

## Agentes Especializados
Este proyecto usa 4 agentes especializados. Consultar:
- `.claude/agents/frontend-specialist.md` — UI/UX y componentes React
- `.claude/agents/backend-specialist.md` — API, proxy, lógica de negocio
- `.claude/agents/security-specialist.md` — Cifrado, auth, protección contra abuso
- `.claude/agents/datascience-specialist.md` — Motor de inteligencia y optimización

## Skills del Proyecto
Consultar `.claude/skills/` para skills específicas del dominio.
