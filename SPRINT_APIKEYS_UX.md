# Sprint Fix — Service API Keys UX + Asignación a Proyectos
## LLM Cost Monitor | Prioridad Alta (bloquea FinOps feature)

---

## Bugs y Mejoras Identificadas

| # | Tipo | Descripción | Severidad |
|---|------|-------------|-----------|
| K-01 | Bug | No hay opción para asignar Service Key a un proyecto | 🔴 CRÍTICO |
| K-02 | Bug | Key se muestra una sola vez y no hay recuperación | 🟠 ALTO |
| K-03 | UX | Advertencia de copiar key es poco visible | 🟠 ALTO |

---

## Tarea K-01 — Asignar Service API Key a Proyecto

**Archivos:** `frontend/src/app/(dashboard)/api-keys/`, `backend/app/api/v1/`

```
[ ] Backend: agregar endpoint PATCH /api/v1/keys/service/{key_id}/assign
    Body: { project_id: string | null, team_id: string | null }
    - Validar que project_id pertenece a la organización del usuario
    - Retornar key actualizada

[ ] Frontend — tabla de Service API Keys:
    Agregar columna "Project" con un Select dropdown por fila
    - Opciones: "No project" + lista de proyectos de la org
    - Al cambiar → llamar al endpoint PATCH de asignación
    - Mostrar toast de confirmación: "Key assigned to [project name]"

[ ] Frontend — modal de creación de nueva key:
    Agregar campo opcional "Assign to project" (Select)
    - Si se selecciona, hacer PATCH de asignación después de crear la key

[ ] Frontend — vista detalle de Proyecto (/projects/[id]):
    Agregar tab o sección "Keys" que muestre las keys asignadas
    con botón para asignar keys adicionales desde ahí
```

---

## Tarea K-02 — Recuperación de Key via Código por Email

**Concepto:** El usuario puede revelar su key existente verificando
su identidad con un código OTP enviado al correo registrado.

**Archivos:** `backend/app/api/v1/keys/`, `backend/app/services/email.py`

### Backend

```
[ ] Crear endpoint: POST /api/v1/keys/service/{key_id}/reveal-request
    - Verificar que la key pertenece al usuario autenticado
    - Generar OTP de 6 dígitos (random.randint)
    - Guardar en Redis: key="reveal_otp:{key_id}:{user_id}" value=OTP ttl=300s (5 min)
    - Enviar email con el OTP al correo del usuario
    - Retornar: { message: "Code sent to j***@gmail.com" } (email parcialmente oculto)

[ ] Crear endpoint: POST /api/v1/keys/service/{key_id}/reveal-confirm
    Body: { otp: string }
    - Verificar OTP en Redis
    - Si válido → retornar la key descifrada (usar KeyVault para decrypt)
    - Si inválido → retornar 400 "Invalid or expired code"
    - Eliminar OTP de Redis tras uso exitoso (one-time use)

[ ] Template de email para el OTP:
    Asunto: "Your LLM Cost Monitor key reveal code"
    Body: código grande y visible + "expires in 5 minutes" + advertencia
          de que si no fuiste tú, cambia tu contraseña
```

### Frontend

```
[ ] En tabla de Service API Keys, agregar ícono de "ojo" por cada key
    Al hacer click → abrir modal "Reveal API Key"

[ ] Modal "Reveal API Key":
    Paso 1 — Solicitar código:
      - Texto: "We'll send a verification code to j***@gmail.com"
      - Botón: "Send Code"
      - Al click → llamar reveal-request

    Paso 2 — Ingresar código:
      - Input OTP de 6 dígitos (estilo cajitas individuales)
      - Countdown timer: "Code expires in 4:32"
      - Botón: "Verify & Reveal"
      - Al click → llamar reveal-confirm

    Paso 3 — Mostrar key:
      - Mostrar key completa en campo con fondo destacado
      - Botón de copiar con feedback visual (✓ Copied!)
      - Advertencia: "Store this key securely. Close this window when done."
      - Auto-ocultar después de 60 segundos
```

---

## Tarea K-03 — Advertencia Visual al Crear Service API Key

**Archivo:** `frontend/src/components/keys/NewKeyModal.tsx` (o similar)

```
[ ] Reemplazar el mensaje actual de advertencia por un banner de alto impacto:

    Diseño del banner:
    - Fondo: amarillo ámbar (#F59E0B) o rojo suave con ícono ⚠️
    - Borde llamativo alrededor de toda la sección de la key
    - Texto en negrita: "Copy your API key now — it won't be shown again"
    - Subtexto: "You can reveal it later by verifying your email"
    - La key debe mostrarse en un campo con:
        * Fondo contrastante (no el mismo oscuro del modal)
        * Botón de copiar grande y visible con ícono
        * Al copiar → cambiar botón a "✓ Copied!" en verde por 3 segundos

[ ] Deshabilitar el botón "Done" / "Close" durante 3 segundos al abrir
    el paso de mostrar la key, para forzar que el usuario la vea

[ ] Agregar checkbox obligatorio antes de cerrar:
    "☐ I have copied my API key and stored it securely"
    El botón de cerrar solo se habilita al marcar el checkbox
```

---

## Orden de Ejecución

```
Día 1:  K-03 → advertencia visual (más rápido, alto impacto inmediato)
        K-01 → asignación de keys a proyectos
Día 2:  K-02 backend → OTP en Redis + email
        K-02 frontend → modal de reveal con OTP
```

---

## Prompt para Claude Code

```
Implementa 3 fixes en el módulo de Service API Keys:

FIX 1 (K-03 — más urgente, empieza aquí):
En el modal de creación de Service API Key, mejorar drásticamente
la advertencia visual:
- Banner ámbar/amarillo con ícono ⚠️ y texto en negrita
- Key en campo con fondo contrastante + botón de copiar grande
- Checkbox obligatorio "I have copied my API key" antes de poder cerrar
- Botón Done deshabilitado hasta que el checkbox esté marcado

FIX 2 (K-01):
Agregar asignación de Service API Key a proyecto:
- Endpoint PATCH /api/v1/keys/service/{key_id}/assign
  Body: { project_id, team_id }
- En la tabla de API Keys, columna "Project" con Select dropdown
- En modal de creación, campo opcional "Assign to project"

FIX 3 (K-02):
Sistema de recuperación de key via OTP por email:
- POST /api/v1/keys/service/{key_id}/reveal-request → genera OTP, guarda
  en Redis con TTL 300s, envía email
- POST /api/v1/keys/service/{key_id}/reveal-confirm → verifica OTP,
  retorna key descifrada, elimina OTP de Redis
- Modal en frontend con 3 pasos: solicitar → ingresar OTP → ver key
- Input OTP estilo cajitas individuales de 6 dígitos
- Auto-ocultar key después de 60 segundos

Mantén código limpio, tipado con TypeScript en frontend y
Pydantic schemas en backend.
```

---

*Sprint generado: 14 Marzo 2026 | Bloquea: FinOps Cost Attribution feature*
