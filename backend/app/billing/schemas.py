"""Pydantic schemas for Aigis billing endpoints."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, HttpUrl


class CheckoutRequest(BaseModel):
    """Request body for creating a Stripe Checkout session."""

    plan: Literal["pro", "business"]
    success_url: str
    cancel_url: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "plan": "pro",
                "success_url": "https://app.aigis.dev/dashboard?checkout=success",
                "cancel_url": "https://app.aigis.dev/pricing",
            }
        }
    }


class CheckoutResponse(BaseModel):
    """Response body containing the Stripe Checkout redirect URL."""

    url: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://checkout.stripe.com/pay/cs_live_xxxxxxxxxxxxxxxx"
            }
        }
    }


class SubscriptionStatus(BaseModel):
    """Current subscription status for a customer."""

    plan: str
    """Plan name: "free", "pro", or "business"."""

    status: str
    """Stripe subscription status: "active", "trialing", "past_due", "canceled", etc."""

    current_period_end: Optional[datetime]
    """UTC datetime when the current billing period ends. None for free plan."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "plan": "pro",
                "status": "trialing",
                "current_period_end": "2026-04-12T00:00:00Z",
            }
        }
    }
