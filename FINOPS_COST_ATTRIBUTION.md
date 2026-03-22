# Feature: FinOps — Cost Attribution por Capas
## LLM Cost Monitor | Adición al MVP

> **Concepto:** Jerarquía de atribución de costos LLM inspirada en FinOps cloud.
> Cualquier herramienta (app, CLI, scripts) que pase por el proxy queda registrada
> y atribuida a su capa correspondiente.

---

## Modelo de Capas

```
Organización
    └── Proyecto (Capa 1)
            └── Equipo (Capa 2)  ← solo si org es mediana/grande
                    └── Desarrollador (Capa 3)
```

**Caso pequeño** (startup, freelancer):
```
Proyecto → Desarrollador directo
```

**Caso mediano/grande** (empresa con equipos):
```
Proyecto → Equipo (Frontend/Backend/IA-ML) → Desarrollador
```

---

## Cambios en Base de Datos

### Tarea F-01 — Nuevos modelos SQLAlchemy

```
[ ] Crear modelo: Project
    - id, organization_id, name, description
    - budget_limit (opcional), created_at

[ ] Crear modelo: Team
    - id, project_id, name
    - budget_limit (opcional)

[ ] Actualizar modelo: ServiceAPIKey
    - Agregar: project_id (FK → Project, nullable)
    - Agregar: team_id (FK → Team, nullable)
    - Agregar: owner_user_id (FK → User, nullable)

[ ] Actualizar modelo: UsageLog
    - Agregar: project_id (nullable)
    - Agregar: team_id (nullable)
    - Agregar: user_id (nullable)

[ ] Generar migración Alembic y aplicar:
    alembic revision --autogenerate -m "add_finops_layers"
    alembic upgrade head
```

---

## Backend — API Endpoints

### Tarea F-02 — CRUD de Proyectos y Equipos

```
[ ] POST   /api/v1/projects          → crear proyecto
[ ] GET    /api/v1/projects          → listar proyectos de la org
[ ] PATCH  /api/v1/projects/{id}     → editar nombre/budget
[ ] DELETE /api/v1/projects/{id}     → eliminar

[ ] POST   /api/v1/projects/{id}/teams     → crear equipo en proyecto
[ ] GET    /api/v1/projects/{id}/teams     → listar equipos
[ ] PATCH  /api/v1/teams/{id}              → editar equipo
[ ] DELETE /api/v1/teams/{id}              → eliminar
```

### Tarea F-03 — Asignar Service API Key a capa

```
[ ] PATCH /api/v1/keys/service/{key_id}/assign
    Body: { project_id, team_id (opcional), owner_user_id (opcional) }

[ ] Al crear ServiceAPIKey, permitir pasar project_id y team_id opcionales
```

### Tarea F-04 — Endpoints de reporte por capa

```
[ ] GET /api/v1/reports/projects
    → costo total por proyecto en rango de fechas

[ ] GET /api/v1/reports/projects/{id}/teams
    → costo por equipo dentro de un proyecto

[ ] GET /api/v1/reports/projects/{id}/members
    → costo por desarrollador dentro de un proyecto

[ ] GET /api/v1/reports/summary
    → vista global: organización → proyectos → equipos

Parámetros comunes: ?from=&to=&group_by=day|week|month
```

### Tarea F-05 — Propagar capas al logging del proxy

```
[ ] En proxy service, al recibir request con ServiceAPIKey:
    - Leer project_id, team_id, owner_user_id de la key
    - Incluirlos al crear el UsageLog

[ ] Esto hace que cualquier herramienta (Gemini CLI, Cursor, scripts)
    quede automáticamente atribuida a su capa sin cambios adicionales
```

---

## Frontend — UI

### Tarea F-06 — Página de Proyectos

```
[ ] Ruta: /projects
[ ] Tabla con columnas: Nombre, Equipos, Keys asignadas, Gasto total, Budget
[ ] Botón: + New Project → modal con nombre y budget_limit opcional
[ ] Click en proyecto → vista detalle con sus equipos y keys
```

### Tarea F-07 — Vista detalle de Proyecto

```
[ ] Ruta: /projects/[id]
[ ] KPIs: Gasto total, Requests, Tokens, % del budget usado
[ ] Chart: gasto diario del proyecto (Recharts)
[ ] Tabs:
    - Equipos: tabla con gasto por equipo
    - Desarrolladores: tabla con gasto por dev
    - Keys: keys asignadas a este proyecto
[ ] Barra de progreso visual si tiene budget_limit definido
```

### Tarea F-08 — Asignación de keys a proyectos

```
[ ] En API Keys Management, agregar columna "Proyecto" en la tabla
[ ] Dropdown para asignar/cambiar proyecto desde la misma tabla
[ ] Al crear nueva key, agregar selector de proyecto y equipo opcionales
```

### Tarea F-09 — Dashboard global actualizado

```
[ ] Agregar sección "Spend by Project" con chart de barras
[ ] Reemplazar o complementar "Spend by Model" con vista por proyecto
[ ] Indicador visual si algún proyecto supera su budget_limit
```

---

## Orden de Ejecución

```
Día 1:  F-01 → modelos DB + migración
        F-02 → CRUD proyectos y equipos
Día 2:  F-03 → asignación de keys
        F-04 → endpoints de reporte
        F-05 → logging del proxy con capas
Día 3:  F-06 → página /projects
        F-07 → detalle de proyecto
Día 4:  F-08 → asignación desde UI de keys
        F-09 → dashboard actualizado
```

---

## Prompt para Claude Code — Inicio

```
Implementa el sistema de Cost Attribution por capas (FinOps) en LLM Cost Monitor.

La jerarquía es: Organización → Proyecto → Equipo → Desarrollador.
Una ServiceAPIKey puede asignarse a un Proyecto y opcionalmente a un Equipo.
Al pasar por el proxy, cada request hereda esas capas y se registra en UsageLog.

Empieza por F-01: crear los modelos Project y Team en SQLAlchemy,
actualizar ServiceAPIKey y UsageLog con los nuevos FK opcionales,
y generar + aplicar la migración de Alembic.

Archivos a crear/modificar:
- backend/app/models/project.py (nuevo)
- backend/app/models/team.py (nuevo)
- backend/app/models/service_key.py (agregar project_id, team_id)
- backend/app/models/usage_log.py (agregar project_id, team_id, user_id)
- Migración Alembic

Mantén todos los FK como nullable para no romper keys existentes.
```

---

*Feature diseñada: 14 Marzo 2026 | Target: MVP pre-clientes*
