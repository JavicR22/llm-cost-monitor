# Sprint Retrospectivo — Auth & Session Fixes
## LLM Cost Monitor | Prioridad Crítica (Pre-Clientes)

> **Contexto:** Se identificaron 4 bugs críticos que bloquean el onboarding de clientes reales.
> Este sprint debe completarse **antes** de cualquier campaña de adquisición.
> Estimado: 2–3 días de trabajo enfocado.

---

## Bugs Identificados

| # | Bug | Impacto | Severidad |
|---|-----|---------|-----------|
| B-01 | Campo email renderiza `[object Object]` en registro | Usuario no puede registrarse | 🔴 CRÍTICO |
| B-02 | OAuth con Google y GitHub no funciona | Pérdida de conversión ~60% | 🔴 CRÍTICO |
| B-03 | Sesión no persiste entre recargas o tabs | UX rota, usuario pierde contexto | 🟠 ALTO |
| B-04 | Ruta base `/` no redirige al login | Primer contacto con el producto confuso | 🟠 ALTO |
| B-05 | Rutas protegidas accesibles sin autenticación | Fallo de seguridad y UX | 🔴 CRÍTICO |

---

## Tarea R-01 — Fix: Bug `[object Object]` en campo email

**Agente:** Frontend  
**Archivos a revisar:** `frontend/src/app/(auth)/register/page.tsx` o el componente `RegisterForm`

### Diagnóstico
El estado del formulario recibe el objeto evento (`SyntheticEvent`) en lugar de `e.target.value`.
Causa típica: destructuring incorrecto o estado inicial como objeto en lugar de string.

### Checklist de implementación

```
[ ] 1. Revisar todos los onChange de los inputs del formulario:
        INCORRECTO: onChange={(e) => setEmail(e)}
        CORRECTO:   onChange={(e) => setEmail(e.target.value)}

[ ] 2. Verificar estado inicial del formulario:
        INCORRECTO: useState({ email: {}, fullName: {} })
        CORRECTO:   useState({ email: "", fullName: "", companyName: "", password: "" })

[ ] 3. Si usa react-hook-form, verificar el spread del register:
        INCORRECTO: <input {...register} />
        CORRECTO:   <input {...register("email")} />

[ ] 4. Agregar validación de tipo en el handler antes de setear estado:
        const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
          setForm(prev => ({ ...prev, [field]: e.target.value }))
        }

[ ] 5. Verificar que el <Input> de Shadcn/ui recibe `value` como string, no como objeto
```

### Práctica recomendada (React)
Usar un handler genérico tipado para evitar repetición:

```typescript
// ✅ Patrón limpio y reutilizable
const [form, setForm] = useState({
  email: "",
  fullName: "",
  companyName: "",
  password: "",
})

const handleField = (key: keyof typeof form) =>
  (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

// Uso: <Input onChange={handleField("email")} value={form.email} />
```

---

## Tarea R-02 — Implementar OAuth: Google y GitHub

**Agente:** Backend + Frontend  
**Archivos:** `backend/app/routers/auth.py`, `frontend/src/app/(auth)/`

### Backend — FastAPI

```
[ ] 1. Instalar dependencia:
        pip install authlib httpx

[ ] 2. Crear archivo: backend/app/core/oauth.py
        - Configurar cliente OAuth para Google (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
        - Configurar cliente OAuth para GitHub (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)

[ ] 3. En backend/app/routers/auth.py agregar endpoints:
        GET  /auth/google          → redirige a Google consent screen
        GET  /auth/google/callback → intercambia code por token, crea/recupera user, emite JWT
        GET  /auth/github          → redirige a GitHub OAuth
        GET  /auth/github/callback → intercambia code por token, crea/recupera user, emite JWT

[ ] 4. Lógica del callback (mismo para ambos providers):
        a. Intercambiar authorization_code por access_token con el provider
        b. Llamar al endpoint de userinfo del provider para obtener email + nombre
        c. Buscar user por email en DB:
           - Si existe → actualizar last_login, generar JWT
           - Si no existe → crear user con oauth_provider="google|github", generar JWT
        d. Redirigir a frontend: {FRONTEND_URL}/auth/callback?token=<JWT>

[ ] 5. Agregar variables al .env:
        GOOGLE_CLIENT_ID=
        GOOGLE_CLIENT_SECRET=
        GITHUB_CLIENT_ID=
        GITHUB_CLIENT_SECRET=
        FRONTEND_URL=http://localhost:3000

[ ] 6. En Google Cloud Console:
        - Authorized redirect URI: {BACKEND_URL}/auth/google/callback

[ ] 7. En GitHub Developer Settings:
        - Authorization callback URL: {BACKEND_URL}/auth/github/callback
```

