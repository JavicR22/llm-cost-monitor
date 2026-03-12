# Plan de Trabajo — LLM Cost Monitor

## Fase 1: MVP (Semanas 1-6)
El objetivo es tener un producto funcional que un usuario pueda probar end-to-end.

### Sprint 1 (Semana 1-2): Fundación
**Agente principal:** Backend + Security

| # | Tarea | Agente | Prioridad |
|---|-------|--------|-----------|
| 1.1 | Inicializar proyecto: monorepo con frontend/ y backend/ | Backend | P0 |
| 1.2 | Configurar FastAPI con estructura de carpetas limpia | Backend | P0 |
| 1.3 | Configurar Next.js con App Router + Tailwind + Shadcn | Frontend | P0 |
| 1.4 | Definir SQLAlchemy models para las 13 tablas | Backend | P0 |
| 1.5 | Configurar Alembic + primera migración | Backend | P0 |
| 1.6 | Implementar KeyVault (Fernet encryption/decryption) | Security | P0 |
| 1.7 | Implementar auth: register, login, JWT RS256 | Backend + Security | P0 |
| 1.8 | Implementar middleware: CORS, security headers, rate limiting | Security | P0 |
| 1.9 | Docker Compose para desarrollo local (FastAPI + PostgreSQL + Redis) | Backend | P0 |
| 1.10 | Design tokens + layout compartido (Sidebar + TopBar) | Frontend | P0 |

### Sprint 2 (Semana 3-4): Core del Proxy + Dashboard
**Agente principal:** Backend + Frontend

| # | Tarea | Agente | Prioridad |
|---|-------|--------|-----------|
| 2.1 | Implementar proxy endpoint: /v1/chat/completions (OpenAI) | Backend | P0 |
| 2.2 | Implementar token counting con tiktoken | Backend | P0 |
| 2.3 | Implementar cost calculation (tokens × precio del modelo) | Backend | P0 |
| 2.4 | Logging asíncrono de usage_logs | Backend | P0 |
| 2.5 | Task Classifier (Nivel 1: reglas) | DataScience | P1 |
| 2.6 | CRUD de service API keys (hash SHA-256) | Backend + Security | P0 |
| 2.7 | CRUD de provider API keys (Fernet encrypted) | Backend + Security | P0 |
| 2.8 | Endpoints de dashboard: summary, spend-over-time, spend-by-model | Backend | P0 |
| 2.9 | Frontend: Login page | Frontend | P0 |
| 2.10 | Frontend: Dashboard con charts (Recharts) | Frontend | P0 |

### Sprint 3 (Semana 5-6): Alertas + API Keys UI + Deploy
**Agente principal:** Frontend + Security

| # | Tarea | Agente | Prioridad |
|---|-------|--------|-----------|
| 3.1 | Alert Engine: rate limiting + budget checks en Redis | Backend + Security | P0 |
| 3.2 | Circuit Breaker implementation | Security | P0 |
| 3.3 | Endpoint: alert rules CRUD + alert events history | Backend | P0 |
| 3.4 | Notificaciones: Email (SendGrid/Resend) | Backend | P1 |
| 3.5 | Frontend: Alerts Management page | Frontend | P0 |
| 3.6 | Frontend: API Keys Management + modal de creación | Frontend | P0 |
| 3.7 | Frontend: Settings (notifications tab) | Frontend | P1 |
| 3.8 | Audit log para acciones sensibles | Security | P0 |
| 3.9 | Deploy: Backend en Railway, Frontend en Vercel | Backend | P0 |
| 3.10 | Testing: tests unitarios mínimos para proxy, auth, key vault | Backend + Security | P0 |

---

## Fase 2: Post-Validación (Semanas 7-12)
Se activa solo si hay usuarios reales usando el MVP.

### Sprint 4-5 (Semana 7-10): Motor de Inteligencia + Más Proveedores
| # | Tarea | Agente | Prioridad |
|---|-------|--------|-----------|
| 4.1 | Proxy: soporte Anthropic (/v1/messages) | Backend | P0 |
| 4.2 | Proxy: soporte Google Gemini | Backend | P1 |
| 4.3 | Proxy: soporte Mistral | Backend | P1 |
| 4.4 | Benchmark Matrix: seed con datos públicos | DataScience | P0 |
| 4.5 | Suggestion Engine: batch diario de sugerencias | DataScience | P0 |
| 4.6 | Frontend: Panel de Sugerencias | Frontend | P0 |
| 4.7 | Frontend: Comparador de Modelos | Frontend | P1 |
| 4.8 | Notificaciones: Slack webhook | Backend | P0 |
| 4.9 | Tagging de costos por feature/departamento | Backend + Frontend | P1 |
| 4.10 | Stripe integration para billing | Backend | P0 |

### Sprint 6 (Semana 11-12): Pulido + Landing Page
| # | Tarea | Agente | Prioridad |
|---|-------|--------|-----------|
| 5.1 | Shadow Testing (Nivel 2 de quality score) | DataScience | P1 |
| 5.2 | Frontend: Landing Page | Frontend | P0 |
| 5.3 | Onboarding flow (3 pasos) | Frontend + Backend | P0 |
| 5.4 | RBAC completo (owner/admin/viewer) | Security | P1 |
| 5.5 | OAuth social login (Google/GitHub) | Backend + Security | P1 |
| 5.6 | Product Hunt launch preparation | — | P0 |

---

## Fase 3: Escalado (Mes 4+)
| Tarea | Agente |
|-------|--------|
| Feedback Loop (Nivel 3 quality score) | DataScience |
| Auto-routing: redirigir al modelo óptimo automáticamente | DataScience + Backend |
| Predicción de gastos con ML (forecasting) | DataScience |
| MFA (TOTP) | Security |
| Master Key rotation automática | Security |
| Multi-tenant con equipos | Backend |
| API pública para integraciones | Backend |
| Migración a AWS KMS | Security |

---

## Comandos de Claude Code por Agente

### Invocar agente frontend:
```
claude --agent .claude/agents/frontend-specialist.md "Implementa el componente KpiCard del dashboard"
```

### Invocar agente backend:
```
claude --agent .claude/agents/backend-specialist.md "Implementa el endpoint GET /api/v1/dashboard/summary"
```

### Invocar agente security:
```
claude --agent .claude/agents/security-specialist.md "Implementa el KeyVault con Fernet encryption"
```

### Invocar agente data science:
```
claude --agent .claude/agents/datascience-specialist.md "Implementa el Task Classifier con reglas"
```
