# Skill: Gestión Segura de API Keys

## Dos tipos de keys en el sistema

### 1. Service API Keys (nuestras)
- El cliente las usa para autenticarse contra nuestro proxy
- Se generan con `secrets.token_urlsafe(32)` con prefix `lcm_sk_live_`
- Se almacena SOLO el hash SHA-256 en la DB
- El prefix visible (lcm_sk_...***abc) se guarda para identificación
- La key completa se muestra UNA SOLA VEZ al momento de crearla
- Validación: hashear la key recibida y comparar contra el hash en DB

### 2. Provider API Keys (de los clientes)
- Las API Keys de OpenAI, Anthropic, Google, Mistral que el cliente nos confía
- Se cifran con Fernet (AES-128-CBC + HMAC) antes de almacenarse
- NUNCA se retornan completas en la API, solo el prefix
- Se descifran en memoria solo para hacer el forward (~100ms)
- El ciphertext se almacena en la columna `key_ciphertext` de `provider_api_keys`

## Ciclo de vida
1. **Ingesta:** Validar formato → test call al proveedor → cifrar → almacenar
2. **Uso:** Request llega → descifrar en memoria → forward → wipe
3. **Rotación:** Cada 90 días, re-cifrar todas las keys con nueva Master Key
4. **Revocación:** Marcar como revocada → flush Redis → audit log

## Regla de oro
La Master Key (MASTER_ENCRYPTION_KEY) vive ÚNICAMENTE en variables de entorno.
Generarla con: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
