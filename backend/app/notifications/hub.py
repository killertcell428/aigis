"""Notification Hub — unified notification dispatch for Aigis.

Sends alerts via Slack, generic Webhook, and logs all notification attempts.
Extends the existing Slack notification with incident-aware messaging.

Usage:
    from app.notifications.hub import notify

    await notify(
        tenant=tenant,
        event="incident.created",
        title="SQL Injection detected",
        body="Score 100, auto-blocked. Incident INC-2026-0003 created.",
        severity="critical",
        incident_number="INC-2026-0003",
    )
"""

import logging
from typing import Any

import httpx

from app.models.tenant import Tenant
from app.notifications.url_guard import is_safe_url as _is_safe_url  # re-export

logger = logging.getLogger(__name__)


async def notify(
    tenant: Tenant,
    event: str,
    title: str,
    body: str,
    severity: str = "info",
    incident_number: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, bool]:
    """Dispatch notification to all configured channels.

    Returns dict of {channel: success_bool}.
    """
    results: dict[str, bool] = {}

    # Slack
    if tenant.slack_webhook_url:
        results["slack"] = await _send_slack(
            tenant, event, title, body, severity, incident_number, details,
        )

    # Generic Webhook (uses same URL pattern — future: separate field)
    webhook_url = (details or {}).get("webhook_url")
    if webhook_url:
        if _is_safe_url(webhook_url):
            results["webhook"] = await _send_webhook(
                webhook_url, event, title, body, severity, incident_number, details,
            )
        else:
            logger.warning("Webhook URL rejected (SSRF protection): %s", webhook_url[:50])

    if not results:
        logger.debug("No notification channels configured for tenant %s", tenant.slug)

    return results


async def notify_incident_created(
    tenant: Tenant,
    incident_number: str,
    severity: str,
    title: str,
    risk_score: int,
    matched_rules: list[dict],
) -> dict[str, bool]:
    """Notify about a new incident creation."""
    rules_summary = ", ".join(r.get("rule_name", "?") for r in matched_rules[:3])
    body = (
        f"Incident {incident_number} created.\n"
        f"Severity: {severity.upper()} | Score: {risk_score}\n"
        f"Rules: {rules_summary}"
    )
    return await notify(
        tenant=tenant,
        event="incident.created",
        title=f"[{severity.upper()}] {title}",
        body=body,
        severity=severity,
        incident_number=incident_number,
        details={"risk_score": risk_score, "matched_rules": matched_rules},
    )


async def notify_sla_warning(
    tenant: Tenant,
    incident_number: str,
    minutes_remaining: int,
) -> dict[str, bool]:
    """Notify that SLA deadline is approaching."""
    return await notify(
        tenant=tenant,
        event="incident.sla_warning",
        title=f"SLA Warning: {incident_number}",
        body=f"Incident {incident_number} has {minutes_remaining} minutes remaining before SLA deadline.",
        severity="warning",
        incident_number=incident_number,
    )


async def notify_incident_resolved(
    tenant: Tenant,
    incident_number: str,
    resolution: str,
    resolved_by: str,
) -> dict[str, bool]:
    """Notify that an incident has been resolved."""
    return await notify(
        tenant=tenant,
        event="incident.resolved",
        title=f"Resolved: {incident_number}",
        body=f"Incident {incident_number} resolved as '{resolution}' by {resolved_by}.",
        severity="info",
        incident_number=incident_number,
    )


# === Channel implementations ===

async def _send_slack(
    tenant: Tenant,
    event: str,
    title: str,
    body: str,
    severity: str,
    incident_number: str | None,
    details: dict[str, Any] | None,
) -> bool:
    """Send Slack Block Kit notification."""
    color = {"critical": "#dc2626", "high": "#f59e0b", "warning": "#f59e0b", "medium": "#3b82f6", "info": "#22c55e"}.get(severity, "#3b82f6")
    emoji = {"critical": "\U0001f6a8", "high": "\u26a0\ufe0f", "warning": "\u26a0\ufe0f"}.get(severity, "\u2139\ufe0f")

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {title}", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": body},
        },
    ]

    if incident_number:
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Incident:*\n`{incident_number}`"},
                {"type": "mrkdwn", "text": f"*Event:*\n`{event}`"},
            ],
        })

    # Matched rules
    matched_rules = (details or {}).get("matched_rules", [])
    if matched_rules:
        rules_text = "\n".join(
            f"- `{r.get('rule_name', '?')}` ({r.get('category', '?')}, +{r.get('score_delta', 0)})"
            for r in matched_rules[:5]
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Matched Rules:*\n{rules_text}"},
        })

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Tenant: *{tenant.name}* | Powered by Aigis"}],
    })

    payload = {"blocks": blocks, "attachments": [{"color": color, "blocks": []}]}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(tenant.slack_webhook_url, json=payload)
            success = resp.status_code == 200
            if not success:
                logger.warning("Slack webhook returned %d for %s", resp.status_code, tenant.slug)
            return success
    except Exception:
        logger.exception("Slack notification failed for %s", tenant.slug)
        return False


async def _send_webhook(
    url: str,
    event: str,
    title: str,
    body: str,
    severity: str,
    incident_number: str | None,
    details: dict[str, Any] | None,
) -> bool:
    """Send generic JSON webhook notification."""
    payload = {
        "event": event,
        "title": title,
        "body": body,
        "severity": severity,
        "incident_number": incident_number,
        "details": details or {},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return 200 <= resp.status_code < 300
    except Exception:
        logger.exception("Webhook notification failed: %s", url)
        return False
