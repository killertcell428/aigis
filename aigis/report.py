"""MonitoringReport — rich security reports for Aigis.

Generates HTML and Markdown reports from SecurityMonitor data, highlighting
Aigis's unique multi-layer detection pipeline and comparing coverage
against industry standards (OWASP LLM Top 10).

Inspired by 0din-ai/ai-scanner's probe-level PDF reports and ASR trend
tracking (Apache 2.0). Implementation is original to Aigis.

Usage::

    from aigis.monitor import SecurityMonitor
    from aigis.report import MonitoringReport

    monitor = SecurityMonitor()
    report = MonitoringReport(monitor)

    # Generate HTML report
    html = report.generate_html(days=30)
    Path("report.html").write_text(html)

    # Generate Markdown report
    md = report.generate_markdown(days=30)

    # Generate JSON data for dashboards
    data = report.generate_json(days=30)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aigis.monitor import OWASP_LLM_TOP10, SecurityMonitor


class MonitoringReport:
    """Generate rich security monitoring reports."""

    def __init__(self, monitor: SecurityMonitor | None = None):
        self.monitor = monitor or SecurityMonitor()

    def generate_json(self, days: int = 30) -> dict[str, Any]:
        """Generate structured JSON report data."""
        snap = self.monitor.snapshot(hours=days * 24)
        asr_trend = self.monitor.asr_trend(days=days)
        heatmap = self.monitor.category_heatmap(days=days)
        scorecard = self.monitor.owasp_scorecard()

        # Collect benchmark data
        benchmarks = []
        bm_file = self.monitor.data_dir / "benchmarks.jsonl"
        if bm_file.exists():
            benchmarks = self.monitor._read_jsonl(bm_file)

        return {
            "report_meta": {
                "generated_at": datetime.now(UTC).isoformat(),
                "period_days": days,
                "tool": "Aigis",
                "version": _get_version(),
            },
            "summary": {
                "total_scans": snap.total_scans,
                "total_blocked": snap.total_blocked,
                "total_review": snap.total_review,
                "total_allowed": snap.total_allowed,
                "detection_rate": snap.detection_rate,
                "asr": snap.asr,
                "risk_distribution": snap.risk_distribution,
            },
            "asr_trend": asr_trend,
            "category_heatmap": heatmap,
            "owasp_scorecard": scorecard,
            "detection_pipeline": {
                "layers": snap.detection_by_layer,
                "description": {
                    "regex": "Pattern matching (165+ rules, 25 categories)",
                    "similarity": "Semantic similarity against known attack corpus",
                    "decoded": "Encoded payload detection (Base64/hex/URL/ROT13)",
                    "multi_turn": "Multi-turn conversation escalation analysis",
                },
            },
            "unique_capabilities": _get_unique_capabilities(snap),
            "benchmarks": benchmarks[-10:],  # Last 10 benchmark runs
            "direction_breakdown": snap.by_direction,
        }

    def generate_markdown(self, days: int = 30) -> str:
        """Generate Markdown report."""
        data = self.generate_json(days=days)
        snap = data["summary"]
        meta = data["report_meta"]

        lines: list[str] = []
        _a = lines.append

        _a("# Aigis Security Report")
        _a("")
        _a(
            f"**Period**: Last {days} days | **Generated**: {meta['generated_at'][:10]} | **Version**: {meta['version']}"
        )
        _a("")

        # --- Summary ---
        _a("## Summary")
        _a("")
        _a("| Metric | Value |")
        _a("|--------|-------|")
        _a(f"| Total Scans | {snap['total_scans']:,} |")
        _a(f"| Blocked (Critical) | {snap['total_blocked']:,} |")
        _a(f"| Review Required | {snap['total_review']:,} |")
        _a(f"| Allowed | {snap['total_allowed']:,} |")
        _a(f"| Detection Rate | {snap['detection_rate']:.1%} |")
        _a(f"| Attack Success Rate (ASR) | {snap['asr']:.1%} |")
        _a("")

        # Risk distribution
        risk = snap["risk_distribution"]
        total_risk = sum(risk.values()) or 1
        _a("### Risk Distribution")
        _a("")
        _a("| Level | Count | Share |")
        _a("|-------|-------|-------|")
        for level in ("critical", "high", "medium", "low"):
            count = risk.get(level, 0)
            _a(f"| {level.upper()} | {count:,} | {count / total_risk:.1%} |")
        _a("")

        # --- ASR Trend ---
        trend = data["asr_trend"]
        if trend:
            _a("## ASR Trend (Attack Success Rate)")
            _a("")
            _a("> Lower ASR = better defense. Inspired by 0din-ai/ai-scanner's ASR tracking.")
            _a("")
            _a("| Date | Attacks | Blocked | Bypassed | ASR |")
            _a("|------|---------|---------|----------|-----|")
            for t in trend[-14:]:  # Last 14 days
                _a(
                    f"| {t['date']} | {t['total_attacks']} | {t['blocked']} | {t['bypassed']} | {t['asr']:.1%} |"
                )
            _a("")

        # --- OWASP LLM Top 10 Scorecard ---
        _a("## OWASP LLM Top 10 Coverage")
        _a("")
        scorecard = data["owasp_scorecard"]
        _a("| ID | Threat | Protection | Detections | Aigis Unique |")
        _a("|----|--------|------------|------------|-------------------|")
        for oid in sorted(scorecard.keys()):
            sc = scorecard[oid]
            level = sc.get("protection_level", "not-covered")
            icon = {
                "active": "ACTIVE",
                "monitored": "MONITORED",
                "pattern-ready": "READY",
                "not-covered": "-",
            }[level]
            feats = ", ".join(sc.get("unique_features", [])[:2]) or "-"
            _a(f"| {oid} | {sc['name']} | {icon} | {sc.get('detections', 0)} | {feats} |")
        _a("")

        # --- Detection Pipeline (aigis unique) ---
        pipeline = data["detection_pipeline"]
        _a("## Multi-Layer Detection Pipeline")
        _a("")
        _a("> Aigis's 4-layer defense - what makes it different from scan-only tools.")
        _a("")
        _a("| Layer | Detections | Description |")
        _a("|-------|------------|-------------|")
        for layer in ("regex", "similarity", "decoded", "multi_turn"):
            count = pipeline["layers"].get(layer, 0)
            desc = pipeline["description"].get(layer, "")
            _a(f"| {layer} | {count:,} | {desc} |")
        _a("")

        # --- Unique Capabilities ---
        caps = data["unique_capabilities"]
        _a("## Aigis Differentiators")
        _a("")
        _a("| Capability | Status | vs. Scan-Only Tools |")
        _a("|------------|--------|---------------------|")
        for cap in caps:
            _a(f"| {cap['name']} | {cap['status']} | {cap['differentiator']} |")
        _a("")

        # --- Direction Breakdown ---
        dirs = data["direction_breakdown"]
        if dirs:
            _a("## Scan Direction Breakdown")
            _a("")
            _a("| Direction | Count |")
            _a("|-----------|-------|")
            for d, c in sorted(dirs.items(), key=lambda x: -x[1]):
                _a(f"| {d} | {c:,} |")
            _a("")

        _a("---")
        _a(f"*Generated by Aigis v{meta['version']}*")
        return "\n".join(lines)

    def generate_html(self, days: int = 30) -> str:
        """Generate a self-contained HTML report with embedded CSS and charts."""
        data = self.generate_json(days=days)
        snap = data["summary"]
        meta = data["report_meta"]
        trend = data["asr_trend"]
        scorecard = data["owasp_scorecard"]
        pipeline = data["detection_pipeline"]
        caps = data["unique_capabilities"]
        risk = snap["risk_distribution"]

        # Build ASR chart data
        asr_dates = json.dumps([t["date"][-5:] for t in trend[-30:]])
        asr_values = json.dumps([round(t["asr"] * 100, 1) for t in trend[-30:]])
        blocked_values = json.dumps([t["blocked"] for t in trend[-30:]])
        bypassed_values = json.dumps([t["bypassed"] for t in trend[-30:]])

        # OWASP coverage data
        owasp_ids = json.dumps(list(OWASP_LLM_TOP10.keys()))
        owasp_detections = json.dumps(
            [scorecard.get(oid, {}).get("detections", 0) for oid in OWASP_LLM_TOP10]
        )

        # Detection layer data
        layer_names = json.dumps(
            list(pipeline["layers"].keys())
            if pipeline["layers"]
            else ["regex", "similarity", "decoded", "multi_turn"]
        )
        layer_values = json.dumps(
            list(pipeline["layers"].values()) if pipeline["layers"] else [0, 0, 0, 0]
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aigis Security Report</title>
<style>
:root {{
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --yellow: #d29922;
    --orange: #db6d28;
    --red: #f85149;
    --purple: #bc8cff;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif; line-height:1.6; }}
.container {{ max-width:1200px; margin:0 auto; padding:2rem; }}
h1 {{ font-size:2rem; margin-bottom:0.5rem; }}
h2 {{ font-size:1.4rem; margin:2rem 0 1rem; color:var(--accent); border-bottom:1px solid var(--border); padding-bottom:0.5rem; }}
h3 {{ font-size:1.1rem; margin:1rem 0 0.5rem; color:var(--text-muted); }}
.subtitle {{ color:var(--text-muted); margin-bottom:2rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:1rem; margin:1rem 0; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1.5rem; }}
.card .label {{ color:var(--text-muted); font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; }}
.card .value {{ font-size:2rem; font-weight:700; margin-top:0.25rem; }}
.card .sub {{ color:var(--text-muted); font-size:0.85rem; margin-top:0.25rem; }}
.card.green .value {{ color:var(--green); }}
.card.red .value {{ color:var(--red); }}
.card.yellow .value {{ color:var(--yellow); }}
.card.accent .value {{ color:var(--accent); }}
table {{ width:100%; border-collapse:collapse; margin:1rem 0; }}
th {{ background:var(--card); text-align:left; padding:0.75rem; border-bottom:2px solid var(--border); font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-muted); }}
td {{ padding:0.75rem; border-bottom:1px solid var(--border); }}
tr:hover {{ background:rgba(88,166,255,0.04); }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }}
.badge-active {{ background:rgba(63,185,80,0.15); color:var(--green); }}
.badge-monitored {{ background:rgba(210,153,34,0.15); color:var(--yellow); }}
.badge-ready {{ background:rgba(88,166,255,0.15); color:var(--accent); }}
.badge-none {{ background:rgba(139,148,158,0.15); color:var(--text-muted); }}
.chart-container {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1.5rem; margin:1rem 0; }}
canvas {{ max-width:100%; }}
.pipeline {{ display:flex; gap:0; margin:1rem 0; align-items:stretch; }}
.pipe-stage {{ flex:1; background:var(--card); border:1px solid var(--border); padding:1rem; text-align:center; position:relative; }}
.pipe-stage:first-child {{ border-radius:8px 0 0 8px; }}
.pipe-stage:last-child {{ border-radius:0 8px 8px 0; }}
.pipe-stage .pipe-name {{ font-weight:600; font-size:0.9rem; }}
.pipe-stage .pipe-count {{ font-size:1.5rem; font-weight:700; color:var(--accent); margin:0.5rem 0; }}
.pipe-stage .pipe-desc {{ font-size:0.75rem; color:var(--text-muted); }}
.pipe-arrow {{ display:flex; align-items:center; color:var(--accent); font-size:1.5rem; padding:0 0.25rem; }}
.diff-table td:first-child {{ font-weight:600; }}
.diff-table .check {{ color:var(--green); }}
.diff-table .cross {{ color:var(--red); }}
.risk-bar {{ display:flex; height:24px; border-radius:4px; overflow:hidden; margin:0.5rem 0; }}
.risk-bar span {{ display:flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:600; min-width:30px; }}
footer {{ margin-top:3rem; padding-top:1rem; border-top:1px solid var(--border); color:var(--text-muted); font-size:0.85rem; text-align:center; }}
</style>
</head>
<body>
<div class="container">
<h1>Aigis Security Report</h1>
<p class="subtitle">Period: Last {days} days &middot; Generated: {meta["generated_at"][:10]} &middot; Version: {meta["version"]}</p>

<div class="grid">
    <div class="card accent">
        <div class="label">Total Scans</div>
        <div class="value">{snap["total_scans"]:,}</div>
    </div>
    <div class="card green">
        <div class="label">Blocked</div>
        <div class="value">{snap["total_blocked"]:,}</div>
        <div class="sub">Critical threats stopped</div>
    </div>
    <div class="card yellow">
        <div class="label">Review Required</div>
        <div class="value">{snap["total_review"]:,}</div>
    </div>
    <div class="card {"green" if snap["detection_rate"] >= 0.95 else "yellow" if snap["detection_rate"] >= 0.8 else "red"}">
        <div class="label">Detection Rate</div>
        <div class="value">{snap["detection_rate"]:.1%}</div>
        <div class="sub">Higher is better</div>
    </div>
    <div class="card {"green" if snap["asr"] <= 0.05 else "yellow" if snap["asr"] <= 0.2 else "red"}">
        <div class="label">ASR</div>
        <div class="value">{snap["asr"]:.1%}</div>
        <div class="sub">Attack Success Rate (lower = better)</div>
    </div>
</div>

<h2>Risk Distribution</h2>
{_render_risk_bar(risk)}

<h2>Multi-Layer Detection Pipeline</h2>
<p style="color:var(--text-muted); margin-bottom:1rem;">Aigis's 4-layer defense — what makes it different from scan-only tools like ai-scanner.</p>
<div class="pipeline">
    <div class="pipe-stage">
        <div class="pipe-name">Layer 1: Regex</div>
        <div class="pipe-count">{pipeline["layers"].get("regex", 0):,}</div>
        <div class="pipe-desc">165+ patterns, 25 categories</div>
    </div>
    <div class="pipe-arrow">&rarr;</div>
    <div class="pipe-stage">
        <div class="pipe-name">Layer 2: Similarity</div>
        <div class="pipe-count">{pipeline["layers"].get("similarity", 0):,}</div>
        <div class="pipe-desc">Semantic matching vs known attacks</div>
    </div>
    <div class="pipe-arrow">&rarr;</div>
    <div class="pipe-stage">
        <div class="pipe-name">Layer 3: Decoded</div>
        <div class="pipe-count">{pipeline["layers"].get("decoded", 0):,}</div>
        <div class="pipe-desc">Base64 / hex / URL / ROT13</div>
    </div>
    <div class="pipe-arrow">&rarr;</div>
    <div class="pipe-stage">
        <div class="pipe-name">Layer 4: Multi-turn</div>
        <div class="pipe-count">{pipeline["layers"].get("multi_turn", 0):,}</div>
        <div class="pipe-desc">Conversation escalation analysis</div>
    </div>
</div>

<h2>ASR Trend</h2>
<div class="chart-container">
    <canvas id="asrChart" height="80"></canvas>
</div>

<h2>OWASP LLM Top 10 Scorecard</h2>
<div class="chart-container">
    <canvas id="owaspChart" height="60"></canvas>
</div>
<table>
    <thead><tr><th>ID</th><th>Threat</th><th>Protection</th><th>Detections</th><th>Aigis Unique Features</th></tr></thead>
    <tbody>
{_render_owasp_rows(scorecard)}
    </tbody>
</table>

<h2>Aigis vs. Scan-Only Tools</h2>
<table class="diff-table">
    <thead><tr><th>Capability</th><th>Aigis</th><th>Scan-Only Tools</th><th>Why It Matters</th></tr></thead>
    <tbody>
{_render_differentiator_rows(caps)}
    </tbody>
</table>

<h2>Detection Layer Distribution</h2>
<div class="chart-container">
    <canvas id="layerChart" height="60"></canvas>
</div>

<footer>
    Generated by Aigis v{meta["version"]} &middot;
    <a href="https://github.com/killertcell428/aigis" style="color:var(--accent);">GitHub</a>
</footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>
const colors = {{
    accent: '#58a6ff', green: '#3fb950', yellow: '#d29922',
    orange: '#db6d28', red: '#f85149', purple: '#bc8cff',
    text: '#8b949e', grid: '#30363d'
}};
const chartDefaults = {{
    color: colors.text,
    borderColor: colors.grid,
}};
Chart.defaults.color = colors.text;
Chart.defaults.borderColor = colors.grid;

// ASR Trend Chart
new Chart(document.getElementById('asrChart'), {{
    type: 'line',
    data: {{
        labels: {asr_dates},
        datasets: [
            {{ label: 'ASR %', data: {asr_values}, borderColor: colors.red, backgroundColor: 'rgba(248,81,73,0.1)', fill: true, tension: 0.3 }},
            {{ label: 'Blocked', data: {blocked_values}, borderColor: colors.green, backgroundColor: 'transparent', tension: 0.3, yAxisID: 'y1' }},
            {{ label: 'Bypassed', data: {bypassed_values}, borderColor: colors.orange, backgroundColor: 'transparent', tension: 0.3, yAxisID: 'y1' }},
        ]
    }},
    options: {{
        responsive: true,
        plugins: {{ title: {{ display: true, text: 'Attack Success Rate Trend (lower ASR = better defense)' }} }},
        scales: {{
            y: {{ title: {{ display: true, text: 'ASR (%)' }}, min: 0, max: 100 }},
            y1: {{ position: 'right', title: {{ display: true, text: 'Count' }}, grid: {{ drawOnChartArea: false }} }}
        }}
    }}
}});

// OWASP Coverage Chart
new Chart(document.getElementById('owaspChart'), {{
    type: 'bar',
    data: {{
        labels: {owasp_ids},
        datasets: [{{ label: 'Detections', data: {owasp_detections}, backgroundColor: colors.accent }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ title: {{ display: true, text: 'OWASP LLM Top 10 Detection Coverage' }} }},
        scales: {{ y: {{ beginAtZero: true }} }}
    }}
}});

// Detection Layer Chart
new Chart(document.getElementById('layerChart'), {{
    type: 'doughnut',
    data: {{
        labels: {layer_names},
        datasets: [{{ data: {layer_values}, backgroundColor: [colors.accent, colors.green, colors.yellow, colors.purple] }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ title: {{ display: true, text: 'Detections by Pipeline Layer' }} }}
    }}
}});
</script>
</body>
</html>"""

        return html

    def save(self, output_path: str, days: int = 30, fmt: str = "html") -> str:
        """Generate and save a report to file.

        Args:
            output_path: Destination file path.
            days: Report period in days.
            fmt: "html", "markdown", or "json".

        Returns:
            The output file path.
        """
        if fmt == "html":
            content = self.generate_html(days=days)
        elif fmt == "markdown":
            content = self.generate_markdown(days=days)
        elif fmt == "json":
            content = json.dumps(self.generate_json(days=days), indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unknown format: {fmt}")

        Path(output_path).write_text(content, encoding="utf-8")
        return output_path


# === Helpers ===


def _get_version() -> str:
    try:
        from aigis import __version__

        return __version__
    except ImportError:
        return "unknown"


def _get_unique_capabilities(snap: Any) -> list[dict]:
    """Build the differentiator table data."""
    return [
        {
            "name": "Real-time Inline Blocking",
            "status": "Active",
            "differentiator": "Blocks threats BEFORE they reach the LLM, not after",
            "scan_only": "Post-hoc scanning only",
        },
        {
            "name": "Multi-Layer Detection",
            "status": f"{len([v for v in snap.detection_by_layer.values() if v > 0])}/4 layers active",
            "differentiator": "4 independent detection layers catch what single-layer misses",
            "scan_only": "Single probe layer",
        },
        {
            "name": "Auto-Fix (Adversarial Loop)",
            "status": f"{snap.learned_patterns_count} learned patterns",
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
            "differentiator": "pip install, no Docker/infra required. Embeds in any Python app",
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
    ]


def _render_risk_bar(risk: dict) -> str:
    total = sum(risk.values()) or 1
    parts = []
    colors = {"critical": "#f85149", "high": "#db6d28", "medium": "#d29922", "low": "#3fb950"}
    for level in ("critical", "high", "medium", "low"):
        count = risk.get(level, 0)
        pct = count / total * 100
        if pct > 0:
            parts.append(
                f'<span style="background:{colors[level]};width:{pct}%">{level[0].upper()} {count}</span>'
            )
    return f'<div class="risk-bar">{"".join(parts)}</div>'


def _render_owasp_rows(scorecard: dict) -> str:
    rows = []
    for oid in sorted(scorecard.keys()):
        sc = scorecard[oid]
        level = sc.get("protection_level", "not-covered")
        badge_cls = {
            "active": "badge-active",
            "monitored": "badge-monitored",
            "pattern-ready": "badge-ready",
        }.get(level, "badge-none")
        badge_text = level.upper().replace("-", " ")
        feats = "<br>".join(sc.get("unique_features", [])) or "-"
        rows.append(
            f"<tr><td>{oid}</td><td>{sc['name']}</td>"
            f'<td><span class="badge {badge_cls}">{badge_text}</span></td>'
            f"<td>{sc.get('detections', 0)}</td>"
            f'<td style="font-size:0.85rem">{feats}</td></tr>'
        )
    return "\n".join(rows)


def _render_differentiator_rows(caps: list[dict]) -> str:
    rows = []
    for cap in caps:
        rows.append(
            f"<tr><td>{cap['name']}</td>"
            f'<td class="check">{cap["status"]}</td>'
            f'<td class="cross">{cap.get("scan_only", "-")}</td>'
            f'<td style="color:var(--text-muted)">{cap["differentiator"]}</td></tr>'
        )
    return "\n".join(rows)
