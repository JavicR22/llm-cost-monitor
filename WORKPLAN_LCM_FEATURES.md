# WORKPLAN: LLM Cost Monitor — Feature Fixes & Enhancements

> Lee este archivo completamente antes de escribir código. Sigue el orden de las tareas.
> Al terminar cada tarea, marca con `[x]` y confirma en el chat.

---

## Contexto del Proyecto

**Stack:** FastAPI (backend) · Next.js 14 (frontend) · PostgreSQL · Redis  
**Design System:** Deep navy `#0F172A` · Electric blue `#3B82F6` · Emerald `#10B981` · Amber `#F59E0B` · Red `#EF4444` · Inter typography  
**Jerarquía:** Organization → Project → Team → Developer  

---

## TAREA 1 — Fix: Asignación de proyecto a usuario no se refleja en el proyecto

**Problema:** Cuando el admin asigna un proyecto a un usuario, el proyecto no actualiza su lista de miembros ni sus contadores.

### Backend
- [ ] Revisar el endpoint `POST /api/projects/{project_id}/members` (o equivalente de asignación).
- [ ] Asegurarse de que al asignar un usuario a un proyecto, se inserte correctamente en la tabla `project_members` (o la relación equivalente).
- [ ] Después de la inserción, invalidar el caché Redis de ese proyecto (key: `project:{project_id}:summary` o similar).
- [ ] Retornar el proyecto actualizado con el conteo de miembros correcto en la respuesta.

### Frontend
- [ ] Después de la llamada exitosa al endpoint de asignación, hacer `revalidate` o `refetch` del query del proyecto.
- [ ] Actualizar el store/contexto local para que el contador **Members** en el dashboard del proyecto se incremente inmediatamente (optimistic update).
- [ ] Si usas React Query / SWR: llamar `queryClient.invalidateQueries(['project', projectId])` al resolver la mutación.

---

## TAREA 2 — Vistas diferenciadas por rol de usuario

**Regla:** Los roles posibles son `admin`, `project_leader` y `developer`.

### Backend
- [ ] Verificar que el JWT o la sesión incluya el campo `role` y `assigned_project_id` (para developers).
- [ ] Crear/ajustar middleware `require_role(roles: list[str])` que proteja rutas según rol.
- [ ] Endpoint `GET /api/me` debe retornar: `{ id, name, email, role, assigned_project_id, assigned_team_id }`.

### Frontend — Lógica de routing por rol
- [ ] En el layout principal (`/app/dashboard/layout.tsx` o equivalente), leer el rol del usuario autenticado.
- [ ] Implementar la siguiente redirección automática al login exitoso:
  ```
  admin / project_leader  →  /dashboard/admin
  developer               →  /dashboard/developer
  ```
- [ ] **Vista Developer (`/dashboard/developer`):**
  - Mostrar SOLO el proyecto al que está asignado.
  - Mostrar SOLO los equipos de ese proyecto.
  - Mostrar sus propias métricas: spend (30d), requests, tokens.
  - NO mostrar navegación de otros proyectos ni gestión de usuarios.
- [ ] **Vista Admin/Leader (`/dashboard/admin`):**
  - Acceso completo (ver Tarea 5).
- [ ] Proteger rutas con un componente `<RoleGuard allowedRoles={['admin', 'project_leader']} />` que redirija si el rol no coincide.

---

## TAREA 3 — Service API Keys por desarrollador

**Objetivo:** Cada developer tiene su propia Service API Key que el sistema usa para atribuirle costos individuales.

### Backend
- [ ] Crear tabla (si no existe):
  ```sql
  CREATE TABLE developer_api_keys (
      id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      key_prefix  VARCHAR(20) NOT NULL,          -- e.g. "lcm_sk_live_..."
      key_hash    TEXT NOT NULL,                 -- Fernet-encrypted full key
      label       VARCHAR(100),
      is_active   BOOLEAN DEFAULT TRUE,
      created_at  TIMESTAMPTZ DEFAULT NOW(),
      last_used_at TIMESTAMPTZ,
      UNIQUE(user_id)                            -- un developer = una key activa
  );
  ```
