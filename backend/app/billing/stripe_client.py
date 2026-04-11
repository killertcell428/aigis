"""Stripe billing integration for Aigis SaaS."""
import stripe
from typing import Optional

from app.config import settings

stripe.api_key = settings.stripe_secret_key

PRICE_IDS = {
    "pro_monthly": settings.stripe_price_pro_monthly,
    "business_monthly": settings.stripe_price_business_monthly,
}


def create_checkout_session(
    customer_email: str,
    plan: str,
    tenant_id: str,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    """Create a Stripe Checkout session for a subscription.

    Args:
        customer_email: Email address of the customer.
        plan: Plan name, must be a key in PRICE_IDS ("pro" or "business").
        tenant_id: Aigis tenant ID to link back in webhooks.
        success_url: URL to redirect to after successful payment.
        cancel_url: URL to redirect to if the user cancels.

    Returns:
        A Stripe Checkout Session object. Use `.url` to redirect the user.

    Raises:
        stripe.error.StripeError: If the Stripe API call fails.
        ValueError: If the plan is not recognized.
    """
    price_key = f"{plan}_monthly"
    if price_key not in PRICE_IDS or not PRICE_IDS[price_key]:
        raise ValueError(f"Unknown or unconfigured plan: {plan!r}")

    session = stripe.checkout.Session.create(
        customer_email=customer_email,
        mode="subscription",
        line_items=[
            {
                "price": PRICE_IDS[price_key],
                "quantity": 1,
            }
        ],
        subscription_data={
            "trial_period_days": 14,
            "metadata": {"tenant_id": tenant_id},
        },
        metadata={"tenant_id": tenant_id},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session


def create_customer_portal_session(
    customer_id: str,
    return_url: str,
) -> stripe.billing_portal.Session:
    """Create a Stripe Customer Portal session.

    Allows the customer to manage their subscription, payment method, and
    billing history without contacting support.

    Args:
        customer_id: Stripe customer ID (e.g. "cus_xxxxxxxxxxxxxxxxxx").
        return_url: URL to redirect to after the user finishes in the portal.

    Returns:
        A Stripe Billing Portal Session object. Use `.url` to redirect the user.

    Raises:
        stripe.error.StripeError: If the Stripe API call fails.
    """
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session


def get_subscription_status(customer_id: str) -> Optional[dict]:
    """Retrieve the active subscription status for a customer.

    Args:
        customer_id: Stripe customer ID (e.g. "cus_xxxxxxxxxxxxxxxxxx").

    Returns:
        A dict with keys: subscription_id, status, plan, current_period_end.
        Returns None if no active subscription is found.

    Raises:
        stripe.error.StripeError: If the Stripe API call fails.
    """
    subscriptions = stripe.Subscription.list(
        customer=customer_id,
        status="all",
        limit=1,
    )

    if not subscriptions.data:
        return None

    sub = subscriptions.data[0]

    # Resolve the plan name from the price ID
    price_id = sub["items"]["data"][0]["price"]["id"] if sub["items"]["data"] else None
    plan_name = "free"
    for name, pid in PRICE_IDS.items():
        if pid and pid == price_id:
            plan_name = name.replace("_monthly", "")
            break

    return {
        "subscription_id": sub["id"],
        "status": sub["status"],
        "plan": plan_name,
        "current_period_end": sub["current_period_end"],
    }


def cancel_subscription(subscription_id: str) -> stripe.Subscription:
    """Cancel a subscription immediately.

    Cancels at the end of the current billing period to avoid partial-month
    refunds. The subscription status will change to "canceled" after the
    current period ends.

    Args:
        subscription_id: Stripe subscription ID (e.g. "sub_xxxxxxxxxxxxxxxxxx").

    Returns:
        The updated Stripe Subscription object.

    Raises:
        stripe.error.StripeError: If the Stripe API call fails.
    """
    subscription = stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=True,
    )
    return subscription
