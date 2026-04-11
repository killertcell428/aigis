"""Policies package."""
from app.policies.manager import create_default_policy, get_active_policy

__all__ = ["get_active_policy", "create_default_policy"]
