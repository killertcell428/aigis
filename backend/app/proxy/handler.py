"""Proxy handler: core logic for filtering and forwarding LLM requests."""
import asyncio
import time
import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.logger import log_event
from app.config import settings
from app.notifications.hub import notify_incident_created
from app.filters.input_filter import filter_input
from app.filters.output_filter import filter_output
from app.incidents.service import create_incident
from app.models.policy import Policy
from app.models.request import Request
from app.models.tenant import Tenant
from app.notifications.slack import send_slack_notification
from app.policies.manager import create_default_policy, get_active_policy
from app.review.service import enqueue_for_review


# ---------------------------------------------------------------------------
# Blocked response (OpenAI-compatible error format)
# ---------------------------------------------------------------------------
def blocked_response(
    reason: str,
    risk_score: int,
    remediation: dict | None = None,
    matched_rules: list | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": {
            "message": f"Request blocked by Aigis security policy. {reason}",
            "type": "guardian_policy_violation",
            "code": "request_blocked",
            "risk_score": risk_score,
        }
    }
    if remediation:
        body["remediation"] = remediation
    if matched_rules:
        body["matched_rules"] = [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category,
                "score_delta": r.score_delta,
                "owasp_ref": r.owasp_ref,
                "remediation_hint": r.remediation_hint,
            }
            for r in matched_rules
        ]
    return body


def queued_response(review_item_id: str, sla_minutes: int) -> dict[str, Any]:
    return {
        "error": {
            "message": (
                "Request queued for human review. "
                f"You will receive a response within {sla_minutes} minutes."
            ),
            "type": "guardian_review_required",
            "code": "queued_for_review",
            "review_item_id": review_item_id,
        }
    }


