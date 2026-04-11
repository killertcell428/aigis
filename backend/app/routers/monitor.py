"""Monitor API — security monitoring dashboard endpoints.

Provides real-time security metrics, ASR (Attack Success Rate) trends,
OWASP LLM Top 10 scorecard, detection pipeline stats, and heatmap data.

Inspired by 0din-ai/ai-scanner's ASR tracking (Apache 2.0).
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.audit import AuditLog
from app.models.request import Request

router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])

# OWASP LLM Top 10 mapping
OWASP_LLM_TOP10 = {
    "LLM01": "Prompt Injection",
    "LLM02": "Insecure Output Handling",
    "LLM03": "Training Data Poisoning",
    "LLM04": "Model Denial of Service",
    "LLM05": "Supply-Chain Vulnerabilities",
    "LLM06": "Sensitive Information Disclosure",
    "LLM07": "Insecure Plugin Design",
    "LLM08": "Excessive Agency",
    "LLM09": "Overreliance",
    "LLM10": "Model Theft",
}

CATEGORY_TO_OWASP = {
    "prompt_injection": "LLM01",
    "jailbreak": "LLM01",
    "system_prompt_leak": "LLM01",
    "output_manipulation": "LLM02",
    "xss_injection": "LLM02",
    "sql_injection": "LLM02",
    "code_injection": "LLM02",
    "training_data": "LLM03",
    "resource_abuse": "LLM04",
    "dos_attack": "LLM04",
    "supply_chain": "LLM05",
    "mcp_poisoning": "LLM05",
    "mcp_tool_shadow": "LLM05",
    "pii_leak": "LLM06",
    "credential_leak": "LLM06",
    "data_exfiltration": "LLM06",
    "confidential_data": "LLM06",
    "pii_input": "LLM06",
    "insecure_plugin": "LLM07",
    "excessive_agency": "LLM08",
    "privilege_escalation": "LLM08",
    "overreliance": "LLM09",
    "model_theft": "LLM10",
}

# ai-guardian unique features per OWASP category
UNIQUE_FEATURES = {
    "LLM01": [
        "4-layer detection (regex + similarity + decoded + multi-turn)",
        "Adversarial loop with auto-fix",
        "Real-time inline blocking (not post-hoc)",
    ],
    "LLM02": [
        "Output scanning with PII/credential detection",
        "Auto-sanitize (redaction) before response",
    ],
    "LLM05": [
        "MCP tool poisoning detection",
        "Rug-pull detection via snapshot diffing",
        "Server trust scoring",
    ],
    "LLM06": [
        "Japanese PII detection (My Number, phone, address)",
        "Auto-redaction with sanitize()",
        "Confidential data pattern matching",
    ],
    "LLM07": [
        "MCP inputSchema parameter injection detection",
        "Cross-tool shadowing detection",
    ],
    "LLM08": [
        "Capability-based access control (CaMeL-inspired)",
        "Policy-as-code governance",
        "Autonomy level tracking",
    ],
}


@router.get("/snapshot")
async def get_snapshot(
    hours: float = Query(24, ge=1, le=8760),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a point-in-time security metrics snapshot."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Query requests
    result = await db.execute(
        select(Request).where(
            Request.tenant_id == user.tenant_id,
            Request.created_at >= cutoff,
        )
    )
    requests = result.scalars().all()

    total = len(requests)
    blocked = sum(1 for r in requests if r.status == "blocked")
    review = sum(1 for r in requests if r.status == "queued")
    allowed = sum(1 for r in requests if r.status == "allowed")

    # Risk distribution
    risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    category_counts: dict[str, int] = {}
    category_blocked: dict[str, int] = {}
    layer_counts: dict[str, int] = {}

    for req in requests:
        score = req.input_risk_score or 0
        if score <= 30:
            risk_dist["low"] += 1
        elif score <= 60:
            risk_dist["medium"] += 1
        elif score <= 80:
            risk_dist["high"] += 1
        else:
            risk_dist["critical"] += 1

        # Parse matched rules for categories and layers
        rules = req.input_matched_rules or []
        for rule in rules:
            cat = rule.get("category", "") if isinstance(rule, dict) else ""
            rid = rule.get("rule_id", "") if isinstance(rule, dict) else ""
            rname = rule.get("rule_name", "") if isinstance(rule, dict) else ""

            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
                if req.status == "blocked":
                    category_blocked[cat] = category_blocked.get(cat, 0) + 1

            # Infer detection layer
            if rid.startswith("sim_"):
                layer_counts["similarity"] = layer_counts.get("similarity", 0) + 1
            elif "(decoded)" in rname:
                layer_counts["decoded"] = layer_counts.get("decoded", 0) + 1
            elif rid == "multi_turn_escalation":
                layer_counts["multi_turn"] = layer_counts.get("multi_turn", 0) + 1
            elif rid:
                layer_counts["regex"] = layer_counts.get("regex", 0) + 1

    # Detection rate and ASR
    detected = blocked + review
    slipped = sum(
        1 for r in requests
        if r.status == "allowed" and (r.input_risk_score or 0) > 30
    )
    detection_rate = detected / (detected + slipped) if (detected + slipped) > 0 else 1.0

    threats_with_rules = [r for r in requests if r.input_matched_rules]
    detected_attacks = sum(
        1 for r in threats_with_rules if (r.input_risk_score or 0) > 30
    )
    asr = (
        (len(threats_with_rules) - detected_attacks) / len(threats_with_rules)
        if threats_with_rules else 0.0
    )

    return JSONResponse({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "period_hours": hours,
        "total_scans": total,
        "total_blocked": blocked,
        "total_review": review,
        "total_allowed": allowed,
        "detection_rate": round(detection_rate, 4),
        "asr": round(asr, 4),
        "risk_distribution": risk_dist,
        "category_counts": category_counts,
        "category_blocked": category_blocked,
        "detection_by_layer": layer_counts,
    })


@router.get("/asr-trend")
async def get_asr_trend(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get daily ASR (Attack Success Rate) trend."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Request).where(
            Request.tenant_id == user.tenant_id,
            Request.created_at >= cutoff,
        )
    )
    requests = result.scalars().all()

    # Group by day
    daily: dict[str, dict[str, int]] = {}
    for req in requests:
        if not req.input_matched_rules:
            continue
        day = req.created_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"total": 0, "detected": 0}
        daily[day]["total"] += 1
        if (req.input_risk_score or 0) > 30:
            daily[day]["detected"] += 1

    trend = []
    for day in sorted(daily.keys()):
        d = daily[day]
        bypassed = d["total"] - d["detected"]
        trend.append({
            "date": day,
            "total_attacks": d["total"],
            "blocked": d["detected"],
            "bypassed": bypassed,
            "asr": round(bypassed / d["total"], 4) if d["total"] > 0 else 0,
        })

    return JSONResponse(trend)


@router.get("/owasp-scorecard")
async def get_owasp_scorecard(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get OWASP LLM Top 10 coverage scorecard."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Request).where(
            Request.tenant_id == user.tenant_id,
            Request.created_at >= cutoff,
        )
    )
    requests = result.scalars().all()

    # Aggregate category data
    cat_counts: dict[str, int] = {}
    cat_blocked: dict[str, int] = {}
    for req in requests:
        for rule in (req.input_matched_rules or []):
            cat = rule.get("category", "") if isinstance(rule, dict) else ""
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
                if req.status == "blocked":
                    cat_blocked[cat] = cat_blocked.get(cat, 0) + 1

    scorecard = {}
    for owasp_id, owasp_name in OWASP_LLM_TOP10.items():
        related_cats = [c for c, o in CATEGORY_TO_OWASP.items() if o == owasp_id]
        detections = sum(cat_counts.get(c, 0) for c in related_cats)
        blocked = sum(cat_blocked.get(c, 0) for c in related_cats)

        protection_level = (
            "active" if blocked > 0
            else "monitored" if detections > 0
            else "pattern-ready" if related_cats
            else "not-covered"
        )

        scorecard[owasp_id] = {
            "name": owasp_name,
            "detections": detections,
            "blocked": blocked,
            "categories": related_cats,
            "covered": len(related_cats) > 0,
            "protection_level": protection_level,
            "unique_features": UNIQUE_FEATURES.get(owasp_id, []),
        }

    return JSONResponse(scorecard)


@router.get("/heatmap")
async def get_category_heatmap(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get category-by-day detection heatmap."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Request).where(
            Request.tenant_id == user.tenant_id,
            Request.created_at >= cutoff,
        )
    )
    requests = result.scalars().all()

    heatmap: dict[str, dict[str, int]] = {}
    for req in requests:
        day = req.created_at.strftime("%Y-%m-%d")
        for rule in (req.input_matched_rules or []):
            cat = rule.get("category", "") if isinstance(rule, dict) else ""
            if cat:
                if cat not in heatmap:
                    heatmap[cat] = {}
                heatmap[cat][day] = heatmap[cat].get(day, 0) + 1

    return JSONResponse(heatmap)


@router.get("/pipeline")
async def get_detection_pipeline(
    user=Depends(get_current_user),
):
    """Get detection pipeline layer descriptions."""
    return JSONResponse({
        "layers": {
            "regex": {
                "name": "Pattern Matching",
                "description": "165+ rules across 25 categories",
                "order": 1,
            },
            "similarity": {
                "name": "Semantic Similarity",
                "description": "Matches against known attack corpus",
                "order": 2,
            },
            "decoded": {
                "name": "Encoded Payload",
                "description": "Base64, hex, URL, ROT13 decoding",
                "order": 3,
            },
            "multi_turn": {
                "name": "Multi-turn Analysis",
                "description": "Conversation escalation detection",
                "order": 4,
            },
        },
        "unique_capabilities": [
            {
                "name": "Real-time Inline Blocking",
                "status": "Active",
                "differentiator": "Blocks threats BEFORE they reach the LLM, not after",
                "scan_only": "Post-hoc scanning only",
            },
            {
                "name": "Multi-Layer Detection",
                "status": "4 layers",
                "differentiator": "4 independent detection layers catch what single-layer misses",
                "scan_only": "Single probe layer",
            },
            {
                "name": "Auto-Fix (Adversarial Loop)",
                "status": "Active",
                "differentiator": "Learns from attacks and auto-generates new defense rules",
                "scan_only": "Manual rule updates only",
            },
            {
                "name": "MCP Tool Security",
                "status": "Active",
                "differentiator": "Detects tool poisoning, shadowing, rug-pulls in MCP ecosystem",
                "scan_only": "Not supported",
            },
            {
                "name": "Capability-Based Access Control",
                "status": "Active",
                "differentiator": "CaMeL-inspired least-privilege for AI agents",
                "scan_only": "Not supported",
            },
            {
                "name": "Zero-Dependency Core",
                "status": "Active",
                "differentiator": "pip install, no Docker/infra required",
                "scan_only": "Requires Docker + PostgreSQL + Rails",
            },
            {
                "name": "Japanese PII Detection",
                "status": "Active",
                "differentiator": "My Number, JP phone/address, bank account patterns",
                "scan_only": "English-centric patterns only",
            },
            {
                "name": "Output Sanitization",
                "status": "Active",
                "differentiator": "Auto-redact PII/secrets from LLM responses",
                "scan_only": "No output filtering",
            },
        ],
    })
