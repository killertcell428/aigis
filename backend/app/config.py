"""Application configuration using pydantic-settings."""
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Look for .env in backend/ first, then project root
_config_path = Path(__file__).resolve()
_backend_env = _config_path.parents[2] / ".env" if len(_config_path.parents) > 2 else None
_root_env = _config_path.parents[3] / ".env" if len(_config_path.parents) > 3 else None
_env_file = (
    str(_backend_env) if _backend_env and _backend_env.exists()
    else str(_root_env) if _root_env and _root_env.exists()
    else ".env"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Aigis"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "production"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aigis"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/aigis"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY_32CHARS"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Upstream LLM
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str = ""

    # Demo mode — mock LLM responses (no real API key needed)
    demo_mode: bool = False

    # Review SLA
    review_sla_minutes: int = 30  # escalate if not reviewed within 30 min
    review_sla_fallback: str = "block"  # block | allow | escalate

    # Risk thresholds
    risk_low_max: int = 30
    risk_medium_max: int = 60
    risk_high_max: int = 80
    # Critical: 81-100

    # Auto-block threshold (skip review, block immediately)
    auto_block_threshold: int = 81  # Critical

    # Auto-allow threshold (skip review, allow immediately)
    auto_allow_threshold: int = 30  # Low

    # Stripe billing
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro_monthly: str = ""
    stripe_price_business_monthly: str = ""

    # Billing enforcement mode: "strict" blocks, "warn" logs only
    billing_enforcement_mode: str = "warn"

    # CORS — comma-separated origins. Use "*" only for local dev (debug=True).
    cors_allowed_origins: str = "http://localhost:3000"

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, v: str, info) -> str:
        # Allow weak defaults only outside production. In production, reject
        # the placeholder and any short/obviously-demo value.
        env = (info.data.get("environment") or "production").lower()
        if env != "production":
            return v
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 chars in production")
        bad_prefixes = ("CHANGE_ME", "demo_secret", "changeme", "your-secret")
        if any(v.startswith(p) for p in bad_prefixes):
            raise ValueError("SECRET_KEY must not use a placeholder value in production")
        return v

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, v: str, info) -> str:
        env = (info.data.get("environment") or "production").lower()
        if env != "production":
            return v
        # Reject default ":postgres@" credential in prod.
        if ":postgres@" in v or "user=postgres password=postgres" in v:
            raise ValueError(
                "DATABASE_URL uses default 'postgres:postgres' credentials in production"
            )
        return v


settings = Settings()
