"""
Set required environment variables before any app imports.
RSA keys are generated fresh at test-session start — nothing is hardcoded.
"""
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def _generate_rsa_pair() -> tuple[str, str]:
    """Generate a temporary RSA-2048 key pair for the test session."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


_private_key, _public_key = _generate_rsa_pair()

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("MASTER_ENCRYPTION_KEY", "V4hg3c-dnfDUiJPbLE7-AnDXshC6cIsf7ebnxsKaPec=")
os.environ.setdefault("JWT_PRIVATE_KEY", _private_key)
os.environ.setdefault("JWT_PUBLIC_KEY", _public_key)