- [ ] Endpoint `POST /api/developer/keys/generate`:
  - Solo ejecutable una vez por developer (o revocar + regenerar).
  - Generar key con formato `lcm_sk_live_{uuid4_hex}`.
  - Almacenar hash Fernet. **Nunca** guardar el valor plano.
  - Retornar `{ key_plain: "lcm_sk_live_...", created_at }` — único momento donde se expone el valor.
- [ ] Endpoint `GET /api/developer/keys/me`:
  - Retorna `{ key_prefix: "lcm_sk_live_...***XYZ", created_at, last_used_at, is_active }`.
  - **Nunca** retorna el valor completo.
- [ ] Endpoint `DELETE /api/developer/keys/me` — revocar key actual.
- [ ] Al recibir una request con una Service Key en el proxy, identificar al developer por key y atribuirle el costo.

### Frontend
- [ ] En el perfil del developer, mostrar sección **"My API Key"** con: prefijo enmascarado, fecha de creación, botón **Revoke & Regenerate**.

---

## TAREA 4 — Modal "First-Time API Key" (solo se muestra una vez)

**Objetivo:** Al primer login del developer, si no tiene key generada, mostrarle un modal que la genere y la muestre una única vez.

### Backend
- [ ] Campo `has_seen_key_modal BOOLEAN DEFAULT FALSE` en tabla `users` (o en `developer_api_keys`).
- [ ] Al llamar `POST /api/developer/keys/generate`, retornar la key en texto plano **solo en esa respuesta**.
- [ ] Marcar `has_seen_key_modal = TRUE` en esa misma transacción.

### Frontend
- [ ] Al cargar `/dashboard/developer`, verificar con `GET /api/me` si `has_seen_key_modal = FALSE`.
- [ ] Si es `FALSE`, llamar automáticamente a `POST /api/developer/keys/generate` y abrir el modal.
- [ ] **Diseño del Modal (usar Frontend Design Skill):**
  - Fondo overlay oscuro con blur.
  - Ícono de advertencia en amber `#F59E0B`.
  - Título: **"Tu API Key — Guárdala ahora"**
  - Texto: *"Esta es la única vez que verás tu Service API Key completa. Cópiala y guárdala en un lugar seguro. No podremos mostrártela de nuevo."*
  - Campo de texto read-only con la key completa + botón **"Copiar"** (con feedback visual ✓).
  - Checkbox obligatorio: **"Entiendo que esta key no se volverá a mostrar"**.
  - Botón **"Continuar"** habilitado solo cuando el checkbox esté marcado.
  - Al cerrar, `has_seen_key_modal` ya está en `TRUE` — el modal nunca vuelve a aparecer.
- [ ] Guardar estado del modal en `localStorage` como respaldo (`lcm_key_acknowledged_{userId}`).

---

## TAREA 5 — Dashboard Admin/Leader: Analytics avanzado

> **IMPORTANTE para Claude Code:** Para esta tarea, aplicar el **Frontend Design Skill** (`/mnt/skills/public/frontend-design/SKILL.md`) y principios de **visualización de datos científicos**. El dashboard debe ser visualmente excepcional, con gráficas interactivas, elegante y profesional. Usar la paleta del design system del proyecto.

### Backend — Endpoints de analytics
- [ ] `GET /api/analytics/overview` → `{ total_spend_30d, total_requests_30d, active_projects, active_developers, spend_trend_pct }`
- [ ] `GET /api/analytics/projects` → lista de proyectos con `{ id, name, spend_30d, requests_30d, teams_count, members_count, budget, budget_used_pct }`
- [ ] `GET /api/analytics/projects/{project_id}/teams` → equipos del proyecto con métricas por equipo
- [ ] `GET /api/analytics/projects/{project_id}/developers` → developers con `{ name, email, spend_30d, requests_30d, tokens_30d, last_active }`
- [ ] `GET /api/analytics/spend/timeseries?project_id=&range=7d|30d|90d` → serie temporal de gasto diario
- [ ] `GET /api/analytics/models/usage` → desglose de gasto por modelo LLM (gpt-4o, claude-3-5, etc.)
- [ ] Todos los endpoints requieren rol `admin` o `project_leader` (middleware).

### Frontend — Dashboard Admin (`/dashboard/admin`)

