"""Weekly Security Report Generator for Aigis.

Generates automated weekly security reports following NIST SP 800-61 post-incident
reporting structure, adapted for LLM security monitoring.

This is the **Default Mode** feature — runs for all users with zero configuration.
Produces a report covering: summary, week-over-week trends, OWASP coverage,
detection layer stats, and recommended actions.

Usage::

    from aigis.weekly_report import WeeklyReportGenerator

    gen = WeeklyReportGenerator()
    report = gen.generate()        # dict
    text = gen.to_text(report)     # terminal-friendly
    md = gen.to_markdown(report)   # Markdown
    html = gen.to_html(report)     # self-contained HTML
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from aigis.monitor import SecurityMonitor


@dataclass
class WeeklyReport:
    """Structured weekly report data."""

    # Meta
    generated_at: str
    period_start: str
    period_end: str
    version: str

    # This week summary
    total_scans: int
    total_blocked: int
    total_review: int
    total_allowed: int
    safety_rate: float  # allowed / total
    detection_rate: float
    asr: float

    # Risk distribution
    risk_distribution: dict[str, int]

    # Category breakdown (sorted by count desc)
    category_counts: dict[str, int]

    # Detection layers
    detection_by_layer: dict[str, int]

    # OWASP coverage
    owasp_coverage: dict[str, dict[str, Any]]

    # Week-over-week trend
    prev_total_scans: int
    prev_total_blocked: int
    prev_safety_rate: float
    trend_scans_pct: float  # % change
    trend_blocked_pct: float
    trend_safety_pct: float  # percentage point change

    # Per-category trends
    category_trends: dict[str, dict[str, Any]]
    # {"sql_injection": {"this_week": 5, "prev_week": 3, "change_pct": 66.7, "direction": "up"}}

    # Recommended actions
    recommendations: list[dict[str, str]]
    # [{"severity": "warning", "message": "SQL Injection increased 67% — review rules"}]

    # Auto-fix stats
    learned_patterns_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WeeklyReportGenerator:
    """Generate weekly security reports from SecurityMonitor data."""

    def __init__(self, monitor: SecurityMonitor | None = None):
        self.monitor = monitor or SecurityMonitor()

    def generate(self, as_of: datetime | None = None) -> WeeklyReport:
        """Generate a weekly report.

        Args:
            as_of: End date for the report period. Defaults to now.
        """
        now = as_of or datetime.now(UTC)
        this_week_end = now
        this_week_start = now - timedelta(days=7)
        prev_week_end = this_week_start
        prev_week_start = prev_week_end - timedelta(days=7)

        # Collect data for both weeks
        this_snap = self.monitor.snapshot(hours=7 * 24)
        prev_records = self._load_records_between(prev_week_start, prev_week_end)

        # Previous week aggregates
        prev_total = len(prev_records)
        prev_blocked = sum(1 for r in prev_records if r.get("is_blocked"))
        prev_review = sum(
            1
            for r in prev_records
            if r.get("risk_level") in ("medium", "high") and not r.get("is_blocked")
        )
        prev_allowed = prev_total - prev_blocked - prev_review
        prev_safety = prev_allowed / prev_total if prev_total > 0 else 1.0

        # This week
        this_total = this_snap.total_scans
        this_blocked = this_snap.total_blocked
        this_safety = this_snap.total_allowed / this_total if this_total > 0 else 1.0

        # Trends
        trend_scans = _pct_change(prev_total, this_total)
        trend_blocked = _pct_change(prev_blocked, this_blocked)
        trend_safety = (this_safety - prev_safety) * 100  # percentage points

        # Per-category trends
        prev_cat_counts: dict[str, int] = {}
        for r in prev_records:
            for cat in r.get("categories", []):
                prev_cat_counts[cat] = prev_cat_counts.get(cat, 0) + 1

        category_trends: dict[str, dict[str, Any]] = {}
        all_cats = set(this_snap.category_counts.keys()) | set(prev_cat_counts.keys())
        for cat in all_cats:
            this_count = this_snap.category_counts.get(cat, 0)
            prev_count = prev_cat_counts.get(cat, 0)
            change = _pct_change(prev_count, this_count)
            direction = "up" if change > 0 else "down" if change < 0 else "flat"
            category_trends[cat] = {
                "this_week": this_count,
                "prev_week": prev_count,
                "change_pct": round(change, 1),
                "direction": direction,
            }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            this_snap,
            category_trends,
            trend_blocked,
            this_safety,
        )

        # OWASP coverage
        owasp = self.monitor.owasp_scorecard()

        # Auto-fix stats
        learned_count = 0
        try:
            from aigis.auto_fix import load_learned_patterns

            learned_count = len(load_learned_patterns())
        except Exception:
            pass

        return WeeklyReport(
            generated_at=now.isoformat(),
            period_start=this_week_start.strftime("%Y-%m-%d"),
            period_end=this_week_end.strftime("%Y-%m-%d"),
            version=_get_version(),
            total_scans=this_total,
            total_blocked=this_blocked,
            total_review=this_snap.total_review,
            total_allowed=this_snap.total_allowed,
            safety_rate=round(this_safety, 4),
            detection_rate=round(this_snap.detection_rate, 4),
            asr=round(this_snap.asr, 4),
            risk_distribution=this_snap.risk_distribution,
            category_counts=dict(this_snap.category_counts),
            detection_by_layer=dict(this_snap.detection_by_layer),
            owasp_coverage=owasp,
            prev_total_scans=prev_total,
            prev_total_blocked=prev_blocked,
            prev_safety_rate=round(prev_safety, 4),
            trend_scans_pct=round(trend_scans, 1),
            trend_blocked_pct=round(trend_blocked, 1),
            trend_safety_pct=round(trend_safety, 2),
            category_trends=category_trends,
            recommendations=recommendations,
            learned_patterns_count=learned_count,
        )

    # === Output Formats ===

    def to_text(self, report: WeeklyReport) -> str:
        """Generate terminal-friendly text output."""
        r = report
        lines: list[str] = []
        a = lines.append

        a("=" * 62)
        a("  Aigis Weekly Security Report")
        a(f"  Period: {r.period_start} ~ {r.period_end}")
        a("=" * 62)
        a("")

        # Summary
        a("  SUMMARY")
        a("  " + "-" * 40)
        a(f"  Total Scans:     {r.total_scans:>8,}")
        a(
            f"  Blocked:         {r.total_blocked:>8,}  ({_arrow(r.trend_blocked_pct)} {abs(r.trend_blocked_pct):.0f}% vs prev week)"
        )
        a(f"  Review:          {r.total_review:>8,}")
        a(f"  Allowed:         {r.total_allowed:>8,}")
        a(
            f"  Safety Rate:     {r.safety_rate:>7.1%}  ({_arrow(r.trend_safety_pct)} {abs(r.trend_safety_pct):.1f}pp)"
        )
        a(f"  Detection Rate:  {r.detection_rate:>7.1%}")
        a(f"  ASR:             {r.asr:>7.1%}  (lower = better)")
        a("")

        # Risk distribution
        a("  RISK DISTRIBUTION")
        a("  " + "-" * 40)
        for level in ("critical", "high", "medium", "low"):
            count = r.risk_distribution.get(level, 0)
            bar = "#" * min(count, 40)
            a(f"  {level:>8s}  {count:>5,}  {bar}")
        a("")

        # Category trends
        if r.category_trends:
            a("  THREAT CATEGORIES (week-over-week)")
            a("  " + "-" * 40)
            sorted_cats = sorted(
                r.category_trends.items(),
                key=lambda x: x[1]["this_week"],
                reverse=True,
            )
            for cat, trend in sorted_cats:
                arrow = _arrow(trend["change_pct"])
                a(
                    f"  {cat:>22s}  {trend['prev_week']:>3} -> {trend['this_week']:>3}  {arrow} {abs(trend['change_pct']):.0f}%"
                )
            a("")

        # Detection layers
        if r.detection_by_layer:
            a("  DETECTION LAYERS")
            a("  " + "-" * 40)
            for layer, count in r.detection_by_layer.items():
                a(f"  {layer:>12s}  {count:>5,}")
            a("")

        # OWASP coverage
        a("  OWASP LLM TOP 10 COVERAGE")
        a("  " + "-" * 40)
        for oid in sorted(r.owasp_coverage.keys()):
            cov = r.owasp_coverage[oid]
            status = cov.get("protection_level", "not-covered").upper()
            hits = cov.get("detections", 0)
            a(f"  {oid}  {cov['name']:<32s}  {status:<14s}  {hits:>3} hits")
        a("")

        # Recommendations
        if r.recommendations:
            a("  RECOMMENDED ACTIONS")
            a("  " + "-" * 40)
            for i, rec in enumerate(r.recommendations, 1):
                icon = {"critical": "!!", "warning": "! ", "info": "  "}[rec["severity"]]
                a(f"  [{icon}] {rec['message']}")
            a("")

        # Auto-fix
        if r.learned_patterns_count > 0:
            a(f"  AUTO-FIX: {r.learned_patterns_count} learned patterns available")
            a("")

        a("-" * 62)
        a(f"  Generated by Aigis v{r.version}")
        a("")
        return "\n".join(lines)

    def to_markdown(self, report: WeeklyReport) -> str:
        """Generate Markdown report."""
        r = report
        lines: list[str] = []
        a = lines.append

        a("# Aigis Weekly Security Report")
        a("")
        a(f"**Period**: {r.period_start} ~ {r.period_end} | **Generated**: {r.generated_at[:10]}")
        a("")

        # Summary table
        a("## Summary")
        a("")
        a("| Metric | This Week | Prev Week | Trend |")
        a("|--------|-----------|-----------|-------|")
        a(
            f"| Total Scans | {r.total_scans:,} | {r.prev_total_scans:,} | {_trend_badge(r.trend_scans_pct)} |"
        )
        a(
            f"| Blocked | {r.total_blocked:,} | {r.prev_total_blocked:,} | {_trend_badge(r.trend_blocked_pct)} |"
        )
        a(
            f"| Safety Rate | {r.safety_rate:.1%} | {r.prev_safety_rate:.1%} | {_trend_badge_safety(r.trend_safety_pct)} |"
        )
        a(f"| Detection Rate | {r.detection_rate:.1%} | - | - |")
        a(f"| ASR | {r.asr:.1%} | - | - |")
        a("")

        # Risk distribution
        a("## Risk Distribution")
        a("")
        a("| Level | Count |")
        a("|-------|-------|")
        for level in ("critical", "high", "medium", "low"):
            count = r.risk_distribution.get(level, 0)
            a(f"| {level.upper()} | {count:,} |")
        a("")

        # Category trends
        if r.category_trends:
            a("## Threat Categories (Week-over-Week)")
            a("")
            a("| Category | Prev | This | Change |")
            a("|----------|------|------|--------|")
            sorted_cats = sorted(
                r.category_trends.items(),
                key=lambda x: x[1]["this_week"],
                reverse=True,
            )
            for cat, t in sorted_cats:
                a(
                    f"| {cat} | {t['prev_week']} | {t['this_week']} | {_trend_badge(t['change_pct'])} |"
                )
            a("")

        # OWASP
        a("## OWASP LLM Top 10 Coverage")
        a("")
        a("| ID | Threat | Status | Detections |")
        a("|----|--------|--------|------------|")
        for oid in sorted(r.owasp_coverage.keys()):
            cov = r.owasp_coverage[oid]
            status = cov.get("protection_level", "not-covered").upper()
            a(f"| {oid} | {cov['name']} | {status} | {cov.get('detections', 0)} |")
        a("")

        # Recommendations
        if r.recommendations:
            a("## Recommended Actions")
            a("")
            for rec in r.recommendations:
                icon = {"critical": "**[CRITICAL]**", "warning": "**[WARNING]**", "info": "[INFO]"}[
                    rec["severity"]
                ]
                a(f"- {icon} {rec['message']}")
            a("")

        a("---")
        a(f"*Generated by Aigis v{r.version}*")
        return "\n".join(lines)

    def to_json(self, report: WeeklyReport) -> str:
        """Generate JSON output."""
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False, default=str)

    # === Internal ===

    def _load_records_between(self, start: datetime, end: datetime) -> list[dict]:
        """Load scan records from a specific time range."""
        scan_file = self.monitor.data_dir / "scans.jsonl"
        if not scan_file.exists():
            return []
        records = []
        for record in self.monitor._read_jsonl(scan_file):
            try:
                ts = datetime.fromisoformat(record["timestamp"])
                if start <= ts < end:
                    records.append(record)
            except (KeyError, ValueError):
                continue
        return records

    def _generate_recommendations(
        self,
        snap: Any,
        category_trends: dict[str, dict[str, Any]],
        trend_blocked_pct: float,
        safety_rate: float,
    ) -> list[dict[str, str]]:
        """Generate actionable recommendations based on data."""
        recs: list[dict[str, str]] = []

        # 1. Categories with significant increase
        for cat, trend in category_trends.items():
            if trend["change_pct"] > 50 and trend["this_week"] >= 3:
                recs.append(
                    {
                        "severity": "warning",
                        "message": f"{cat} increased {trend['change_pct']:.0f}% this week "
                        f"({trend['prev_week']} -> {trend['this_week']}). "
                        f"Consider reviewing detection rules for this category.",
                    }
                )

        # 2. New categories appearing
        for cat, trend in category_trends.items():
            if trend["prev_week"] == 0 and trend["this_week"] > 0:
                recs.append(
                    {
                        "severity": "info",
                        "message": f"New threat category detected: {cat} "
                        f"({trend['this_week']} occurrences). Monitor closely.",
                    }
                )

        # 3. High blocked rate increase
        if trend_blocked_pct > 100:
            recs.append(
                {
                    "severity": "warning",
                    "message": f"Blocked requests doubled ({trend_blocked_pct:.0f}% increase). "
                    f"Investigate whether this is a targeted attack or false positives.",
                }
            )

        # 4. Low safety rate
        if safety_rate < 0.9:
            recs.append(
                {
                    "severity": "critical",
                    "message": f"Safety rate is {safety_rate:.1%}, below 90% threshold. "
                    f"Review blocked and review-queued requests for false positives.",
                }
            )

        # 5. Auto-fix suggestions available
        try:
            from aigis.auto_fix import load_learned_patterns

            learned = load_learned_patterns()
            unapplied = [p for p in learned if not p.get("auto_applied")]
            if unapplied:
                recs.append(
                    {
                        "severity": "info",
                        "message": f"{len(unapplied)} auto-fix rules are pending review. "
                        f"Run `aigis adversarial-loop --auto-fix` to apply.",
                    }
                )
        except Exception:
            pass

        # 6. Detection layers with zero hits
        active_layers = {k for k, v in snap.detection_by_layer.items() if v > 0}
        all_layers = {"regex", "similarity", "decoded", "multi_turn"}
        unused = all_layers - active_layers
        if unused and snap.total_scans > 10:
            recs.append(
                {
                    "severity": "info",
                    "message": f"Detection layers with no hits this week: {', '.join(sorted(unused))}. "
                    f"This is normal if no obfuscated attacks were attempted.",
                }
            )

        # 7. Zero scans warning
        if snap.total_scans == 0:
            recs.append(
                {
                    "severity": "warning",
                    "message": "No scans recorded this week. Verify that Aigis is properly "
                    "integrated into your LLM pipeline.",
                }
            )

        return recs


# === Helpers ===


def _get_version() -> str:
    try:
        from aigis import __version__

        return __version__
    except ImportError:
        return "unknown"


def _pct_change(old: int, new: int) -> float:
    """Calculate percentage change, handling zero division."""
    if old == 0:
        return 100.0 if new > 0 else 0.0
    return ((new - old) / old) * 100


def _arrow(pct: float) -> str:
    if pct > 5:
        return "↑"
    elif pct < -5:
        return "↓"
    return "→"


def _trend_badge(pct: float) -> str:
    """Markdown trend badge."""
    if pct > 5:
        return f"↑ {abs(pct):.0f}%"
    elif pct < -5:
        return f"↓ {abs(pct):.0f}%"
    return "→ flat"


def _trend_badge_safety(pp: float) -> str:
    """Safety rate trend (higher is better)."""
    if pp > 0.5:
        return f"↑ +{pp:.1f}pp"
    elif pp < -0.5:
        return f"↓ {pp:.1f}pp"
    return "→ stable"
