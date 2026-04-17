"""API key generation and validation for proxy authentication."""
import hashlib
import hmac
import secrets

from app.config import settings


def _hmac_key() -> bytes:
    # Derive the HMAC secret from the app secret_key. Using a fixed label
    # keeps the API-key hash distinct from any other HMAC domain.
    return hashlib.sha256(b"aigis.api_key.v1|" + settings.secret_key.encode()).digest()


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key.

    Returns:
        Tuple of (raw_key, hashed_key).
        Store only the hash; return the raw key once to the user.
    """
    raw = f"aig_{secrets.token_urlsafe(32)}"
    hashed = hash_api_key(raw)
    return raw, hashed


def hash_api_key(raw_key: str) -> str:
    """Hash an API key with HMAC-SHA256 keyed by the app secret."""
    return hmac.new(_hmac_key(), raw_key.encode(), hashlib.sha256).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Constant-time verify a raw API key against its stored hash."""
    return hmac.compare_digest(hash_api_key(raw_key), stored_hash)
