"""Reports API — compliance report generation endpoints."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.enforcement import require_plan
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.request import Request
from app.reports.generator import generate_report_data, render_csv, render_excel, render_pdf

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# Category → OWASP mapping (shared with monitor router)
CATEGORY_TO_OWASP = {
    "prompt_injection": "LLM01", "jailbreak": "LLM01", "system_prompt_leak": "LLM01",
    "output_manipulation": "LLM02", "xss_injection": "LLM02", "sql_injection": "LLM02",
    "code_injection": "LLM02", "command_injection": "LLM02",
    "pii_leak": "LLM06", "credential_leak": "LLM06", "pii_input": "LLM06",
    "confidential_data": "LLM06", "data_exfiltration": "LLM06",
}

OWASP_LLM_TOP10 = {
    "LLM01": "Prompt Injection", "LLM02": "Insecure Output Handling",
    "LLM03": "Training Data Poisoning", "LLM04": "Model Denial of Service",
    "LLM05": "Supply-Chain Vulnerabilities", "LLM06": "Sensitive Information Disclosure",
    "LLM07": "Insecure Plugin Design", "LLM08": "Excessive Agency",
    "LLM09": "Overreliance", "LLM10": "Model Theft",
}


@router.get("/generate", dependencies=[Depends(require_plan("business"))])
async def generate_report(
    format: str = Query("json", enum=["json", "csv", "pdf", "excel"]),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate a compliance report for the specified period.

    Formats:
      - json: Structured JSON data
      - csv: Tabular CSV file
      - pdf: Professional PDF document with tables
      - excel: Multi-sheet Excel workbook (OWASP, SOC2, GDPR, Japan)
    """
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=days)

    report_data = await generate_report_data(
        db=db,
        tenant_id=user.tenant_id,
        date_from=date_from,
        date_to=date_to,
    )

    if format == "csv":
        csv_content = render_csv(report_data)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=aigis_report_{days}d.csv"
            },
        )

    if format == "pdf":
        pdf_bytes = render_pdf(report_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=aigis_report_{days}d.pdf"
            },
        )

    if format == "excel":
        excel_bytes = render_excel(report_data)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=aigis_report_{days}d.xlsx"
            },
        )

    return JSONResponse(content=report_data)


