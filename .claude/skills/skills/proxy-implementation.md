# Skill: Implementar Proxy LLM

## Contexto
El proxy es el core del producto. Es un endpoint que se comporta como un drop-in replacement de la API de OpenAI/Anthropic. El cliente solo cambia su base URL y todo su tráfico pasa por nosotros.

## Flujo completo de una request
1. Cliente envía POST /v1/chat/completions con su service API key
2. Validar service API key (hash SHA-256 contra DB, cache en Redis)
3. Check rate limit (sliding window en Redis)
4. Check budget limit (counter diario/mensual en Redis)
5. Contar tokens de entrada (tiktoken para OpenAI, estimación para otros)
6. Clasificar task_type del prompt (Task Classifier)
7. Descifrar provider API key (Fernet, en memoria ~100ms)
8. Forward request al proveedor con httpx.AsyncClient
9. Recibir response (soportar streaming SSE)
10. Contar tokens de salida
11. Calcular costo = (tokens_input × price_input + tokens_output × price_output) / 1_000_000
12. Retornar response al cliente (mismo formato exacto del proveedor)
13. Background task: guardar usage_log, evaluar alertas

## Streaming SSE
El proxy DEBE soportar streaming. La mayoría de apps usan stream=true.
```python
async def stream_proxy_response(provider_response):
    async for chunk in provider_response.aiter_bytes():
        yield chunk
    # Después del stream completo, contar tokens y loggear
```

## Compatibilidad
El response DEBE ser idéntico al del proveedor original. Si el cliente usa el SDK de OpenAI, debe funcionar sin cambios.
