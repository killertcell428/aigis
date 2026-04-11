"""Tests for Activity Stream — multi-tier logging, rotation, export."""

import tempfile
from pathlib import Path

from aigis.activity import ActivityEvent, ActivityStream


class TestActivityEvent:
    def test_default_fields(self):
        e = ActivityEvent(action="shell:exec", target="ls")
        assert e.action == "shell:exec"
        assert e.target == "ls"
        assert e.timestamp
        assert e.event_id
        assert e.user_id
        assert e.policy_decision == "allow"

    def test_to_dict(self):
        e = ActivityEvent(action="file:read", target="/etc/passwd")
        d = e.to_dict()
        assert d["action"] == "file:read"
        assert "timestamp" in d

    def test_is_alert_blocked(self):
        e = ActivityEvent(action="shell:exec", target="rm -rf /", policy_decision="deny")
        assert e.is_alert is True

    def test_is_alert_high_risk(self):
        e = ActivityEvent(action="llm:prompt", risk_score=80)
        assert e.is_alert is True

    def test_is_alert_safe(self):
        e = ActivityEvent(action="file:read", target="readme.md")
        assert e.is_alert is False

    def test_agi_fields(self):
        e = ActivityEvent(
            action="agent:spawn",
            target="sub_agent_1",
            autonomy_level=3,
            delegation_chain=["a", "b"],
            estimated_cost=0.05,
            memory_scope="department:sales",
        )
        assert e.autonomy_level == 3
        assert e.estimated_cost == 0.05

    def test_auto_fix_fields(self):
        e = ActivityEvent(
            action="shell:exec",
            target="rm -rf /",
            suggested_fix="rm -rf /tmp/test_only",
            fix_applied=False,
        )
        assert e.suggested_fix == "rm -rf /tmp/test_only"
        assert e.fix_applied is False

    def test_project_name_auto(self):
        e = ActivityEvent(action="file:read", cwd="/home/user/my-project")
        assert e.project_name == "my-project"


class TestActivityStreamLocal:
    def test_record_and_query(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream.record(ActivityEvent(action="shell:exec", target="ls"))
            events = stream.query(days=1)
            assert len(events) == 1
            assert events[0].action == "shell:exec"

    def test_query_filter_action(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream.record(ActivityEvent(action="shell:exec", target="ls"))
            stream.record(ActivityEvent(action="file:read", target="f.py"))
            stream.record(ActivityEvent(action="shell:exec", target="pwd"))
            events = stream.query(days=1, action="shell:exec")
            assert len(events) == 2

    def test_query_filter_risk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream.record(ActivityEvent(action="shell:exec", risk_score=0))
            stream.record(ActivityEvent(action="shell:exec", risk_score=90))
            events = stream.query(days=1, risk_above=50)
            assert len(events) == 1
            assert events[0].risk_score == 90

    def test_empty_stream(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            assert stream.query(days=1) == []
            assert stream.summary(days=1)["total_events"] == 0


class TestActivityStreamGlobal:
    def test_global_aggregation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            global_dir = Path(tmpdir) / "global"
            stream = ActivityStream(
                log_dir=str(Path(tmpdir) / "local"),
                enable_global=True,
                enable_alerts=False,
            )
            stream.global_dir = global_dir
            stream.global_dir.mkdir(parents=True, exist_ok=True)

            stream.record(ActivityEvent(action="shell:exec", target="ls", project_name="proj-a"))
            stream.record(ActivityEvent(action="file:read", target="f.py", project_name="proj-b"))

            # Local has both
            local_events = stream.query(days=1)
            assert len(local_events) == 2

            # Global also has both (cross-project view)
            global_events = stream.query(days=1, use_global=True)
            assert len(global_events) == 2


class TestActivityStreamAlerts:
    def test_alert_archive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            alert_dir = Path(tmpdir) / "alerts"
            stream = ActivityStream(
                log_dir=str(Path(tmpdir) / "local"),
                enable_global=False,
                enable_alerts=True,
            )
            stream.alert_dir = alert_dir
            stream.alert_dir.mkdir(parents=True, exist_ok=True)

            # Safe event — not in alerts
            stream.record(ActivityEvent(action="file:read", target="readme.md"))
            # Blocked event — in alerts
            stream.record(
                ActivityEvent(
                    action="shell:exec", target="rm -rf /", policy_decision="deny", risk_score=90
                )
            )

            alerts = stream.query(days=1, alerts_only=True)
            assert len(alerts) == 1
            assert alerts[0].policy_decision == "deny"

    def test_alert_knowledge_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            alert_dir = Path(tmpdir) / "alerts"
            stream = ActivityStream(
                log_dir=str(Path(tmpdir) / "local"),
                enable_global=False,
                enable_alerts=True,
            )
            stream.alert_dir = alert_dir
            stream.alert_dir.mkdir(parents=True, exist_ok=True)

            stream.record(
                ActivityEvent(
                    action="shell:exec",
                    target="rm -rf /",
                    policy_decision="deny",
                    risk_score=90,
                    matched_rules=["dangerous_commands"],
                    remediation_hints=["Use targeted deletion instead"],
                    owasp_refs=["CWE-78"],
                )
            )

            knowledge = stream.get_alert_knowledge()
            assert len(knowledge) == 1
            assert knowledge[0]["matched_rules"] == ["dangerous_commands"]
            assert "targeted deletion" in knowledge[0]["remediation_hints"][0]


class TestActivityStreamExport:
    def test_export_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream.record(ActivityEvent(action="shell:exec", target="ls"))
            stream.record(ActivityEvent(action="file:read", target="f.py"))

            csv_path = str(Path(tmpdir) / "export.csv")
            count = stream.export_csv(csv_path, days=1)
            assert count == 2
            content = Path(csv_path).read_text(encoding="utf-8-sig")
            assert "shell:exec" in content
            assert "file:read" in content

    def test_export_excel_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream.record(ActivityEvent(action="shell:exec", target="ls", agent_type="claude_code"))
            stream.record(
                ActivityEvent(action="shell:exec", target="rm -rf /", policy_decision="deny")
            )

            out = str(Path(tmpdir) / "report.csv")
            summary_path = stream.export_excel_summary(out, days=1)
            assert Path(summary_path).exists()
            events_path = summary_path.replace("_summary", "_events")
            assert Path(events_path).exists()

            summary_text = Path(summary_path).read_text(encoding="utf-8-sig")
            assert "Aigis Activity Report" in summary_text
            assert "Blocked" in summary_text

    def test_export_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream.record(ActivityEvent(action="shell:exec", target="ls"))

            export_path = str(Path(tmpdir) / "export.jsonl")
            count = stream.export_jsonl(export_path, days=1)
            assert count == 1


class TestActivityStreamSummary:
    def test_summary_with_projects_and_users(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream = ActivityStream(log_dir=tmpdir, enable_global=False, enable_alerts=False)
            stream.record(
                ActivityEvent(
                    action="shell:exec", target="ls", user_id="alice", project_name="proj-a"
                )
            )
            stream.record(
                ActivityEvent(
                    action="file:read", target="f.py", user_id="bob", project_name="proj-b"
                )
            )
            stream.record(
                ActivityEvent(
                    action="shell:exec",
                    target="rm",
                    user_id="alice",
                    project_name="proj-a",
                    policy_decision="deny",
                )
            )

            summary = stream.summary(days=1)
            assert summary["total_events"] == 3
            assert summary["by_user"]["alice"] == 2
            assert summary["by_user"]["bob"] == 1
            assert summary["by_project"]["proj-a"] == 2
            assert summary["blocked_count"] == 1
            assert len(summary["top_blocked_targets"]) >= 1