### Frontend — Next.js

```
[ ] 8. Crear página: frontend/src/app/auth/callback/page.tsx
        - Leer ?token= de la URL (useSearchParams)
        - Guardar token en cookie httpOnly via Server Action o en localStorage como fallback
        - Redirigir a /dashboard

[ ] 9. En el componente de login/registro, conectar botones OAuth:
        const handleGoogle = () => {
          window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/google`
        }
        // Igual para GitHub

[ ] 10. Los botones Google y GitHub ya existen visualmente — solo conectar el onClick
```

---

## Tarea R-03 — Persistencia de Sesión entre Recargas y Tabs

**Agente:** Frontend  
**Archivos:** `frontend/src/lib/auth/`, `frontend/src/providers/`

### Diagnóstico
El JWT se almacena solo en memoria (estado de React). Al recargar, se pierde.

### Implementación

```
[ ] 1. Crear: frontend/src/lib/auth/token.ts
        Responsabilidad única: leer/escribir/borrar el token.

        export const TOKEN_KEY = "llm_monitor_token"

        export const setToken = (token: string) => {
          // Guardar en cookie (más seguro) o localStorage como fallback
          document.cookie = `${TOKEN_KEY}=${token}; path=/; max-age=604800; SameSite=Strict`
        }

        export const getToken = (): string | null => {
          // Leer de cookie
          const match = document.cookie.match(new RegExp(`${TOKEN_KEY}=([^;]+)`))
          return match ? match[1] : null
        }

        export const clearToken = () => {
          document.cookie = `${TOKEN_KEY}=; path=/; max-age=0`
        }

[ ] 2. Crear o actualizar: frontend/src/providers/AuthProvider.tsx
        - Al montar, leer token con getToken()
        - Validar expiración del JWT (decodificar payload, verificar exp)
        - Si válido → setUser(decodedPayload), setIsAuthenticated(true)
        - Si expirado → clearToken(), redirigir a /login

[ ] 3. Validar expiración del token sin librería externa:
        const isTokenExpired = (token: string): boolean => {
          try {
            const payload = JSON.parse(atob(token.split(".")[1]))
            return payload.exp * 1000 < Date.now()
          } catch {
            return true
          }
        }

[ ] 4. Envolver _app o layout.tsx con <AuthProvider>:
        // frontend/src/app/layout.tsx
        export default function RootLayout({ children }) {
          return (
            <html>
              <body>
                <AuthProvider>{children}</AuthProvider>
              </body>
            </html>
          )
        }

[ ] 5. Para sincronización entre tabs: escuchar storage event
        useEffect(() => {
          const handleStorageChange = (e: StorageEvent) => {
            if (e.key === TOKEN_KEY && !e.newValue) logout()
          }
          window.addEventListener("storage", handleStorageChange)
          return () => window.removeEventListener("storage", handleStorageChange)
        }, [])
```

---

## Tarea R-04 — Redirect: `/` debe mostrar login

**Agente:** Frontend  
**Archivos:** `frontend/src/app/page.tsx`, `frontend/src/middleware.ts`

### Opción A — Redirect en page.tsx (simple)

```typescript
// frontend/src/app/page.tsx
import { redirect } from "next/navigation"

export default function RootPage() {
  redirect("/login")  // Server-side redirect inmediato, sin flash
}
```

### Opción B — Middleware (recomendado, más robusto)

```
[ ] 1. Crear o actualizar: frontend/src/middleware.ts

        import { NextResponse } from "next/server"
        import type { NextRequest } from "next/server"

        const PUBLIC_ROUTES = ["/login", "/register", "/auth/callback"]
        const ROOT_ROUTE = "/"

        export function middleware(request: NextRequest) {
          const { pathname } = request.nextUrl
          const token = request.cookies.get("llm_monitor_token")?.value

          // Ruta raíz → siempre redirige
          if (pathname === ROOT_ROUTE) {
            return NextResponse.redirect(new URL("/login", request.url))
          }

          // Rutas protegidas sin token → login
          if (!PUBLIC_ROUTES.includes(pathname) && !token) {
            const loginUrl = new URL("/login", request.url)
            loginUrl.searchParams.set("from", pathname)  // Para redirigir de vuelta al login
            return NextResponse.redirect(loginUrl)
          }

          // Ya autenticado intentando ir a login/register → dashboard
          if (PUBLIC_ROUTES.includes(pathname) && token) {
            return NextResponse.redirect(new URL("/dashboard", request.url))
          }

          return NextResponse.next()
        }

        export const config = {
          matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
        }
