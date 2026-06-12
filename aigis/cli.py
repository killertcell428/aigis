"""Aigis CLI - command-line interface for agent governance.

Usage:
    aigis init                     # Initialize Aigis in current project
    aigis init --agent claude-code # Also configure Claude Code hooks
    aigis doctor                   # Diagnose setup issues
    aigis status                   # Show governance status summary
    aigis logs                     # View recent activity
    aigis logs --action shell:exec # Filter by action type
    aigis logs --risk-above 50     # Filter by risk score
    aigis logs --alerts            # Show blocked/reviewed events only
    aigis logs --export-csv out.csv  # Export to CSV
    aigis policy check             # Validate policy file
    aigis policy show              # Show all rules
    aigis scan "rm -rf /"          # Scan text for threats
    aigis scan --file prompt.txt   # Scan a file
    echo "text" | aigis scan       # Scan from stdin
    aigis report --days 30         # Generate compliance report
    aigis maintenance              # Rotate and compress old logs
    aigis mcp '{"name":"add",...}'  # Scan MCP tool definition for poisoning
    aigis mcp --file tools.json    # Scan MCP tools from JSON file
    aigis trust-pack               # Generate IT/security adoption-approval pack
    aigis audit verify             # Verify signed audit-log integrity
    aigis audit status             # Show signed audit-log status
"""

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aigis",
        description="Aigis - Agent Governance CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # aig init
    init_p = sub.add_parser("init", help="Initialize Aigis in current project")
    init_p.add_argument("--agent", choices=["claude-code"], help="Configure agent adapter")
    init_p.add_argument(
        "--policy",
        choices=["developer", "reviewer", "restricted", "enterprise"],
        default="developer",
        help="Policy template to use",
    )

    # aig logs
    logs_p = sub.add_parser("logs", help="View activity stream")
    logs_p.add_argument("--action", help="Filter by action (e.g., shell:exec)")
    logs_p.add_argument("--agent-type", help="Filter by agent type")
    logs_p.add_argument("--risk-above", type=int, help="Show events with risk > N")
    logs_p.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    logs_p.add_argument("--limit", type=int, default=20, help="Max events (default: 20)")
    logs_p.add_argument("--json", action="store_true", help="Output as JSON")
    logs_p.add_argument(
        "--global", dest="use_global", action="store_true", help="Query global logs (all projects)"
    )
    logs_p.add_argument("--alerts", action="store_true", help="Show alerts only (blocked/reviewed)")
    logs_p.add_argument("--export-csv", metavar="PATH", help="Export to CSV file")
    logs_p.add_argument(
        "--export-excel", metavar="PATH", help="Export summary + events to Excel-compatible CSVs"
    )

    # aig policy
    policy_p = sub.add_parser("policy", help="Policy management")
    policy_p.add_argument("action", choices=["check", "show", "reset"], help="Policy action")

    # aig status
    sub.add_parser("status", help="Show governance status summary")

    # aig report
    report_p = sub.add_parser("report", help="Generate compliance report")
    report_p.add_argument(
        "report_type",
        nargs="?",
        default=None,
        choices=["weekly"],
        help="Report type (e.g. 'weekly')",
    )
    report_p.add_argument("--days", type=int, default=30, help="Report period in days")
    report_p.add_argument("--format", choices=["text", "json", "html", "markdown"], default="text")
    report_p.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="Save report to file (auto-detects format from extension: .html/.md/.json)",
    )

    # aig monitor
    monitor_p = sub.add_parser("monitor", help="Security monitoring dashboard")
    monitor_p.add_argument(
        "--hours", type=float, default=24, help="Look-back period in hours (default: 24)"
    )
    monitor_p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    monitor_p.add_argument("--asr-trend", action="store_true", help="Show ASR trend over time")
    monitor_p.add_argument("--days", type=int, default=30, help="Days for trend data (default: 30)")
    monitor_p.add_argument("--owasp", action="store_true", help="Show OWASP LLM Top 10 scorecard")

    # aig maintenance
    maint_p = sub.add_parser("maintenance", help="Log maintenance (rotate, compress)")
    maint_p.add_argument(
        "--retention-days", type=int, default=60, help="Keep full logs for N days (default: 60)"
    )
    maint_p.add_argument(
        "--compress-after", type=int, default=7, help="Compress after N days (default: 7)"
    )

    # aig doctor
    sub.add_parser("doctor", help="Diagnose Aigis setup issues")

    # aig scan (quick scan from CLI)
    scan_p = sub.add_parser("scan", help="Scan text for threats")
    scan_p.add_argument("text", nargs="?", help="Text to scan (or read from stdin)")
    scan_p.add_argument(
        "--file",
        dest="scan_file",
        metavar="PATH",
        help="Scan a file instead of a text argument (reads entire file contents)",
    )
    scan_p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output results as JSON (machine-readable)",
    )

    # aig mcp
    mcp_p = sub.add_parser("mcp", help="Scan MCP tool definitions for security threats")
    mcp_p.add_argument(
        "mcp_input",
        nargs="?",
        help="MCP tool definition JSON string (or read from --file / stdin)",
    )
    mcp_p.add_argument(
        "--file",
        dest="mcp_file",
        metavar="PATH",
        help="JSON file containing MCP tool definition(s)",
    )
    mcp_p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output results as JSON",
    )
    mcp_p.add_argument(
        "--trust",
        action="store_true",
        help="Show server trust score and permission summary",
    )
    mcp_p.add_argument(
        "--diff",
        action="store_true",
        help="Compare against previous snapshots (rug pull detection)",
    )
    mcp_p.add_argument(
        "--snapshot-dir",
        metavar="PATH",
        default=".aigis/mcp_snapshots",
        help="Snapshot storage directory (default: .aigis/mcp_snapshots)",
    )
    mcp_p.add_argument(
        "--server",
        dest="server_url",
        metavar="URL",
        default="",
        help="MCP server URL (stored as metadata)",
    )

    # aig redteam
    red_p = sub.add_parser("redteam", help="Automated red team testing")
    red_p.add_argument("--category", help="Test only this category")
    red_p.add_argument("--count", type=int, default=10, help="Attacks per category (default: 10)")
    red_p.add_argument("--seed", type=int, help="Random seed for reproducibility")
    red_p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    red_p.add_argument("--adaptive", action="store_true", help="Run adaptive mutation mode")
    red_p.add_argument(
        "--rounds", type=int, default=3, help="Max mutation rounds for adaptive mode (default: 3)"
    )
    red_p.add_argument("--report", action="store_true", help="Generate vulnerability report")
    red_p.add_argument(
        "--report-format",
        choices=["markdown", "html"],
        default="markdown",
        help="Report format (default: markdown)",
    )
    red_p.add_argument("--report-path", metavar="PATH", help="Report output path")
    red_p.add_argument("--target-url", metavar="URL", help="HTTP endpoint to test against")
    red_p.add_argument("--multi-step", action="store_true", help="Include multi-step attack chains")

    # aig adversarial-loop
    adv_p = sub.add_parser("adversarial-loop", help="Run attack-defend-improve cycle")
    adv_p.add_argument(
        "--rounds", type=int, default=3, help="Number of adversarial rounds (default: 3)"
    )
    adv_p.add_argument(
        "--count", type=int, default=5, help="Attacks per category per round (default: 5)"
    )
    adv_p.add_argument("--category", help="Test only this category")
    adv_p.add_argument("--seed", type=int, help="Random seed for reproducibility")
    adv_p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    adv_p.add_argument(
        "--no-evolve", action="store_true", help="Disable bypass evolution between rounds"
    )
    adv_p.add_argument("--report", action="store_true", help="Generate full report")
    adv_p.add_argument(
        "--report-format",
        choices=["markdown", "json"],
        default="markdown",
        help="Report format (default: markdown)",
    )
    adv_p.add_argument("--report-path", metavar="PATH", help="Report output path")
    adv_p.add_argument("--proposals", metavar="PATH", help="Save defense proposals to JSON file")
    adv_p.add_argument(
        "--auto-fix",
        action="store_true",
        help="Auto-apply high/medium priority proposals, verify no FP regressions, rollback if needed",
    )
    adv_p.add_argument(
        "--min-priority",
        choices=["low", "medium", "high"],
        default="medium",
        help="Minimum priority for auto-fix (default: medium)",
    )
    adv_p.add_argument(
        "--no-rollback",
        action="store_true",
        help="Do not auto-rollback on false positive regressions",
    )

    # aig benchmark
    bench_p = sub.add_parser("benchmark", help="Run built-in adversarial test suite")
    bench_p.add_argument("--category", help="Test only this category (e.g., jailbreak)")
    bench_p.add_argument(
        "--latency", action="store_true", help="Run latency benchmark (measure scan speed)"
    )
    bench_p.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Iterations per input for latency benchmark (default: 100)",
    )
    bench_p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")
    bench_p.add_argument(
        "--threshold", type=int, default=1, help="Minimum score to count as detected (default: 1)"
    )
    bench_p.add_argument(
        "--report",
        action="store_true",
        help="Generate Markdown latency report (requires --latency)",
    )
    bench_p.add_argument(
        "--report-path",
        metavar="PATH",
        default="benchmark_report.md",
        help="Output path for latency report (default: benchmark_report.md)",
    )
    bench_p.add_argument(
        "--badge", action="store_true", help="Output shields.io badge JSON (requires --latency)"
    )

    # aig serve
    serve_p = sub.add_parser(
        "serve", help="Run Aigis as an HTTP sidecar (POST /v1/check/input etc.)"
    )
    serve_p.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    serve_p.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")

    # aigis trust-pack
    tp_p = sub.add_parser(
        "trust-pack",
        help="Generate an IT/security adoption-approval document pack from live config",
    )
    tp_p.add_argument(
        "--output",
        "-o",
        metavar="DIR",
        default="./aigis-trust-pack",
        help="Output directory (default: ./aigis-trust-pack)",
    )
    tp_p.add_argument(
        "--lang",
        choices=["ja", "en", "both"],
        default="both",
        help="Document language (default: both)",
    )
    tp_p.add_argument(
        "--format",
        choices=["markdown", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    tp_p.add_argument("--org", metavar="NAME", help="Organisation name to substitute into the pack")
    tp_p.add_argument(
        "--contact", metavar="EMAIL", help="Security contact email to substitute into the pack"
    )

    # aigis audit
    audit_p = sub.add_parser("audit", help="Signed audit-log integrity verification")
    audit_sub = audit_p.add_subparsers(dest="audit_command")
    audit_verify_p = audit_sub.add_parser("verify", help="Verify signed audit-log integrity")
    audit_verify_p.add_argument(
        "--log", metavar="PATH", help="Audit log path (default: .aigis/audit.jsonl)"
    )
    audit_verify_p.add_argument("--json", dest="json_output", action="store_true", help="JSON output")
    audit_status_p = audit_sub.add_parser("status", help="Show signed audit-log status")
    audit_status_p.add_argument(
        "--log", metavar="PATH", help="Audit log path (default: .aigis/audit.jsonl)"
    )
    audit_status_p.add_argument(
        "--json", dest="json_output", action="store_true", help="JSON output"
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        return cmd_init(args)
    elif args.command == "logs":
        return cmd_logs(args)
    elif args.command == "policy":
        return cmd_policy(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "report":
        return cmd_report(args)
    elif args.command == "monitor":
        return cmd_monitor(args)
    elif args.command == "maintenance":
        return cmd_maintenance(args)
    elif args.command == "doctor":
        return cmd_doctor(args)
    elif args.command == "scan":
        return cmd_scan(args)
    elif args.command == "mcp":
        return cmd_mcp(args)
    elif args.command == "redteam":
        return cmd_redteam(args)
    elif args.command == "adversarial-loop":
        return cmd_adversarial_loop(args)
    elif args.command == "benchmark":
        return cmd_benchmark(args)
    elif args.command == "serve":
        return cmd_serve(args)
    elif args.command == "trust-pack":
        return cmd_trust_pack(args)
    elif args.command == "audit":
        return cmd_audit(args, audit_p)
    else:
        parser.print_help()
        return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from aigis.server import serve

    serve(host=args.host, port=args.port)
    return 0


def cmd_trust_pack(args: argparse.Namespace) -> int:
    """Generate the IT/security adoption-approval document pack."""
    from aigis.trust_pack import TrustPackGenerator

    out_dir = Path(args.output)
    gen = TrustPackGenerator(org=args.org, contact=args.contact)

    if args.format == "html":
        path = gen.write_html(out_dir, lang=args.lang)
        print("Aigis Trust Pack generated (HTML)")
        print(f"  Output: {path}")
        print(f"  Language: {args.lang}")
        print(f"  Policy: {gen.evidence.policy_name} (v{gen.evidence.policy_version})")
        print("\n  Open in a browser, print to PDF, or email to your IT/security team.")
        return 0

    written = gen.write_markdown(out_dir, lang=args.lang)
    print("Aigis Trust Pack generated (Markdown)")
    print(f"  Output: {out_dir}/")
    print(f"  Language: {args.lang}")
    print(f"  Files: {len(written)}")
    for p in written:
        print(f"    - {p.name}")
    print(f"\n  Start with {out_dir}/README.md (the index).")
    if not gen.evidence.settings_hook_configured:
        print("\n  Note: Claude Code hook is not yet configured in this project.")
        print("        Run 'aigis init --agent claude-code' for a complete posture.")
    return 0


def cmd_audit(args: argparse.Namespace, audit_parser: argparse.ArgumentParser) -> int:
    """Signed audit-log integrity commands."""
    if args.audit_command == "verify":
        return _cmd_audit_verify(args)
    elif args.audit_command == "status":
        return _cmd_audit_status(args)
    else:
        audit_parser.print_help()
        return 0


def _default_audit_log_path() -> Path:
    return Path(".aigis") / "audit.jsonl"


def _cmd_audit_verify(args: argparse.Namespace) -> int:
    """Verify signed audit-log integrity (signature + chain + sequence + time)."""
    from aigis.audit import AuditVerifier
    from aigis.audit.signed_log import _resolve_key

    log_path = Path(args.log) if args.log else _default_audit_log_path()

    if not log_path.exists():
        msg = f"Audit log not found: {log_path}"
        if getattr(args, "json_output", False):
            print(json.dumps({"valid": False, "error": "log_not_found", "path": str(log_path)}))
        else:
            print(msg, file=sys.stderr)
            print("  No signed audit log to verify. Enable signed logging first.", file=sys.stderr)
        return 1

    # Resolve the HMAC key the same way SignedAuditLog does (.aigis/audit_key).
    key = _resolve_key(None).decode("utf-8")
    verifier = AuditVerifier(secret_key=key)
    result = verifier.verify_file(log_path)

    if getattr(args, "json_output", False):
        print(
            json.dumps(
                {
                    "valid": result.valid,
                    "total_entries": result.total_entries,
                    "checked_entries": result.checked_entries,
                    "chain_valid": result.chain_valid,
                    "signature_valid": result.signature_valid,
                    "broken_chain_at": result.broken_chain_at,
                    "invalid_signatures_at": result.invalid_signatures_at,
                    "sequence_errors_at": result.sequence_errors_at,
                    "timestamp_errors_at": result.timestamp_errors_at,
                    "summary": result.summary,
                },
                ensure_ascii=False,
            )
        )
        return 0 if result.valid else 1

    print("Aigis Audit Verify")
    print("=" * 50)
    print(f"  Log: {log_path}")
    print(f"  Entries: {result.total_entries}")

    def line(label: str, ok: bool) -> None:
        print(f"  [{'OK' if ok else 'FAIL'}] {label}")

    line("Signatures (HMAC-SHA256)", result.signature_valid)
    line("Hash chain", result.chain_valid)
    line("Sequence ordering", not result.sequence_errors_at)
    line("Timestamp ordering", not result.timestamp_errors_at)
    print()
    if result.valid:
        print("  PASS — no tampering detected.")
        return 0
    print("  FAIL — integrity check failed.")
    print(f"  {result.summary}")
    return 1


def _cmd_audit_status(args: argparse.Namespace) -> int:
    """Show signed audit-log status (key present? log present? entry count)."""
    log_path = Path(args.log) if args.log else _default_audit_log_path()
    key_path = Path(".aigis") / "audit_key"

    key_present = key_path.exists()
    log_present = log_path.exists()
    entry_count = 0
    if log_present:
        try:
            with open(log_path, encoding="utf-8") as f:
                entry_count = sum(1 for line in f if line.strip())
        except OSError:
            entry_count = 0

    if getattr(args, "json_output", False):
        print(
            json.dumps(
                {
                    "key_present": key_present,
                    "key_path": str(key_path),
                    "log_present": log_present,
                    "log_path": str(log_path),
                    "entry_count": entry_count,
                },
                ensure_ascii=False,
            )
        )
        return 0

    print("Aigis Audit Status")
    print("=" * 50)
    print(f"  HMAC key: {'present' if key_present else 'absent'} ({key_path})")
    print(f"  Audit log: {'present' if log_present else 'absent'} ({log_path})")
    print(f"  Entries: {entry_count}")
    if not key_present and not log_present:
        print("\n  Signed audit logging is not yet active.")
    return 0


def _warn_if_hooks_disabled(project_dir: str = ".") -> None:
    """Check if Claude Code hooks are disabled and warn the user."""
    local_settings = Path(project_dir) / ".claude" / "settings.local.json"
    if not local_settings.exists():
        return
    try:
        raw = local_settings.read_bytes()
        text = raw.decode("utf-8-sig") if raw[:3] == b"\xef\xbb\xbf" else raw.decode("utf-8")
        data = json.loads(text)
        if data.get("disableAllHooks", False):
            print()
            print("  WARNING: disableAllHooks=true in .claude/settings.local.json")
            print("  All Claude Code hooks are disabled -- Aigis will NOT run.")
            print("  Fix: set disableAllHooks to false, or remove the key.")
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        # Settings file unreadable — silent fail is acceptable for the warning.
        _ = exc


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize Aigis in the current project."""
    from aigis.policy import _default_policy, save_policy

    print("Aigis -Initializing project governance...")

    # Create .aigis directory
    aig_dir = Path(".aigis")
    aig_dir.mkdir(exist_ok=True)
    (aig_dir / "logs").mkdir(exist_ok=True)

    # Generate policy file
    policy_path = Path("aigis-policy.yaml")
    if policy_path.exists():
        print(f"  Policy file already exists: {policy_path}")
    else:
        policy = _default_policy()
        policy.name = f"Aigis {args.policy.title()} Policy"
        save_policy(policy, str(policy_path))
        print(f"  Created policy: {policy_path} ({len(policy.rules)} rules)")

    # Configure Claude Code adapter if requested
    if args.agent == "claude-code":
        from aigis.adapters.claude_code import install_hooks

        install_hooks(".")
        print("  Configured Claude Code hooks")

    # Warn if hooks are disabled
    _warn_if_hooks_disabled(project_dir=".")

    print()
    print("  Done! Aigis is ready.")
    print()
    print("  Next steps:")
    print("    aigis doctor      -Check setup health")
    print("    aigis status      -Check governance status")
    print("    aigis logs        -View activity stream")
    print("    aigis policy show -View active policy")
    print()
    print("  If Aigis helps you ship safer agents, a star keeps the project moving:")
    print("    https://github.com/killertcell428/aigis")
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    """View activity stream."""
    from aigis.activity import ActivityStream

    stream = ActivityStream()

    # Excel export
    if args.export_excel:
        path = stream.export_excel_summary(
            args.export_excel, days=args.days, use_global=args.use_global
        )
        print(f"Exported to {path} and {path.replace('_summary', '_events')}")
        return 0

    # CSV export
    if args.export_csv:
        count = stream.export_csv(args.export_csv, days=args.days, use_global=args.use_global)
        print(f"Exported {count} events to {args.export_csv}")
        return 0

    events = stream.query(
        days=args.days,
        action=args.action,
        agent_type=args.agent_type,
        risk_above=args.risk_above,
        alerts_only=args.alerts,
        use_global=args.use_global,
        limit=args.limit,
    )

    if not events:
        print("No events found.")
        return 0

    if args.json:
        for e in events:
            print(json.dumps(e.to_dict(), ensure_ascii=False, default=str))
        return 0

    # Table format
    print(f"{'Time':>20} {'Action':>15} {'Target':>30} {'Risk':>5} {'Decision':>8}")
    print("-" * 82)
    for e in events:
        time_str = e.timestamp[11:19] if len(e.timestamp) > 19 else e.timestamp
        target = e.target[:30] if e.target else "-"
        decision_icon = {"allow": "  OK", "deny": "BLOCK", "review": " REV"}.get(
            e.policy_decision, "  ?"
        )
        risk_color = e.risk_score
        print(f"{time_str:>20} {e.action:>15} {target:>30} {risk_color:>5} {decision_icon:>8}")

    print(f"\n{len(events)} events shown (last {args.days} days)")
    return 0


def cmd_policy(args: argparse.Namespace) -> int:
    """Policy management."""
    from aigis.policy import _default_policy, load_policy, save_policy

    if args.action == "check":
        policy_path = "aigis-policy.yaml"
        if not Path(policy_path).exists():
            print(f"No policy file found at {policy_path}")
            print("Run 'aigis init' to create one.")
            return 1
        policy = load_policy(policy_path)
        print(f"Policy: {policy.name} (v{policy.version})")
        print(f"Rules: {len(policy.rules)}")
        print(f"Default: {policy.default_decision}")
        deny_count = sum(1 for r in policy.rules if r.decision == "deny")
        review_count = sum(1 for r in policy.rules if r.decision == "review")
        print(f"Deny rules: {deny_count}, Review rules: {review_count}")
        print("Policy is valid.")
        return 0

    elif args.action == "show":
        policy = load_policy("aigis-policy.yaml")
        for rule in policy.rules:
            icon = {"deny": "X", "review": "?", "allow": "O"}.get(rule.decision, " ")
            print(f"  [{icon}] {rule.id}: {rule.action} {rule.target} -> {rule.decision}")
            if rule.reason:
                print(f"      {rule.reason}")
        return 0

    elif args.action == "reset":
        policy = _default_policy()
        save_policy(policy)
        print("Policy reset to defaults.")
        return 0

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show governance status summary."""
    from aigis.activity import ActivityStream
    from aigis.policy import load_policy

    print("Aigis -Governance Status")
    print("=" * 50)

    # Check policy
    policy_path = Path("aigis-policy.yaml")
    if policy_path.exists():
        policy = load_policy(str(policy_path))
        deny = sum(1 for r in policy.rules if r.decision == "deny")
        review = sum(1 for r in policy.rules if r.decision == "review")
        print(f"  Policy: {policy.name} (v{policy.version})")
        print(f"  Rules: {len(policy.rules)} ({deny} deny, {review} review)")
    else:
        print("  Policy: Not configured (run 'aigis init')")

    # Check activity
    stream = ActivityStream()
    summary = stream.summary(days=7)
    print("\n  Activity (last 7 days):")
    print(f"    Total events: {summary['total_events']}")
    print(f"    Blocked: {summary['blocked_count']}")
    if summary["by_agent"]:
        print(f"    Agents: {', '.join(summary['by_agent'].keys())}")

    # Check Claude Code hooks
    claude_hooks = Path(".claude/settings.json")
    if claude_hooks.exists():
        print("\n  Claude Code: Hooks configured")
    else:
        print("\n  Claude Code: Not configured (run 'aigis init --agent claude-code')")

    # Compliance
    try:
        from aigis.compliance import get_compliance_summary

        comp = get_compliance_summary()
        print(
            f"\n  Compliance: {comp['coverage_rate']}% ({comp['covered']}/{comp['total_requirements']} covered)"
        )
    except Exception as exc:
        # Compliance section is optional — module may not be installed.
        print(f"  Compliance: not available ({exc.__class__.__name__})")

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Generate compliance report."""
    # Weekly report subcommand
    if getattr(args, "report_type", None) == "weekly":
        return _cmd_report_weekly(args)

    fmt = args.format

    # Auto-detect format from output file extension
    if args.output:
        ext = Path(args.output).suffix.lower()
        if ext == ".html" and fmt == "text":
            fmt = "html"
        elif ext == ".md" and fmt == "text":
            fmt = "markdown"
        elif ext == ".json" and fmt == "text":
            fmt = "json"

    # Rich report formats (html/markdown/json) use the new MonitoringReport
    if fmt in ("html", "markdown", "json"):
        from aigis.monitor import SecurityMonitor
        from aigis.report import MonitoringReport

        monitor = SecurityMonitor()
        report = MonitoringReport(monitor)

        if args.output:
            report.save(args.output, days=args.days, fmt=fmt)
            print(f"Report saved to {args.output}")
        else:
            if fmt == "html":
                print(report.generate_html(days=args.days))
            elif fmt == "markdown":
                print(report.generate_markdown(days=args.days))
            else:
                data = report.generate_json(days=args.days)
                print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return 0

    # Legacy text report (compliance-focused)
    from aigis.activity import ActivityStream
    from aigis.compliance import get_compliance_summary

    stream = ActivityStream()
    summary = stream.summary(days=args.days)
    compliance = get_compliance_summary()

    report_data = {
        "activity_summary": summary,
        "compliance": compliance,
        "period_days": args.days,
    }

    if fmt == "json":
        print(json.dumps(report_data, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"Aigis Compliance Report ({args.days} days)")
        print("=" * 50)
        print(f"  Total events: {summary['total_events']}")
        print(f"  Blocked: {summary['blocked_count']}")
        print(f"  Compliance: {compliance['coverage_rate']}%")
        print(f"  Regulations covered: {compliance['covered']}/{compliance['total_requirements']}")
        print()
        print("  Tip: Use --format html or --format markdown for rich security reports.")

    return 0


def _cmd_report_weekly(args: argparse.Namespace) -> int:
    """Generate weekly security report."""
    from aigis.weekly_report import WeeklyReportGenerator

    gen = WeeklyReportGenerator()
    report = gen.generate()

    fmt = args.format

    # Auto-detect from output extension
    if args.output:
        ext = Path(args.output).suffix.lower()
        if ext == ".md" and fmt == "text":
            fmt = "markdown"
        elif ext == ".json" and fmt == "text":
            fmt = "json"
        elif ext == ".html" and fmt == "text":
            fmt = "html"

    if fmt == "json":
        output = gen.to_json(report)
    elif fmt == "markdown":
        output = gen.to_markdown(report)
    elif fmt == "html":
        output = gen.to_markdown(report)  # HTML generation can be added later
    else:
        output = gen.to_text(report)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Weekly report saved to {args.output}")
    else:
        print(output)

    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    """Security monitoring dashboard."""
    from aigis.monitor import SecurityMonitor

    monitor = SecurityMonitor()

    # OWASP scorecard mode
    if args.owasp:
        scorecard = monitor.owasp_scorecard()
        if args.json_output:
            print(json.dumps(scorecard, ensure_ascii=False, indent=2))
            return 0

        print("OWASP LLM Top 10 Scorecard")
        print("=" * 75)
        print(f"{'ID':<7} {'Threat':<35} {'Protection':<14} {'Detections':>10}")
        print("-" * 75)
        for oid in sorted(scorecard.keys()):
            sc = scorecard[oid]
            level = sc.get("protection_level", "not-covered").upper().replace("-", " ")
            print(f"{oid:<7} {sc['name']:<35} {level:<14} {sc.get('detections', 0):>10}")
            for feat in sc.get("unique_features", [])[:2]:
                print(f"        + {feat}")
        return 0

    # ASR trend mode
    if args.asr_trend:
        trend = monitor.asr_trend(days=args.days)
        if args.json_output:
            print(json.dumps(trend, ensure_ascii=False, indent=2))
            return 0

        if not trend:
            print("No ASR data available. Run scans first.")
            return 0

        print(f"ASR Trend (last {args.days} days)")
        print("=" * 60)
        print(f"{'Date':<12} {'Attacks':>8} {'Blocked':>8} {'Bypassed':>9} {'ASR':>6}")
        print("-" * 60)
        for t in trend:
            print(
                f"{t['date']:<12} {t['total_attacks']:>8} {t['blocked']:>8} {t['bypassed']:>9} {t['asr']:>5.1%}"
            )
        return 0

    # Default: snapshot
    snap = monitor.snapshot(hours=args.hours)

    if args.json_output:
        print(json.dumps(snap.to_dict(), ensure_ascii=False, indent=2, default=str))
        return 0

    print(f"Aigis Monitor (last {args.hours:.0f}h)")
    print("=" * 50)
    print(f"  Total Scans:    {snap.total_scans:,}")
    print(f"  Blocked:        {snap.total_blocked:,}")
    print(f"  Review:         {snap.total_review:,}")
    print(f"  Detection Rate: {snap.detection_rate:.1%}")
    print(f"  ASR:            {snap.asr:.1%}  (lower = better)")

    if snap.risk_distribution:
        print("\n  Risk: ", end="")
        for level in ("critical", "high", "medium", "low"):
            count = snap.risk_distribution.get(level, 0)
            if count:
                print(f"{level}={count} ", end="")
        print()

    if snap.detection_by_layer:
        print("\n  Detection Layers:")
        for layer, count in snap.detection_by_layer.items():
            print(f"    {layer:<12} {count:,}")

    if snap.learned_patterns_count > 0:
        print(f"\n  Auto-Fix: {snap.learned_patterns_count} learned patterns")

    print("\n  Tip: Use 'aigis report --format html -o report.html' for a full visual report.")
    return 0


def cmd_maintenance(args: argparse.Namespace) -> int:
    """Log maintenance: rotate and compress."""
    from aigis.activity import ActivityStream

    stream = ActivityStream()
    stats = stream.rotate_logs(
        retention_days=args.retention_days,
        compress_after_days=args.compress_after,
    )
    print("Log maintenance complete:")
    print(f"  Compressed: {stats['compressed']} files")
    print(f"  Deleted (>{args.retention_days} days): {stats['deleted']} files")
    if stats["errors"]:
        print(f"  Errors: {stats['errors']}")
    print("\n  Note: Alert logs (~/.aigis/alerts/) are never deleted.")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Diagnose Aigis setup issues."""
    print("Aigis Doctor")
    print("=" * 50)

    passed = 0
    warned = 0
    failed = 0

    def ok(msg: str) -> None:
        nonlocal passed
        print(f"  [OK]   {msg}")
        passed += 1

    def warn(msg: str) -> None:
        nonlocal warned
        print(f"  [WARN] {msg}")
        warned += 1

    def fail(msg: str) -> None:
        nonlocal failed
        print(f"  [FAIL] {msg}")
        failed += 1

    # 1. Policy file
    policy_path = Path("aigis-policy.yaml")
    if policy_path.exists():
        ok(f"Policy file found: {policy_path}")
    else:
        fail("Policy file not found. Run 'aigis init'")

    # 2. .aigis/logs/ directory
    log_dir = Path(".aigis/logs")
    if log_dir.is_dir():
        ok(f"Log directory exists: {log_dir}")
    else:
        fail("Log directory missing: .aigis/logs/")

    # 3. aigis module importable
    try:
        from aigis.activity import ActivityEvent, ActivityStream
        from aigis.policy import evaluate, load_policy

        ok("aigis module imports OK")
    except ImportError as e:
        fail(f"aigis import failed: {e}")

    # 4. Claude Code hook script
    hook_script = Path(".claude/hooks/aig-guard.py")
    if hook_script.exists():
        ok(f"Hook script found: {hook_script}")
    else:
        warn("Hook script not found. Run 'aigis init --agent claude-code'")

    # 5. Claude Code settings.json has hook configured
    settings_path = Path(".claude/settings.json")
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            hooks = settings.get("hooks", {}).get("PreToolUse", [])
            has_aig = any(
                "aig-guard" in h.get("command", "") for m in hooks for h in m.get("hooks", [])
            )
            if has_aig:
                ok("PreToolUse hook configured in settings.json")
            else:
                fail("PreToolUse hook for Aigis not found in settings.json")
        except (json.JSONDecodeError, Exception) as e:
            fail(f"Cannot parse .claude/settings.json: {e}")
    else:
        warn(".claude/settings.json not found")

    # 6. Check disableAllHooks in settings.local.json
    local_settings_path = Path(".claude/settings.local.json")
    if local_settings_path.exists():
        try:
            raw = local_settings_path.read_bytes()
            text = raw.decode("utf-8-sig") if raw[:3] == b"\xef\xbb\xbf" else raw.decode("utf-8")
            local_settings = json.loads(text)
            if local_settings.get("disableAllHooks", False):
                fail(
                    "disableAllHooks=true in settings.local.json -- "
                    "ALL hooks are disabled! "
                    "Set to false or remove the key to enable Aigis."
                )
            else:
                ok("Hooks are enabled (disableAllHooks is not set)")
        except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
            warn(f"Cannot parse settings.local.json: {e}")
    else:
        ok("No settings.local.json overrides")

    # 7. Check for recent log activity
    log_files = sorted(log_dir.glob("*.jsonl")) if log_dir.is_dir() else []
    if log_files:
        latest = log_files[-1]
        with open(latest, encoding="utf-8") as f:
            line_count = sum(1 for _ in f)
        ok(f"Recent logs found: {latest.name} ({line_count} events)")
    else:
        warn("No log files found. If you've used Claude Code recently, the hook may not be firing.")

    # 8. Check global log directory
    global_dir = Path.home() / ".aigis" / "global"
    if global_dir.is_dir():
        global_files = sorted(global_dir.glob("*.jsonl"))
        if global_files:
            ok(f"Global logs: {len(global_files)} file(s)")
        else:
            warn("Global log directory exists but has no log files")
    else:
        warn("Global log directory not found (~/.aigis/global/)")

    # Summary
    print()
    total = passed + warned + failed
    print(f"Results: {passed}/{total} passed", end="")
    if warned:
        print(f", {warned} warnings", end="")
    if failed:
        print(f", {failed} FAILED", end="")
    print()

    if failed:
        print("\nFix the FAIL items above, then run 'aigis doctor' again.")
        return 1
    elif warned:
        print("\nNo critical issues. Review warnings above.")
        return 0
    else:
        print("\nAll checks passed. Aigis is healthy.")
        return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """Quick scan from CLI."""
    from aigis import scan

    # Resolve text source: --file flag > positional text > stdin
    scan_file = getattr(args, "scan_file", None)
    if scan_file:
        file_path = Path(scan_file)
        if not file_path.exists():
            print(f"Error: file not found: {scan_file}", file=sys.stderr)
            return 2
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 2
    else:
        text = args.text
        if not text:
            text = sys.stdin.read()

    result = scan(text)

    if getattr(args, "json_output", False):
        # Machine-readable JSON output (used by VS Code extension and CI tooling)
        output = {
            "risk_score": result.risk_score,
            "risk_level": result.risk_level.upper()
            if hasattr(result.risk_level, "upper")
            else str(result.risk_level).split(".")[-1],
            "blocked": result.is_blocked,
            "is_safe": result.is_safe,
            "reasons": [result.reason] if result.reason else [],
            "matched_rules": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category,
                    "score_delta": r.score_delta,
                    "matched_text": r.matched_text,
                    "owasp_ref": r.owasp_ref,
                    "remediation_hint": r.remediation_hint,
                }
                for r in result.matched_rules
            ],
        }
        print(json.dumps(output, ensure_ascii=False))
        return 0 if result.is_safe else 1

    if result.is_safe:
        print(f"SAFE (score={result.risk_score})")
    else:
        print(
            f"{result.risk_level.upper() if hasattr(result.risk_level, 'upper') else str(result.risk_level).split('.')[-1]} (score={result.risk_score})"
        )
        for rule in result.matched_rules:
            print(f"  {rule.rule_name}: {rule.owasp_ref}")
            if rule.remediation_hint:
                print(f"    Fix: {rule.remediation_hint[:80]}")
    return 0 if result.is_safe else 1


def cmd_redteam(args: argparse.Namespace) -> int:
    """Run automated red team testing."""
    from aigis.redteam import RedTeamReportGenerator, RedTeamSuite

    categories = [args.category] if getattr(args, "category", None) else None
    count = getattr(args, "count", 10)
    seed = getattr(args, "seed", None)

    # HTTP endpoint target
    target_fn = None
    target_url = getattr(args, "target_url", None)
    if target_url:
        from aigis.redteam import make_http_check

        target_fn = make_http_check(target_url)

    suite = RedTeamSuite(
        target_fn=target_fn,
        categories=categories,
        count_per_category=count,
        seed=seed,
    )

    # Run adaptive or standard mode
    if getattr(args, "adaptive", False):
        max_rounds = getattr(args, "rounds", 3)
        result = suite.run_adaptive(max_rounds=max_rounds)
    else:
        result = suite.run()

    # Generate report if requested
    if getattr(args, "report", False):
        report_format = getattr(args, "report_format", "markdown")
        if report_format == "html":
            report_content = RedTeamReportGenerator.generate_html(result)
            default_ext = ".html"
        else:
            report_content = RedTeamReportGenerator.generate_markdown(result)
            default_ext = ".md"

        report_path = getattr(args, "report_path", None) or f"redteam_report{default_ext}"
        Path(report_path).write_text(report_content, encoding="utf-8")
        print(f"Report written to: {report_path}")

    if getattr(args, "json_output", False):
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(result.summary())
    return 0 if result.overall_block_rate >= 90.0 else 1


def cmd_adversarial_loop(args: argparse.Namespace) -> int:
    """Run attack-defend-improve adversarial loop."""
    from aigis.adversarial_loop import AdversarialLoop

    categories = [args.category] if getattr(args, "category", None) else None
    loop = AdversarialLoop(
        max_rounds=getattr(args, "rounds", 3),
        attacks_per_category=getattr(args, "count", 5),
        categories=categories,
        seed=getattr(args, "seed", None),
        evolve=not getattr(args, "no_evolve", False),
    )

    report = loop.run()

    # Save defense proposals if requested
    proposals_path = getattr(args, "proposals", None)
    if proposals_path:
        report.save_proposals(proposals_path)
        print(f"Defense proposals saved to: {proposals_path}")

    # Generate report if requested
    if getattr(args, "report", False):
        fmt = getattr(args, "report_format", "markdown")
        default_ext = ".json" if fmt == "json" else ".md"
        report_path = getattr(args, "report_path", None) or f"adversarial_loop_report{default_ext}"
        report.save_report(report_path, fmt=fmt)
        print(f"Report saved to: {report_path}")

    if getattr(args, "json_output", False):
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print(report.summary())

    # Auto-fix: apply proposals → verify → rollback if needed
    if getattr(args, "auto_fix", False) and report.proposals:
        from aigis.auto_fix import run_auto_fix

        print("\n--- Auto-Fix ---")
        fix_result = run_auto_fix(
            proposals=report.proposals,
            min_priority=getattr(args, "min_priority", "medium"),
            auto_rollback=not getattr(args, "no_rollback", False),
        )
        print(fix_result.summary())

        if fix_result.rolled_back:
            print("\nFalse positives detected — changes rolled back.")
            print("Review proposals manually with --proposals flag.")
        elif fix_result.applied:
            applied_patterns = sum(1 for f in fix_result.applied if f.fix_type == "pattern")
            applied_similarity = sum(1 for f in fix_result.applied if f.fix_type == "similarity")
            print(
                f"\nDefenses strengthened: {applied_patterns} patterns, {applied_similarity} similarity phrases"
            )

    # Exit 1 if any bypasses found (useful for CI)
    return 0 if report.total_bypassed == 0 else 1


def cmd_mcp(args: argparse.Namespace) -> int:
    """Scan MCP tool definitions for security threats."""
    from aigis.scanner import scan_mcp_tool, scan_mcp_tools

    # Resolve input source
    mcp_file = getattr(args, "mcp_file", None)
    if mcp_file:
        file_path = Path(mcp_file)
        if not file_path.exists():
            print(f"Error: file not found: {mcp_file}", file=sys.stderr)
            return 2
        try:
            raw = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 2
    else:
        raw = args.mcp_input
        if not raw:
            raw = sys.stdin.read()

    if not raw or not raw.strip():
        print(
            "Error: no input provided. Pass JSON string, --file, or pipe from stdin.",
            file=sys.stderr,
        )
        return 2

    # Parse JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Treat as raw description text
        data = raw

    # Resolve tools list from input
    if isinstance(data, list):
        tools_list = data
    elif isinstance(data, dict):
        if "tools" in data:
            tools_list = data["tools"]
        else:
            tools_list = [data]
    else:
        tools_list = [{"name": "description", "description": str(data)}]

    # Use enhanced MCP server scanner if --trust or --diff requested
    use_trust = getattr(args, "trust", False)
    use_diff = getattr(args, "diff", False)
    server_url = getattr(args, "server_url", "") or ""

    if use_trust or use_diff:
        from aigis.mcp_scanner import scan_mcp_server

        snapshot_dir = getattr(args, "snapshot_dir", ".aigis/mcp_snapshots")
        report = scan_mcp_server(
            tools_list,
            server_url=server_url,
            snapshot_dir=snapshot_dir if use_diff else None,
        )

        if getattr(args, "json_output", False):
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(report.summary())

        any_unsafe = any(not r.is_safe for r in report.tool_results.values())
        return 1 if any_unsafe else 0

    # Standard per-tool scan (original behavior)
    results = {
        tool.get("name", f"tool_{i}"): scan_mcp_tool(tool) for i, tool in enumerate(tools_list)
    }

    if getattr(args, "json_output", False):
        output = {}
        for name, result in results.items():
            output[name] = {
                "risk_score": result.risk_score,
                "risk_level": result.risk_level.upper()
                if hasattr(result.risk_level, "upper")
                else str(result.risk_level).split(".")[-1],
                "is_safe": result.is_safe,
                "matched_rules": [
                    {
                        "rule_id": r.rule_id,
                        "rule_name": r.rule_name,
                        "category": r.category,
                        "score_delta": r.score_delta,
                        "owasp_ref": r.owasp_ref,
                    }
                    for r in result.matched_rules
                ],
            }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        any_unsafe = any(not r.is_safe for r in results.values())
        return 1 if any_unsafe else 0

    # Human-readable output
    any_unsafe = False
    for name, result in results.items():
        if result.is_safe:
            print(f"  \u2713 {name}: SAFE (score={result.risk_score})")
        else:
            any_unsafe = True
            level = (
                result.risk_level.upper()
                if hasattr(result.risk_level, "upper")
                else str(result.risk_level).split(".")[-1]
            )
            print(f"  \u2717 {name}: {level} (score={result.risk_score})")
            for rule in result.matched_rules:
                print(f"      {rule.rule_name}: {rule.owasp_ref}")
                if rule.remediation_hint:
                    print(f"        Fix: {rule.remediation_hint[:100]}")

    if any_unsafe:
        unsafe_count = sum(1 for r in results.values() if not r.is_safe)
        print(f"\n  {unsafe_count}/{len(results)} tool(s) flagged as unsafe.")
    else:
        print(f"\n  All {len(results)} tool(s) passed security checks.")

    return 1 if any_unsafe else 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Run built-in adversarial benchmark suite."""
    from aigis.benchmark import ATTACK_CORPUS, BenchmarkSuite

    # Latency benchmark mode
    if getattr(args, "latency", False):
        iterations = getattr(args, "iterations", 100)
        suite = BenchmarkSuite()
        latency = suite.run_latency(iterations=iterations)

        if getattr(args, "badge", False):
            print(latency.to_badge_json())
            return 0

        if getattr(args, "report", False):
            report_md = latency.to_markdown_report()
            report_path = getattr(args, "report_path", "benchmark_report.md")
            Path(report_path).write_text(report_md, encoding="utf-8")
            print(f"Latency report written to: {report_path}")
            return 0

        if getattr(args, "json_output", False):
            print(json.dumps(latency.to_dict(), indent=2))
        else:
            print(latency.summary())
        return 0

    categories = [args.category] if getattr(args, "category", None) else None
    threshold = getattr(args, "threshold", 1)
    suite = BenchmarkSuite(threshold=threshold, categories=categories)

    if getattr(args, "json_output", False):
        print(suite.run_json())
        return 0

    # Human-readable output
    result = suite.run()
    print(result.summary())

    if result.false_positive_examples:
        print("\nFalse-positive inputs (safe inputs incorrectly flagged):")
        for ex in result.false_positive_examples[:5]:
            print(f"  - {ex}")

    for cat_result in result.category_results:
        if cat_result.missed_examples:
            print(f"\nMissed {cat_result.category} attacks:")
            for ex in cat_result.missed_examples[:3]:
                print(f"  - {ex}")

    # Exit 0 if overall precision ≥ 90%, else 1
    return 0 if result.overall_precision >= 90.0 else 1


if __name__ == "__main__":
    sys.exit(main())