# ---------------------------------------------------------------------------
# Main proxy handler
# ---------------------------------------------------------------------------
async def handle_proxy_request(
    db: AsyncSession,
    tenant: Tenant,
    request_body: dict[str, Any],
    client_ip: str | None,
    upstream_api_key: str,
) -> tuple[dict[str, Any], int]:
    """Process a proxied LLM chat completion request.

    Flow:
      1. Load policy
      2. Run input filter
      3. Route: allow / block / queue
      4. If allowed: forward to upstream LLM
      5. Run output filter on response
      6. Store request record + audit log
      7. Return final response

    Returns:
        Tuple of (response_body, http_status_code).
    """
    start_time = time.monotonic()

    # 1. Load policy
    policy = await get_active_policy(db, tenant.id)
    if policy is None:
        policy = await create_default_policy(db, tenant.id)

    messages: list[dict] = request_body.get("messages", [])
    model: str = request_body.get("model", "gpt-4o")

    # 2. Input filter
    input_result = filter_input(messages, policy.custom_rules)

    # 3. Route based on risk score
    req = Request(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        model=model,
        messages=messages,
        request_headers={},
        client_ip=client_ip,
        input_risk_score=input_result.risk_score,
        input_risk_level=input_result.risk_level,
        input_matched_rules=[
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category,
                "score_delta": r.score_delta,
                "matched_text": r.matched_text,
                "owasp_ref": r.owasp_ref,
                "remediation_hint": r.remediation_hint,
            }
            for r in input_result.matched_rules
        ],
        status="pending",
    )
    db.add(req)
    await db.flush()  # get req.id

    # --- Auto-block (Critical) ---
    if input_result.risk_score >= policy.auto_block_threshold:
        req.status = "blocked"
        req.latency_ms = (time.monotonic() - start_time) * 1000
        db.add(req)
        await log_event(
            db=db,
            tenant_id=tenant.id,
            event_type="request.blocked",
            summary=f"Request auto-blocked (score={input_result.risk_score})",
            request_id=req.id,
            severity="critical",
            details={
                "risk_score": input_result.risk_score,
                "risk_level": input_result.risk_level,
                "reason": input_result.reason,
            },
        )
        # Fire-and-forget Slack notification
        asyncio.create_task(
            send_slack_notification(
                tenant=tenant,
                event_type="request.blocked",
                summary=f"Request auto-blocked (score={input_result.risk_score}): {input_result.reason}",
                details={
                    "risk_score": input_result.risk_score,
                    "risk_level": input_result.risk_level,
                    "matched_rules": req.input_matched_rules,
                },
            )
        )
        # Create incident for critical threats
        primary_cat = req.input_matched_rules[0].get("category", "") if req.input_matched_rules else ""
        inc_title = f"{input_result.reason or 'Critical threat'} (score={input_result.risk_score})"
        inc = await create_incident(
            db=db,
            tenant_id=tenant.id,
            request_id=req.id,
            severity="critical",
            title=inc_title,
            risk_score=input_result.risk_score,
            matched_rules=req.input_matched_rules,
            source_ip=client_ip,
            trigger_category=primary_cat,
            request_snapshot={"model": model, "messages": messages},
            sla_minutes=policy.review_sla_minutes,
        )
        asyncio.create_task(notify_incident_created(
            tenant=tenant, incident_number=inc.incident_number, severity="critical",
            title=inc_title, risk_score=input_result.risk_score, matched_rules=req.input_matched_rules,
        ))
        return blocked_response(
            input_result.reason,
            input_result.risk_score,
            remediation=input_result.remediation,
            matched_rules=input_result.matched_rules,
        ), 403

    # --- Queue for review (Medium / High) ---
    if input_result.risk_score > policy.auto_allow_threshold:
        review_item = await enqueue_for_review(db, req, policy.review_sla_minutes)
        req.latency_ms = (time.monotonic() - start_time) * 1000
        db.add(req)
        # Create incident for high-risk threats entering review
        primary_cat = req.input_matched_rules[0].get("category", "") if req.input_matched_rules else ""
        sev = "high" if input_result.risk_score > 60 else "medium"
        inc_title = f"{input_result.reason or 'Threat detected'} (score={input_result.risk_score})"
        inc = await create_incident(
            db=db,
            tenant_id=tenant.id,
            request_id=req.id,
            severity=sev,
            title=inc_title,
            risk_score=input_result.risk_score,
            matched_rules=req.input_matched_rules,
            source_ip=client_ip,
            trigger_category=primary_cat,
            request_snapshot={"model": model, "messages": messages},
            sla_minutes=policy.review_sla_minutes,
        )
        asyncio.create_task(notify_incident_created(
            tenant=tenant, incident_number=inc.incident_number, severity=sev,
            title=inc_title, risk_score=input_result.risk_score, matched_rules=req.input_matched_rules,
        ))
        return queued_response(str(review_item.id), policy.review_sla_minutes), 202

    # --- Auto-allow (Low) ---
    # 4. Forward to upstream LLM
    upstream_response_body, upstream_status = await _forward_to_upstream(
        request_body=request_body,
        api_key=upstream_api_key,
    )

    # 5. Output filter
    if upstream_status == 200:
        output_result = filter_output(upstream_response_body, policy.custom_rules)
        req.output_risk_score = output_result.risk_score
        req.output_risk_level = output_result.risk_level
        req.output_matched_rules = [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category,
                "score_delta": r.score_delta,
                "matched_text": r.matched_text,
                "owasp_ref": r.owasp_ref,
                "remediation_hint": r.remediation_hint,
            }
            for r in output_result.matched_rules
        ]
        req.response_body = upstream_response_body
        req.response_status_code = upstream_status

        # Block on critical output (e.g., API key leak)
        if output_result.risk_score >= policy.auto_block_threshold:
            req.status = "blocked"
            req.latency_ms = (time.monotonic() - start_time) * 1000
            db.add(req)
            await log_event(
                db=db,
                tenant_id=tenant.id,
                event_type="response.blocked",
                summary=f"Response blocked by output filter (score={output_result.risk_score})",
                request_id=req.id,
                severity="critical",
                details={
                    "risk_score": output_result.risk_score,
                    "reason": output_result.reason,
                },
            )
            asyncio.create_task(
                send_slack_notification(
                    tenant=tenant,
                    event_type="response.blocked",
                    summary=f"Response blocked by output filter (score={output_result.risk_score})",
                    details={
                        "risk_score": output_result.risk_score,
                        "risk_level": output_result.risk_level,
                        "matched_rules": req.output_matched_rules,
                    },
                )
            )
            # Create incident for output filter blocks
            out_cat = req.output_matched_rules[0].get("category", "") if req.output_matched_rules else ""
            out_title = f"Output blocked: {output_result.reason or 'Data leak detected'} (score={output_result.risk_score})"
            inc = await create_incident(
                db=db,
                tenant_id=tenant.id,
                request_id=req.id,
                severity="critical",
                title=out_title,
                risk_score=output_result.risk_score,
                matched_rules=req.output_matched_rules,
                source_ip=client_ip,
                trigger_category=out_cat,
                request_snapshot={"model": model, "messages": messages},
                sla_minutes=policy.review_sla_minutes,
            )
            asyncio.create_task(notify_incident_created(
                tenant=tenant, incident_number=inc.incident_number, severity="critical",
                title=out_title, risk_score=output_result.risk_score, matched_rules=req.output_matched_rules,
            ))
            return blocked_response(
                output_result.reason,
                output_result.risk_score,
                remediation=output_result.remediation,
                matched_rules=output_result.matched_rules,
            ), 403

        req.status = "allowed"
    else:
        req.status = "allowed"
        req.response_body = upstream_response_body
        req.response_status_code = upstream_status

    req.latency_ms = (time.monotonic() - start_time) * 1000
    db.add(req)

    await log_event(
        db=db,
        tenant_id=tenant.id,
        event_type="request.allowed",
        summary=f"Request allowed (score={input_result.risk_score})",
        request_id=req.id,
        severity="info",
        details={"risk_score": input_result.risk_score, "latency_ms": req.latency_ms},
    )

    return upstream_response_body, upstream_status