```

---

## Tarea R-05 — Rutas Protegidas: bloquear acceso sin sesión

**Agente:** Frontend  
**Archivos:** `frontend/src/middleware.ts`, `frontend/src/components/auth/ProtectedRoute.tsx`

### Capa 1: Middleware (ya cubierto en R-04)
El middleware de Next.js es la primera y más robusta línea de defensa.
Con R-04 completado, esto ya está cubierto a nivel de servidor.

### Capa 2: HOC `withAuth` (defensa en profundidad en cliente)

```
[ ] 1. Crear: frontend/src/components/auth/withAuth.tsx
        import { useAuth } from "@/providers/AuthProvider"
        import { useRouter } from "next/navigation"
        import { useEffect } from "react"

        export function withAuth<T extends object>(Component: React.ComponentType<T>) {
          return function AuthenticatedComponent(props: T) {
            const { isAuthenticated, isLoading } = useAuth()
            const router = useRouter()

            useEffect(() => {
              if (!isLoading && !isAuthenticated) {
                router.replace("/login")
              }
            }, [isAuthenticated, isLoading])

            if (isLoading) return <PageLoader />   // Evitar flash de contenido
            if (!isAuthenticated) return null

            return <Component {...props} />
          }
        }

[ ] 2. Aplicar en páginas protegidas:
        // frontend/src/app/dashboard/page.tsx
        function DashboardPage() { ... }
        export default withAuth(DashboardPage)

        // Aplicar igual en: /logs, /api-keys, /alerts, /settings

[ ] 3. Verificar que el layout de dashboard también comprueba autenticación:
        // frontend/src/app/(dashboard)/layout.tsx
        // Usar useAuth() y redirigir si !isAuthenticated
```

---

## Orden de Ejecución Recomendado

```
Día 1 (mañana):  R-01 → Fix email bug        (~30 min)
Día 1 (tarde):   R-04 → Redirect en /        (~30 min)
                 R-05 → Rutas protegidas      (~1 hora)
Día 2 (mañana):  R-03 → Persistencia sesión  (~2 horas)
Día 2 (tarde):   R-02 → OAuth Google/GitHub  (~3-4 horas, requiere setup externo)
Día 3:           QA completo del flujo end-to-end
```

> R-02 (OAuth) es el más costoso en tiempo. Requiere crear apps en Google Cloud Console
> y GitHub Developer Settings. Planificar con anticipación.

---

## QA — Checklist Final

Antes de declarar el sprint completo, verificar cada escenario:

```
REGISTRO
[ ] Formulario con email/password funciona sin errores
[ ] Botón Google redirige y completa registro
[ ] Botón GitHub redirige y completa registro
[ ] Usuario duplicado muestra mensaje de error claro

SESIÓN
[ ] Login exitoso guarda token
[ ] Recargar la página mantiene la sesión activa
[ ] Abrir nueva tab mantiene la sesión
[ ] Cerrar sesión en una tab la cierra en otras tabs

RUTAS
[ ] http://localhost:3000/ → redirige a /login automáticamente
[ ] http://localhost:3000/dashboard sin login → redirige a /login
[ ] http://localhost:3000/api-keys sin login → redirige a /login
[ ] http://localhost:3000/login con sesión activa → redirige a /dashboard
[ ] Token expirado → redirige a /login y limpia cookie

OAUTH
[ ] Callback con token válido redirige a /dashboard
[ ] Callback con error muestra mensaje apropiado
```

---

## Variables de Entorno Nuevas Requeridas

```bash
# backend/.env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
FRONTEND_URL=http://localhost:3000   # Producción: https://tu-dominio.vercel.app

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

*Sprint generado: Pre-Fase 2 | Bloquea: adquisición de clientes reales*
