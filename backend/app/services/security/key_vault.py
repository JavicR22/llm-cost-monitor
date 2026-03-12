import hashlib
import secrets
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class KeyVaultError(Exception):
    pass


class KeyVault:
    """
    Handles all encryption/decryption of sensitive values.

    - Provider API keys (OpenAI/Anthropic/etc): Fernet AES-128-CBC + HMAC
    - Service API keys: SHA-256 hash (one-way, for validation only)
    - Notification channel configs: Fernet (same as provider keys)

    The MASTER_ENCRYPTION_KEY lives only in env vars — never in code or DB.
    """

    def __init__(self, master_key: str) -> None:
        try:
            self._fernet = Fernet(master_key.encode())
        except Exception as exc:
            raise KeyVaultError("Invalid MASTER_ENCRYPTION_KEY format") from exc

    # ------------------------------------------------------------------
    # Fernet encryption (provider keys, notification configs)
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string. Returns base64 ciphertext."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a ciphertext string.
        The decrypted value should live in memory only for the duration
        of the forwarded request (~100ms) — never log or persist it.
        """
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:
            raise KeyVaultError("Decryption failed — invalid ciphertext or wrong master key") from exc

    # ------------------------------------------------------------------
    # Service API key generation + validation (SHA-256, one-way)
    # ------------------------------------------------------------------

    @staticmethod
    def generate_service_key() -> tuple[str, str, str]:
        """
        Generate a new service API key.

        Returns:
            (raw_key, key_hash, key_prefix)
            - raw_key: shown to the user ONCE, never stored
            - key_hash: SHA-256 hex, stored in DB for validation
            - key_prefix: shown in UI for identification (lcm_sk_...***abc)
        """
        raw_key = f"lcm_sk_live_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = KeyVault.extract_prefix(raw_key)
        return raw_key, key_hash, key_prefix

    @staticmethod
    def hash_service_key(raw_key: str) -> str:
        """Hash an incoming service key for DB lookup."""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Prefix extraction (safe to display in UI)
    # ------------------------------------------------------------------

    @staticmethod
    def extract_prefix(key: str, visible_start: int = 12, visible_end: int = 4) -> str:
        """
        Returns a safe prefix for display: 'lcm_sk_live_...***abcd'
        Never exposes enough of the key to be usable.
        """
        if len(key) <= visible_start + visible_end:
            return key[:4] + "...***"
        return key[:visible_start] + "...***" + key[-visible_end:]


@lru_cache(maxsize=1)
def get_key_vault() -> KeyVault:
    """Singleton — instantiated once at startup, reused across requests."""
    return KeyVault(settings.MASTER_ENCRYPTION_KEY)