async def _forward_to_upstream(
    request_body: dict[str, Any],
    api_key: str,
) -> tuple[dict[str, Any], int]:
    """Forward the request to the upstream LLM API.

    In demo mode, returns a mock response without calling the real API.

    Returns:
        Tuple of (response_json, status_code).
    """
    if settings.demo_mode:
        return _generate_mock_response(request_body), 200

    url = f"{settings.openai_api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=request_body, headers=headers)
        try:
            body = resp.json()
        except Exception:
            body = {"error": {"message": "Invalid JSON from upstream", "type": "upstream_error"}}
        return body, resp.status_code


def _generate_mock_response(request_body: dict[str, Any]) -> dict[str, Any]:
    """Generate a realistic mock LLM response for demo mode."""
    messages = request_body.get("messages", [])
    model = request_body.get("model", "gpt-4o")
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    content = _mock_answer(user_message)
    prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
    completion_tokens = len(content.split())

    return {
        "id": f"chatcmpl-demo-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def _mock_answer(user_message: str) -> str:
    """Return a contextually appropriate mock answer."""
    lower = user_message.lower().strip()

    patterns = [
        (["capital of france", "capitale de la france"], "The capital of France is Paris."),
        (["capital of japan"], "The capital of Japan is Tokyo."),
        (["hello", "hi there", "hey"], "Hello! How can I help you today?"),
        (["summarize", "summary"], "Here's a brief summary: The document discusses key points related to your query, highlighting the main findings and recommendations for next steps."),
        (["translate"], "Here is the translation of your text. Please note that machine translations may not capture all nuances of the original language."),
        (["code", "function", "implement", "write a"], "Here's an implementation approach:\n\n```python\ndef process_data(items):\n    results = []\n    for item in items:\n        results.append(transform(item))\n    return results\n```\n\nThis follows best practices for readability and maintainability."),
        (["explain", "what is", "how does"], "Great question! This concept works by processing information through multiple stages, each adding a layer of analysis and refinement to produce accurate results."),
        (["list", "give me"], "Here are the key items:\n\n1. First item - the primary consideration\n2. Second item - supporting element\n3. Third item - additional context\n4. Fourth item - final recommendation"),
    ]

    for keywords, answer in patterns:
        if any(kw in lower for kw in keywords):
            return answer

    return (
        "Based on your request, I've analyzed the available information. "
        "The key findings suggest a balanced approach that considers multiple factors. "
        "I'd recommend reviewing the specific details in context and adjusting as needed "
        "for your particular use case."
    )
