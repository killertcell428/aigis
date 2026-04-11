"""Tests for billing plans and enforcement."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.billing.plans import (
    PLAN_LIMITS,
    PLAN_ORDER,
    get_limit,
    get_plan_limits,
    is_plan_at_least,
)


class TestPlanDefinitions:
    """Verify plan definitions are consistent."""

    def test_all_plans_defined(self):
        assert set(PLAN_LIMITS.keys()) == {"free", "pro", "business", "enterprise"}

    def test_plan_order(self):
        assert PLAN_ORDER == ["free", "pro", "business", "enterprise"]

    def test_free_plan_limits(self):
        limits = get_plan_limits("free")
        assert limits["max_users"] == 1
        assert limits["monthly_requests"] == 0
        assert limits["retention_days"] == 0
        assert limits["compliance_reports"] is False
        assert limits["sso"] is False

    def test_pro_plan_limits(self):
        limits = get_plan_limits("pro")
        assert limits["max_users"] == 5
        assert limits["monthly_requests"] == 500_000
        assert limits["retention_days"] == 90
        assert limits["compliance_reports"] is False

    def test_business_plan_limits(self):
        limits = get_plan_limits("business")
        assert limits["max_users"] == 50
        assert limits["monthly_requests"] == 5_000_000
        assert limits["retention_days"] == 365
        assert limits["compliance_reports"] is True
        assert limits["sso"] is True

    def test_enterprise_plan_unlimited(self):
        limits = get_plan_limits("enterprise")
        assert limits["max_users"] is None
        assert limits["monthly_requests"] is None
        assert limits["retention_days"] is None

    def test_unknown_plan_falls_back_to_free(self):
        limits = get_plan_limits("nonexistent")
        assert limits == PLAN_LIMITS["free"]


class TestGetLimit:
    def test_returns_specific_limit(self):
        assert get_limit("pro", "max_users") == 5

    def test_returns_none_for_unknown_key(self):
        assert get_limit("pro", "nonexistent") is None


class TestIsPlanAtLeast:
    def test_same_plan(self):
        assert is_plan_at_least("pro", "pro") is True

    def test_higher_plan(self):
        assert is_plan_at_least("business", "pro") is True

    def test_lower_plan(self):
        assert is_plan_at_least("free", "pro") is False

    def test_enterprise_meets_all(self):
        for plan in PLAN_ORDER:
            assert is_plan_at_least("enterprise", plan) is True

    def test_free_only_meets_free(self):
        assert is_plan_at_least("free", "free") is True
        assert is_plan_at_least("free", "pro") is False

    def test_unknown_plan_treated_as_free(self):
        assert is_plan_at_least("unknown", "free") is True
        assert is_plan_at_least("unknown", "pro") is False


class TestPlanHierarchy:
    """Verify request limits increase with each tier."""

    def test_request_limits_increase(self):
        free = get_plan_limits("free")["monthly_requests"]
        pro = get_plan_limits("pro")["monthly_requests"]
        biz = get_plan_limits("business")["monthly_requests"]
        # free < pro < business
        assert free < pro < biz

    def test_user_limits_increase(self):
        free = get_plan_limits("free")["max_users"]
        pro = get_plan_limits("pro")["max_users"]
        biz = get_plan_limits("business")["max_users"]
        assert free < pro < biz

    def test_retention_increases(self):
        free = get_plan_limits("free")["retention_days"]
        pro = get_plan_limits("pro")["retention_days"]
        biz = get_plan_limits("business")["retention_days"]
        assert free < pro < biz