**Layout general:**
- [ ] Sidebar izquierdo con navegación: Overview · Projects · Teams · Developers · Settings.
- [ ] Header con: nombre del org, selector de rango de fechas (7d / 30d / 90d), avatar del admin.

**Sección Overview (página principal):**
- [ ] **KPI Cards** (4 cards en fila):
  - Total Spend (30d) con indicador de tendencia (↑↓ vs período anterior)
  - Total Requests
  - Active Developers
  - Budget Utilization (% global)
- [ ] **Gráfica principal:** Line chart de gasto diario acumulado por proyecto (multi-line, una línea por proyecto, colores distintivos). Usar **Recharts** o **Chart.js**.
- [ ] **Gráfica secundaria:** Donut/Pie chart de distribución de gasto por modelo LLM.

**Sección Projects:**
- [ ] Tabla interactiva de proyectos con columnas: Nombre · Spend (30d) · Requests · Teams · Members · Budget Used (progress bar) · Acciones.
- [ ] Al hacer click en un proyecto → expandir o navegar a vista detallada del proyecto.

**Vista detallada de Proyecto (`/dashboard/admin/projects/[id]`):**
- [ ] Header con nombre del proyecto + métricas resumen.
- [ ] **Tab "Teams":**
  - Cards por equipo con: nombre, spend (30d), requests, members count.
  - Bar chart comparativo de gasto entre equipos.
- [ ] **Tab "Developers":**
  - Tabla con: nombre, email, spend (30d) con mini sparkline, requests, tokens, última actividad.
  - Ordenable por cualquier columna.
- [ ] **Tab "Spend Timeline":**
  - Line/Area chart de gasto diario del proyecto con selector de rango.
  - Anotaciones en picos de gasto.
- [ ] **Budget Tracker:**
  - Progress bar animada (color: verde → amber → rojo según % usado).
  - Proyección de gasto al fin del período basada en tendencia actual.

**Diseño visual (aplicar Frontend Design Skill):**
- [ ] Tema: dark (`#0F172A` base), cards con `#1E293B`, borders `#334155`.
- [ ] Tipografía: combinar una display font característica para títulos + fuente monoespaciada para valores numéricos/keys.
- [ ] Micro-animaciones en KPI cards al cargar (count-up animation para valores).
- [ ] Hover states en filas de tabla con highlight sutil.
- [ ] Gráficas con tooltips customizados que muestren desglose completo.
- [ ] Responsive: funcionar en 1280px+ (desktop first, es herramienta B2B).
- [ ] Empty states elegantes cuando no hay datos.

---

## Orden de Implementación Recomendado

```
1. TAREA 1  →  Fix crítico de asignación (más sencillo, desbloquea tests)
2. TAREA 3  →  Modelo de datos de API Keys (base para Tarea 4)
3. TAREA 4  →  Modal first-time (depende de Tarea 3)
4. TAREA 2  →  Vistas por rol (depende de que keys y asignación funcionen)
5. TAREA 5  →  Dashboard Admin (mayor esfuerzo, hacerlo al final)
```

---

## Notas técnicas

- **Fernet encryption:** Usar `cryptography` lib de Python. La SECRET_KEY de Fernet debe estar en variables de entorno (`LCM_FERNET_KEY`).
- **Redis invalidation:** Prefijo de keys: `lcm:project:{id}:*` para invalidación por proyecto.
- **No romper endpoints existentes:** Todos los cambios de BD deben tener migraciones Alembic.
- **Tests:** Agregar al menos un test unitario por endpoint nuevo en `/tests/`.
- **Logs:** Cada generación/revocación de API Key debe quedar en logs de auditoría.

---

## Archivos clave a revisar antes de empezar

```
/backend/app/models/          # Modelos SQLAlchemy
/backend/app/routers/         # Routers FastAPI existentes
/backend/app/core/security.py # Lógica de auth y Fernet
/frontend/src/app/dashboard/  # Páginas del dashboard
/frontend/src/components/     # Componentes reutilizables
/frontend/src/lib/api.ts      # Cliente API
```

---

*Generado: 2026-03-17 | Proyecto: LLM Cost Monitor | Autor: Claude*
