from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ------------------------------------------------------------------
# Password hashing (bcrypt, no passlib)
# ------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ------------------------------------------------------------------
# JWT RS256
# ------------------------------------------------------------------

def _pem(raw: str) -> str:
    """Normalize PEM keys: support literal \\n in env vars."""
    return raw.replace("\\n", "\n")


def create_access_token(user_id: str, org_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload: dict[str, Any] = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, _pem(settings.JWT_PRIVATE_KEY), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, _pem(settings.JWT_PRIVATE_KEY), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT. Raises JWTError on invalid/expired token.
    Use the public key so this can safely run on read-only replicas.
    """
    return jwt.decode(token, _pem(settings.JWT_PUBLIC_KEY), algorithms=[settings.JWT_ALGORITHM])
