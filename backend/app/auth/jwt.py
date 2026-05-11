"""JWT token creation and verification."""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt as pyjwt
from passlib.context import CryptContext

from app.config import settings

# bcrypt__rounds=14 — 2026 baseline; raise periodically as hardware improves.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=14)

# Restrict accepted algorithms to HS256 only to defeat "alg: none" and
# algorithm-confusion attacks regardless of settings.algorithm typos.
_ALLOWED_ALGORITHMS = ["HS256"]


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: User ID (UUID as string).
        tenant_id: Tenant UUID as string.
        role: User role (admin | reviewer).
        expires_delta: Optional custom expiry.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Returns:
        Decoded payload dict.

    Raises:
        jwt.exceptions.PyJWTError: If token is invalid, expired, or missing required claims.
    """
    return pyjwt.decode(
        token,
        settings.secret_key,
        algorithms=_ALLOWED_ALGORITHMS,
        options={
            "require": ["exp", "sub", "tenant_id"],
        },
    )


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