@router.get("/weekly")
async def weekly_report(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate a weekly security report with week-over-week trends.

    This is the Default Mode report — available to all plans.
    Returns summary, risk distribution, category trends, OWASP coverage,
    and recommended actions.
    """
    now = datetime.now(timezone.utc)
    this_week_start = now - timedelta(days=7)
    prev_week_start = this_week_start - timedelta(days=7)

    # Load this week's requests
    result = await db.execute(
        select(Request).where(
            Request.tenant_id == user.tenant_id,
            Request.created_at >= this_week_start,
        )
    )
    this_requests = result.scalars().all()

    # Load previous week's requests
    result = await db.execute(
        select(Request).where(
            Request.tenant_id == user.tenant_id,
            Request.created_at >= prev_week_start,
            Request.created_at < this_week_start,
        )
    )
    prev_requests = result.scalars().all()

    # Aggregate this week
    this_total = len(this_requests)
    this_blocked = sum(1 for r in this_requests if r.status == "blocked")
    this_review = sum(1 for r in this_requests if r.status == "queued")
    this_allowed = sum(1 for r in this_requests if r.status == "allowed")
    this_safety = this_allowed / this_total if this_total > 0 else 1.0

    # Aggregate previous week
    prev_total = len(prev_requests)
    prev_blocked = sum(1 for r in prev_requests if r.status == "blocked")
    prev_safety = sum(1 for r in prev_requests if r.status == "allowed") / prev_total if prev_total > 0 else 1.0

    # Risk distribution (this week)
    risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for req in this_requests:
        score = req.input_risk_score or 0
        if score <= 30:
            risk_dist["low"] += 1
        elif score <= 60:
            risk_dist["medium"] += 1
        elif score <= 80:
            risk_dist["high"] += 1
        else:
            risk_dist["critical"] += 1

    # Category counts (this week + prev week)
    this_cats: dict[str, int] = defaultdict(int)
    prev_cats: dict[str, int] = defaultdict(int)
    this_layer_counts: dict[str, int] = defaultdict(int)

    for req in this_requests:
        for rule in (req.input_matched_rules or []):
            cat = rule.get("category", "") if isinstance(rule, dict) else ""
            rid = rule.get("rule_id", "") if isinstance(rule, dict) else ""
            if cat:
                this_cats[cat] += 1
            if rid.startswith("sim_"):
                this_layer_counts["similarity"] += 1
            elif rid:
                this_layer_counts["regex"] += 1

    for req in prev_requests:
        for rule in (req.input_matched_rules or []):
            cat = rule.get("category", "") if isinstance(rule, dict) else ""
            if cat:
                prev_cats[cat] += 1

    # Category trends
    all_cats = set(this_cats.keys()) | set(prev_cats.keys())
    category_trends = {}
    for cat in all_cats:
        this_count = this_cats.get(cat, 0)
        prev_count = prev_cats.get(cat, 0)
        change = _pct_change(prev_count, this_count)
        category_trends[cat] = {
            "this_week": this_count,
            "prev_week": prev_count,
            "change_pct": round(change, 1),
            "direction": "up" if change > 5 else "down" if change < -5 else "flat",
        }

    # OWASP coverage
    owasp_coverage = {}
    for oid, name in OWASP_LLM_TOP10.items():
        related = [c for c, o in CATEGORY_TO_OWASP.items() if o == oid]
        hits = sum(this_cats.get(c, 0) for c in related)
        blocked = sum(
            1 for req in this_requests
            if req.status == "blocked"
            and any(
                rule.get("category") in related
                for rule in (req.input_matched_rules or [])
                if isinstance(rule, dict)
            )
        )
        owasp_coverage[oid] = {
            "name": name,
            "detections": hits,
            "blocked": blocked,
            "covered": len(related) > 0,
            "protection_level": (
                "active" if blocked > 0
                else "monitored" if hits > 0
                else "pattern-ready" if related
                else "not-covered"
            ),
        }

    # Recommendations
    recommendations = _generate_recommendations(
        this_cats, category_trends, this_blocked, prev_blocked, this_safety, this_total,
    )

    return JSONResponse({
        "generated_at": now.isoformat(),
        "period_start": this_week_start.strftime("%Y-%m-%d"),
        "period_end": now.strftime("%Y-%m-%d"),
        "total_scans": this_total,
        "total_blocked": this_blocked,
        "total_review": this_review,
        "total_allowed": this_allowed,
        "safety_rate": round(this_safety, 4),
        "risk_distribution": risk_dist,
        "category_counts": dict(this_cats),
        "detection_by_layer": dict(this_layer_counts),
        "owasp_coverage": owasp_coverage,
        "prev_total_scans": prev_total,
        "prev_total_blocked": prev_blocked,
        "prev_safety_rate": round(prev_safety, 4),
        "trend_scans_pct": round(_pct_change(prev_total, this_total), 1),
        "trend_blocked_pct": round(_pct_change(prev_blocked, this_blocked), 1),
        "trend_safety_pct": round((this_safety - prev_safety) * 100, 2),
        "category_trends": category_trends,
        "recommendations": recommendations,
    })


def _pct_change(old: int, new: int) -> float:
    if old == 0:
        return 100.0 if new > 0 else 0.0
    return ((new - old) / old) * 100


def _generate_recommendations(
    this_cats: dict[str, int],
    category_trends: dict[str, dict],
    this_blocked: int,
    prev_blocked: int,
    safety_rate: float,
    total: int,
) -> list[dict[str, str]]:
    recs = []

    for cat, trend in category_trends.items():
        if trend["change_pct"] > 50 and trend["this_week"] >= 3:
            recs.append({
                "severity": "warning",
                "message": f"{cat} increased {trend['change_pct']:.0f}% this week "
                           f"({trend['prev_week']} -> {trend['this_week']}). "
                           f"Consider reviewing detection rules.",
            })

    for cat, trend in category_trends.items():
        if trend["prev_week"] == 0 and trend["this_week"] > 0:
            recs.append({
                "severity": "info",
                "message": f"New threat category: {cat} ({trend['this_week']} occurrences).",
            })

    blocked_change = _pct_change(prev_blocked, this_blocked)
    if blocked_change > 100:
        recs.append({
            "severity": "warning",
            "message": f"Blocked requests doubled ({blocked_change:.0f}% increase). "
                       f"Check for targeted attacks or false positives.",
        })

    if safety_rate < 0.9 and total > 5:
        recs.append({
            "severity": "critical",
            "message": f"Safety rate is {safety_rate:.1%}, below 90%. "
                       f"Review blocked requests for false positives.",
        })

    if total == 0:
        recs.append({
            "severity": "warning",
            "message": "No scans this week. Verify Aigis integration is active.",
        })

    return recs
