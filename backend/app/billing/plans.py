"""Plan definitions and limits for Aigis SaaS tiers."""
from __future__ import annotations

from typing import Any, Optional

PLAN_LIMITS: dict[str, dict[str, Any]] = {
    "free": {
        "max_users": 1,
        "monthly_requests": 0,
        "retention_days": 0,
        "max_custom_rules": 1,
        "max_api_keys": 1,
        "compliance_reports": False,
        "slack_notifications": False,
        "hitl_review": False,
        "sso": False,
    },
    "pro": {
        "max_users": 5,
        "monthly_requests": 500_000,
        "retention_days": 90,
        "max_custom_rules": None,  # Unlimited
        "max_api_keys": 5,
        "compliance_reports": False,
        "slack_notifications": True,
        "hitl_review": False,
        "sso": False,
    },
    "business": {
        "max_users": 50,
        "monthly_requests": 5_000_000,
        "retention_days": 365,
        "max_custom_rules": None,
        "max_api_keys": 50,
        "compliance_reports": True,
        "slack_notifications": True,
        "hitl_review": True,
        "sso": True,
    },
    "enterprise": {
        "max_users": None,  # Unlimited
        "monthly_requests": None,
        "retention_days": None,
        "max_custom_rules": None,
        "max_api_keys": None,
        "compliance_reports": True,
        "slack_notifications": True,
        "hitl_review": True,
        "sso": True,
    },
}

# Ordered from lowest to highest tier
PLAN_ORDER = ["free", "pro", "business", "enterprise"]


def get_plan_limits(plan: str) -> dict[str, Any]:
    """Return the limits dict for a given plan name."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def get_limit(plan: str, key: str) -> Optional[int | bool]:
    """Return a single limit value for a plan."""
    return get_plan_limits(plan).get(key)


def is_plan_at_least(current_plan: str, required_plan: str) -> bool:
    """Check if current_plan meets or exceeds required_plan tier."""
    current_idx = PLAN_ORDER.index(current_plan) if current_plan in PLAN_ORDER else 0
    required_idx = PLAN_ORDER.index(required_plan) if required_plan in PLAN_ORDER else 0
    return current_idx >= required_idx
