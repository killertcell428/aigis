"""Tests for aigis.trust_pack and the trust-pack / audit CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from aigis.cli import main
from aigis.policy import Policy, PolicyRule, _default_policy, save_policy
from aigis.trust_pack import (
    TrustPackGenerator,
    control_matrix,
    gather_evidence,
)

# Markdown stems (excluding README) that must exist for each language.
EXPECTED_STEMS = [
    "01_executive_summary",
    "02_control_matrix",
    "03_policy_snapshot",
    "04_audit_log_evidence",
    "05_incident_runbook",
    "06_rollout_plan",
]


# ---------------------------------------------------------------------------
# Evidence gathering
# ---------------------------------------------------------------------------


class TestGatherEvidence:
    def test_fresh_dir_no_crash(self, tmp_path: Path) -> None:
        ev = gather_evidence(str(tmp_path))
        assert ev.aigis_version
        assert ev.generated_at
        # No policy file -> documents the built-in default.
        assert ev.policy_exists is False
        assert ev.total_rules > 0  # default policy has rules
        assert ev.settings_hook_configured is False
        assert ev.local_log_present is False
        assert ev.events_last_7d == 0

    def test_detects_custom_policy(self, tmp_path: Path) -> None:
        policy = Policy(
            name="Custom Test Policy",
            rules=[PolicyRule(id="r1", action="shell:exec", target="*", decision="deny")],
        )
        save_policy(policy, str(tmp_path / "aigis-policy.yaml"))
        ev = gather_evidence(str(tmp_path))
        assert ev.policy_exists is True
        assert ev.policy_name == "Custom Test Policy"
        assert ev.policy_mtime is not None
        assert ev.deny_rules == 1

    def test_detects_hook_and_logs(self, tmp_path: Path) -> None:
        # Configure a fake Claude Code hook in settings.json
        settings = tmp_path / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {"hooks": [{"command": 'python ".claude/hooks/aig-guard.py"'}]}
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        # Create a minimal JSONL log fixture with a recent timestamp
        from datetime import UTC, datetime

        logs = tmp_path / ".aigis" / "logs"
        logs.mkdir(parents=True)
        now = datetime.now(UTC).isoformat()
        (logs / "activity.jsonl").write_text(
            json.dumps({"action": "shell:exec", "target": "ls", "timestamp": now}) + "\n",
            encoding="utf-8",
        )
        ev = gather_evidence(str(tmp_path))
        assert ev.settings_hook_configured is True
        assert ev.local_log_present is True
        assert ev.events_last_7d == 1
        assert ev.events_last_30d == 1


# ---------------------------------------------------------------------------
# Control matrix
# ---------------------------------------------------------------------------


class TestControlMatrix:
    def test_has_expected_controls(self) -> None:
        rows = control_matrix()
        assert len(rows) >= 7
        names = " ".join(r.control for r in rows)
        assert "Input scanning" in names
        assert "audit log" in names.lower()
        assert "SIEM" in names

    def test_iso_phrased_as_evidence_not_guarantee(self) -> None:
        # Every row must cite an ISO/IEC 27001 Annex A item.
        for r in control_matrix():
            assert "A." in r.iso27001


# ---------------------------------------------------------------------------
# Markdown pack generation
# ---------------------------------------------------------------------------


class TestMarkdownGeneration:
    def test_both_langs_all_files_created(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        written = gen.write_markdown(out, lang="both")
        names = {p.name for p in written}
        assert "README.md" in names
        for stem in EXPECTED_STEMS:
            assert f"{stem}.md" in names
            assert f"{stem}.ja.md" in names
        # 1 README + 6 stems * 2 langs = 13
        assert len(written) == 13
        for p in written:
            assert p.exists()

    def test_readme_lists_all_files(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="both")
        readme = (out / "README.md").read_text(encoding="utf-8")
        for stem in EXPECTED_STEMS:
            assert f"{stem}.md" in readme
            assert f"{stem}.ja.md" in readme

    def test_lang_en_produces_only_english(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        written = gen.write_markdown(out, lang="en")
        names = {p.name for p in written}
        assert "README.md" in names
        for stem in EXPECTED_STEMS:
            assert f"{stem}.md" in names
            assert f"{stem}.ja.md" not in names
        # 1 README + 6 EN files = 7
        assert len(written) == 7

    def test_lang_ja_produces_only_japanese(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        written = gen.write_markdown(out, lang="ja")
        names = {p.name for p in written}
        for stem in EXPECTED_STEMS:
            assert f"{stem}.ja.md" in names
            assert f"{stem}.md" not in names
        assert len(written) == 7

    def test_to_fill_markers_when_org_omitted(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))  # no org/contact
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="both")
        readme = (out / "README.md").read_text(encoding="utf-8")
        assert "[TO FILL:" in readme
        # Japanese template field marker appears in the JA executive summary.
        exec_ja = (out / "01_executive_summary.ja.md").read_text(encoding="utf-8")
        assert "【要記入:" in exec_ja

    def test_org_contact_substituted_when_given(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(
            project_dir=str(tmp_path),
            org="Acme Inc.",
            contact="sec@acme.example",
        )
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="both")
        readme = (out / "README.md").read_text(encoding="utf-8")
        assert "Acme Inc." in readme
        assert "sec@acme.example" in readme
        exec_en = (out / "01_executive_summary.md").read_text(encoding="utf-8")
        assert "Acme Inc." in exec_en

    def test_policy_snapshot_contains_custom_rule(self, tmp_path: Path) -> None:
        policy = Policy(
            name="Snapshot Test Policy",
            rules=[
                PolicyRule(
                    id="forbid_curl_pipe",
                    action="shell:exec",
                    target="*curl*| bash*",
                    decision="deny",
                    reason="No remote pipe to bash",
                )
            ],
        )
        save_policy(policy, str(tmp_path / "aigis-policy.yaml"))
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="en")
        snapshot = (out / "03_policy_snapshot.md").read_text(encoding="utf-8")
        # Both the human-readable table and the literal YAML must show the rule.
        assert "forbid_curl_pipe" in snapshot
        assert "No remote pipe to bash" in snapshot
        assert "Snapshot Test Policy" in snapshot

    def test_not_covered_section_present(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="both")
        cm_en = (out / "02_control_matrix.md").read_text(encoding="utf-8")
        cm_ja = (out / "02_control_matrix.ja.md").read_text(encoding="utf-8")
        assert "does NOT cover" in cm_en
        assert "対象としない範囲" in cm_ja

    def test_ja_policy_snapshot_translates_default_rule_reasons(self, tmp_path: Path) -> None:
        # The default policy's rule reasons are English string literals
        # (aigis.policy.default_policy). The ja snapshot's human-readable
        # table must not leak them untranslated. Materialise the policy
        # file first, otherwise the YAML section is just a placeholder
        # comment and this wouldn't be exercising the literal-file case.
        save_policy(_default_policy(), str(tmp_path / "aigis-policy.yaml"))
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="ja")
        snapshot = (out / "03_policy_snapshot.ja.md").read_text(encoding="utf-8")
        table, _, yaml_block = snapshot.partition("## ポリシーファイル")
        assert "Recursive forced deletion is blocked" not in table
        assert "再帰的な強制削除をブロックします" in table
        # The literal YAML is the actual file under version control and is
        # never translated — this is the one place the English reason
        # should still appear.
        assert "Recursive forced deletion is blocked" in yaml_block

    def test_ja_policy_snapshot_falls_back_for_custom_rule_reason(self, tmp_path: Path) -> None:
        # A rule id Aigis doesn't ship (i.e. user-authored) has no Japanese
        # translation available; its own reason must pass through as-is
        # rather than disappearing or raising.
        policy = Policy(
            name="Custom Test Policy",
            rules=[
                PolicyRule(
                    id="forbid_curl_pipe",
                    action="shell:exec",
                    target="*curl*| bash*",
                    decision="deny",
                    reason="No remote pipe to bash",
                )
            ],
        )
        save_policy(policy, str(tmp_path / "aigis-policy.yaml"))
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="ja")
        snapshot = (out / "03_policy_snapshot.ja.md").read_text(encoding="utf-8")
        assert "No remote pipe to bash" in snapshot

    def test_ja_siem_status_has_no_untranslated_english(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="ja")
        for stem in ("01_executive_summary", "04_audit_log_evidence"):
            text = (out / f"{stem}.ja.md").read_text(encoding="utf-8")
            assert "not detected (forwarders are configured in code" not in text
            assert "未検出" in text

    def test_ja_control_matrix_has_no_english_owasp_note(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        gen.write_markdown(out, lang="ja")
        cm_ja = (out / "02_control_matrix.ja.md").read_text(encoding="utf-8")
        assert "cross-cutting; not an OWASP risk category" not in cm_ja

    def test_no_crash_with_logs_present(self, tmp_path: Path) -> None:
        from datetime import UTC, datetime

        logs = tmp_path / ".aigis" / "logs"
        logs.mkdir(parents=True)
        now = datetime.now(UTC).isoformat()
        (logs / "activity.jsonl").write_text(
            json.dumps({"action": "file:read", "target": "x", "timestamp": now})
            + "\n"
            + "this is not json\n",  # malformed line must be skipped, not crash
            encoding="utf-8",
        )
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        written = gen.write_markdown(out, lang="both")
        assert len(written) == 13
        audit_doc = (out / "04_audit_log_evidence.md").read_text(encoding="utf-8")
        # The audit evidence doc lists the ActivityEvent schema fields.
        assert "risk_score" in audit_doc


# ---------------------------------------------------------------------------
# HTML pack generation
# ---------------------------------------------------------------------------


class TestHtmlGeneration:
    def test_single_file_with_html_and_japanese(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        path = gen.write_html(out, lang="both")
        assert path.name == "aigis-trust-pack.html"
        # Only one HTML file in the directory.
        assert list(out.glob("*.html")) == [path]
        html = path.read_text(encoding="utf-8")
        assert "<html" in html
        assert "情報システム部門" in html  # Japanese text present
        # A control-matrix table should be rendered to HTML.
        assert "<table>" in html
        # No external resources (CDN/JS) — self-contained.
        assert "<script" not in html
        assert "http://" not in html
        assert "https://cdn" not in html

    def test_html_en_only_has_no_japanese_body(self, tmp_path: Path) -> None:
        gen = TrustPackGenerator(project_dir=str(tmp_path))
        out = tmp_path / "pack"
        path = gen.write_html(out, lang="en")
        html = path.read_text(encoding="utf-8")
        assert "<html" in html
        # The bilingual title still has Japanese, but the executive-summary
        # body heading "エグゼクティブサマリ" should not appear in EN-only mode.
        assert "エグゼクティブサマリ" not in html


# ---------------------------------------------------------------------------
# CLI: trust-pack
# ---------------------------------------------------------------------------


class TestTrustPackCli:
    def test_cli_markdown_default(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        rc = main(["trust-pack", "-o", "pack"])
        assert rc == 0
        out = tmp_path / "pack"
        assert (out / "README.md").exists()
        assert (out / "01_executive_summary.ja.md").exists()

    def test_cli_html(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        rc = main(["trust-pack", "-o", "pack", "--format", "html"])
        assert rc == 0
        assert (tmp_path / "pack" / "aigis-trust-pack.html").exists()

    def test_cli_lang_en(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        rc = main(["trust-pack", "-o", "pack", "--lang", "en"])
        assert rc == 0
        out = tmp_path / "pack"
        assert (out / "01_executive_summary.md").exists()
        assert not (out / "01_executive_summary.ja.md").exists()


# ---------------------------------------------------------------------------
# CLI: audit verify / status
# ---------------------------------------------------------------------------


def _make_signed_log(directory: Path) -> Path:
    """Create a signed audit log under ``directory/.aigis/`` and return its path."""
    from aigis.audit import SignedAuditLog

    log = SignedAuditLog(secret_key=None)  # auto-generates .aigis/audit_key
    log.append(event_type="tool_call", actor="agent", action="shell:exec", target="ls")
    log.append(event_type="tool_call", actor="agent", action="file:write", target="a.txt")
    log_path = directory / ".aigis" / "audit.jsonl"
    log.save(str(log_path))
    return log_path


class TestAuditCli:
    def test_verify_happy_path(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        _make_signed_log(tmp_path)
        rc = main(["audit", "verify"])
        assert rc == 0

    def test_verify_json_output(self, tmp_path: Path, monkeypatch, capsys) -> None:
        monkeypatch.chdir(tmp_path)
        _make_signed_log(tmp_path)
        rc = main(["audit", "verify", "--json"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["valid"] is True
        assert data["total_entries"] == 2

    def test_verify_tamper_path(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        log_path = _make_signed_log(tmp_path)
        # Flip a byte: mutate the action of the first entry.
        text = log_path.read_text(encoding="utf-8")
        tampered = text.replace("shell:exec", "shell:EXEC", 1)
        assert tampered != text
        log_path.write_text(tampered, encoding="utf-8")
        rc = main(["audit", "verify"])
        assert rc == 1

    def test_verify_missing_log(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        rc = main(["audit", "verify"])
        assert rc == 1

    def test_status(self, tmp_path: Path, monkeypatch, capsys) -> None:
        monkeypatch.chdir(tmp_path)
        _make_signed_log(tmp_path)
        rc = main(["audit", "status"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Entries: 2" in out

    def test_status_json(self, tmp_path: Path, monkeypatch, capsys) -> None:
        monkeypatch.chdir(tmp_path)
        _make_signed_log(tmp_path)
        rc = main(["audit", "status", "--json"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["key_present"] is True
        assert data["log_present"] is True
        assert data["entry_count"] == 2
