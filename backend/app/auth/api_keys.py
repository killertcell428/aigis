"""API key generation and validation for proxy authentication."""
import hashlib
import secrets
import uuid


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
    """Hash an API key for secure storage (SHA-256)."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Verify a raw API key against its stored hash."""
    return hash_api_key(raw_key) == stored_hash
