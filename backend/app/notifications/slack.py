"""Slack notification service for Aigis.

Sends Webhook messages to Slack when high-risk events are detected.
"""
import logging
from typing import Any

import httpx

from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


async def send_slack_notification(
    tenant: Tenant,
    event_type: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> bool:
    """Send a Slack notification for a security event.

    Returns True if sent successfully, False otherwise.
    """
    if not tenant.slack_webhook_url:
        return False

    # Decide whether to notify based on tenant preferences
    if event_type in ("request.blocked", "response.blocked") and not tenant.notify_on_block:
        return False
    if event_type == "request.queued" and not tenant.notify_on_high_risk:
        return False

    risk_score = details.get("risk_score", 0) if details else 0
    risk_level = details.get("risk_level", "unknown") if details else "unknown"

    # Build Slack Block Kit message
    color = _severity_color(event_type, risk_score)
    emoji = _severity_emoji(event_type)

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Aigis Alert",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Event:*\n`{event_type}`"},
                {"type": "mrkdwn", "text": f"*Risk Score:*\n{risk_score} ({risk_level})"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Summary:*\n{summary}"},
        },
    ]

    # Add matched rules if available
    matched_rules = details.get("matched_rules", []) if details else []
    if matched_rules and isinstance(matched_rules, list):
        rules_text = "\n".join(
            f"- `{r.get('rule_name', 'Unknown')}` (+{r.get('score_delta', 0)})"
            for r in matched_rules[:5]
        )
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Matched Rules:*\n{rules_text}"},
            }
        )

    blocks.append(
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Tenant: *{tenant.name}* | Powered by Aigis"},
            ],
        }
    )

    payload = {
        "blocks": blocks,
        "attachments": [{"color": color, "blocks": []}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(tenant.slack_webhook_url, json=payload)
            if resp.status_code == 200:
                logger.info("Slack notification sent for tenant %s: %s", tenant.slug, event_type)
                return True
            else:
                logger.warning(
                    "Slack webhook returned %d for tenant %s",
                    resp.status_code, tenant.slug,
                )
                return False
    except Exception:
        logger.exception("Failed to send Slack notification for tenant %s", tenant.slug)
        return False


def _severity_color(event_type: str, risk_score: int) -> str:
    """Return Slack attachment color based on event severity."""
    if "blocked" in event_type:
        return "#dc2626"  # red
    if risk_score >= 80:
        return "#dc2626"  # red
    if risk_score >= 60:
        return "#f59e0b"  # amber
    return "#3b82f6"  # blue


def _severity_emoji(event_type: str) -> str:
    if "blocked" in event_type:
        return "\U0001f6a8"  # 🚨
    return "\u26a0\ufe0f"  # ⚠️
