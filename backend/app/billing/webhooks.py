"""Stripe Webhook handler for Aigis SaaS billing events."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.plans import PLAN_LIMITS, get_plan_limits
from app.billing.stripe_client import PRICE_IDS
from app.config import settings
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.webhook_event import WebhookEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


async def _find_tenant_by_customer_id(
    db: AsyncSession, customer_id: str
) -> Tenant | None:
    """Look up a tenant by Stripe customer ID."""
    result = await db.execute(
        select(Tenant).where(Tenant.stripe_customer_id == customer_id)
    )
    return result.scalar_one_or_none()


async def _find_tenant_by_metadata_or_email(
    db: AsyncSession, data: dict
) -> Tenant | None:
    """Look up a tenant by checkout session metadata (tenant_id) or customer email."""
    # Try metadata first
    tenant_id = data.get("metadata", {}).get("tenant_id")
    if tenant_id:
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant:
            return tenant

    # Fallback: find tenant via user email
    customer_email = data.get("customer_email") or data.get(
        "customer_details", {}
    ).get("email")
    if customer_email:
        from app.models.user import User

        result = await db.execute(select(User).where(User.email == customer_email))
        user = result.scalar_one_or_none()
        if user:
            result2 = await db.execute(
                select(Tenant).where(Tenant.id == user.tenant_id)
            )
            return result2.scalar_one_or_none()

    return None


def _resolve_plan_from_price_id(price_id: str | None) -> str:
    """Resolve plan name from a Stripe price ID."""
    if not price_id:
        return "free"
    for name, pid in PRICE_IDS.items():
        if pid and pid == price_id:
            return name.replace("_monthly", "")
    return "free"


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    stripe_signature: str = Header(alias="stripe-signature"),
) -> dict:
    """Handle incoming Stripe Webhook events."""
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.stripe_webhook_secret,
        )
    except stripe.error.SignatureVerificationError as exc:
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid Stripe signature") from exc
    except Exception as exc:
        logger.error("Failed to parse Stripe webhook payload: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid payload") from exc

    event_type = event["type"]
    data = event["data"]["object"]
    event_id = event["id"]

    logger.info("Received Stripe webhook event: %s (id=%s)", event_type, event_id)

    # Idempotency gate — reject duplicate Stripe event IDs.
    # Stripe retries failed deliveries, so the same event may arrive multiple
    # times. A unique-insert acts as the gate; IntegrityError => already processed.
    db.add(
        WebhookEvent(
            id=uuid.uuid4(),
            source="stripe",
            event_id=event_id,
            event_type=event_type,
        )
    )
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        logger.info("Stripe webhook duplicate ignored: %s (id=%s)", event_type, event_id)
        return {"status": "ok", "duplicate": True}

    # ------------------------------------------------------------------
    # checkout.session.completed
    # ------------------------------------------------------------------
    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")

        tenant = await _find_tenant_by_metadata_or_email(db, data)
        if not tenant:
            logger.error("checkout.session.completed: tenant not found for event %s", event["id"])
            return {"status": "ok"}

        # Resolve plan from subscription
        plan_name = "pro"
        if subscription_id:
            try:
                sub = stripe.Subscription.retrieve(subscription_id)
                price_id = sub["items"]["data"][0]["price"]["id"] if sub["items"]["data"] else None
                plan_name = _resolve_plan_from_price_id(price_id)
                trial_end = sub.get("trial_end")
                if trial_end:
                    tenant.trial_ends_at = datetime.fromtimestamp(trial_end, tz=timezone.utc)
            except Exception:
                logger.exception("Failed to retrieve subscription details")

        tenant.stripe_customer_id = customer_id
        tenant.stripe_subscription_id = subscription_id
        tenant.plan = plan_name
        tenant.subscription_status = "active"

        logger.info("Tenant %s activated on plan=%s", tenant.slug, plan_name)

    # ------------------------------------------------------------------
    # customer.subscription.updated
    # ------------------------------------------------------------------
    elif event_type == "customer.subscription.updated":
        customer_id = data.get("customer")
        status = data.get("status")
        price_id = (
            data.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
        )

        tenant = await _find_tenant_by_customer_id(db, customer_id)
        if not tenant:
            logger.warning("subscription.updated: tenant not found for customer=%s", customer_id)
            return {"status": "ok"}

        plan_name = _resolve_plan_from_price_id(price_id)
        tenant.plan = plan_name
        tenant.subscription_status = status or "active"

        if status == "past_due":
            logger.warning("Tenant %s subscription is past_due", tenant.slug)

        logger.info("Tenant %s updated: plan=%s status=%s", tenant.slug, plan_name, status)

    # ------------------------------------------------------------------
    # customer.subscription.deleted
    # ------------------------------------------------------------------
    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")

        tenant = await _find_tenant_by_customer_id(db, customer_id)
        if not tenant:
            logger.warning("subscription.deleted: tenant not found for customer=%s", customer_id)
            return {"status": "ok"}

        tenant.plan = "free"
        tenant.subscription_status = "canceled"
        tenant.stripe_subscription_id = None

        logger.info("Tenant %s downgraded to free (subscription canceled)", tenant.slug)

    # ------------------------------------------------------------------
    # invoice.payment_succeeded
    # ------------------------------------------------------------------
    elif event_type == "invoice.payment_succeeded":
        customer_id = data.get("customer")
        period_end = data.get("lines", {}).get("data", [{}])[0].get("period", {}).get("end")

        tenant = await _find_tenant_by_customer_id(db, customer_id)
        if not tenant:
            return {"status": "ok"}

        if period_end:
            tenant.subscription_current_period_end = datetime.fromtimestamp(
                period_end, tz=timezone.utc
            )
        # Clear past_due if it was set
        if tenant.subscription_status == "past_due":
            tenant.subscription_status = "active"

        logger.info("Payment succeeded for tenant %s", tenant.slug)

    # ------------------------------------------------------------------
    # invoice.payment_failed
    # ------------------------------------------------------------------
    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        attempt_count = data.get("attempt_count", 1)

        tenant = await _find_tenant_by_customer_id(db, customer_id)
        if not tenant:
            return {"status": "ok"}

        if attempt_count >= 3:
            tenant.plan = "free"
            tenant.subscription_status = "canceled"
            logger.warning(
                "Tenant %s downgraded to free after %d failed payment attempts",
                tenant.slug, attempt_count,
            )
        else:
            tenant.subscription_status = "past_due"
            logger.warning(
                "Payment failed for tenant %s (attempt %d)",
                tenant.slug, attempt_count,
            )

    # ------------------------------------------------------------------
    # customer.subscription.trial_will_end
    # ------------------------------------------------------------------
    elif event_type == "customer.subscription.trial_will_end":
        customer_id = data.get("customer")
        trial_end = data.get("trial_end")

        tenant = await _find_tenant_by_customer_id(db, customer_id)
        if not tenant:
            return {"status": "ok"}

        if trial_end:
            tenant.trial_ends_at = datetime.fromtimestamp(trial_end, tz=timezone.utc)

        logger.info("Trial ending soon for tenant %s", tenant.slug)

    else:
        logger.debug("Unhandled Stripe event type: %s", event_type)

    return {"status": "ok"}
