# Skill: Alert Engine y Circuit Breaker

## 4 Niveles de protección (en orden de ejecución)

### Nivel 1: Rate Limiting
- Sliding window counter en Redis
- Key: `ratelimit:{org_id}:{window}`
- Planes: Free=60/min, Starter=200/min, Pro=1000/min
- Si excede → HTTP 429 con header Retry-After

### Nivel 2: Budget Limits
- Counter acumulativo en Redis: `budget:{org_id}:daily:{YYYY-MM-DD}` y `budget:{org_id}:monthly:{YYYY-MM}`
- Incrementar en cada request con el costo calculado
- Soft limit (80%): enviar alerta, NO bloquear
- Hard limit (100%): BLOQUEAR, retornar HTTP 429 con detalle

### Nivel 3: Anomaly Detection
- Calcular promedio de gasto/hora últimos 7 días (stored en Redis, actualizado cada hora)
- Si gasto última hora > 3x promedio → disparar alerta
- NO bloquea (soft, el owner decide)

### Nivel 4: Circuit Breaker
- Sliding window en Redis: `circuit:{org_id}:{5min_window}`
- Si gasto en ventana > threshold configurado → BLOQUEO AUTOMÁTICO
- Key de bloqueo: `circuit_breaker:{org_id}:active` con TTL
- Solo se desbloquea manualmente (DELETE de la key en Redis via API)
- Notificar por TODOS los canales simultáneamente

## Flujo de evaluación en cada request
```
Rate Limit check → Budget check → Anomaly check → [Si pasa todo] → Forward
                                                  → [Si falla alguno] → HTTP 429
```

## Alert Events
Cada alerta disparada se registra en `alert_events` con:
- severity (info/warning/critical)
- type (soft_limit/hard_limit/anomaly/circuit_breaker)
- triggered_value (cuánto gastó)
- threshold_value (cuál era el límite)
- notification_channels (por dónde se notificó)
