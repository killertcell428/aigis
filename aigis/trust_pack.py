"""Trust Pack generator — IT/security adoption-approval documents.

Generates the "adoption approval pack" (導入承認パック) that a corporate
IT / information-security department (情報システム部門) reviews before
approving Claude Code or another autonomous AI agent for company use.

Every document is generated from the **live local configuration** — the
active policy, installed hooks, and on-disk audit/activity logs — never
from fabricated claims. Items that are inherently organisation-specific
(data classification rules, approver names, escalation contacts) are
emitted as explicit ``[TO FILL: ...]`` / ``【要記入: ...】`` template
fields rather than guessed.

Usage::

    from aigis.trust_pack import TrustPackGenerator

    gen = TrustPackGenerator(org="Acme Inc.", contact="security@acme.example")
    paths = gen.write_markdown(Path("./aigis-trust-pack"), lang="both")

Or via the CLI::

    aigis trust-pack -o ./aigis-trust-pack --lang both --format markdown

The pack is intentionally honest about scope: a "What Aigis does NOT
cover" section is always included, and compliance mappings are phrased
as "supports evidence for" — Aigis never *certifies* or *guarantees*
compliance with any framework.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aigis.activity import ActivityEvent
from aigis.policy import Policy, load_policy, save_policy

# ---------------------------------------------------------------------------
# Version helper (mirrors aigis/report.py style)
# ---------------------------------------------------------------------------


def _get_version() -> str:
    try:
        from aigis import __version__

        return __version__
    except ImportError:
        return "unknown"


# ---------------------------------------------------------------------------
# Control matrix — Aigis controls mapped to external frameworks
# ---------------------------------------------------------------------------
#
# Each control maps an Aigis capability to the relevant clause/function in
# four frameworks. ISO/IEC 27001:2022 Annex A items are phrased throughout
# as "supports evidence for" — Aigis is a control *implementation*, not a
# certification body, and these documents are submitted as supporting
# evidence during an internal review, not as a compliance guarantee.


@dataclass(frozen=True)
class ControlMapping:
    """A single Aigis control mapped to external security frameworks."""

    control: str
    """Aigis control name (English)."""

    control_ja: str
    """Aigis control name (Japanese)."""

    what_it_does: str
    """One-line description (English)."""

    what_it_does_ja: str
    """One-line description (Japanese)."""

    iso27001: str
    """ISO/IEC 27001:2022 Annex A item numbers (supporting evidence)."""

    nist_ai_rmf: str
    """NIST AI RMF function (GOVERN / MAP / MEASURE / MANAGE)."""

    owasp_llm: str
    """OWASP LLM Top 10 (2025) identifiers."""

    ai_gl: str
    """経済産業省・総務省 AI事業者ガイドライン v1.2 reference."""


def control_matrix() -> list[ControlMapping]:
    """Static mapping of Aigis controls to external frameworks.

    Phrased as supporting evidence, never as a compliance certification.
    """
    return [
        ControlMapping(
            control="Input scanning (prompt-injection / jailbreak / PII)",
            control_ja="入力スキャン（プロンプトインジェクション・ジェイルブレイク・個人情報）",
            what_it_does="Deterministic regex + similarity detection on every prompt before it reaches the model.",
            what_it_does_ja="モデルに到達する前に、すべてのプロンプトを正規表現と類似度検知で決定論的に検査します。",
            iso27001="A.8.16 (Monitoring activities), A.5.7 (Threat intelligence)",
            nist_ai_rmf="MEASURE 2.7, MANAGE 2.1",
            owasp_llm="LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure",
            ai_gl="GL-POISON-01, SEC-PI-01",
        ),
        ControlMapping(
            control="Output scanning (data leak / secret / PII)",
            control_ja="出力スキャン（情報漏洩・秘密情報・個人情報）",
            what_it_does="Scans model output for leaked secrets, PII, and system-prompt disclosure before it is returned.",
            what_it_does_ja="モデルの出力を返す前に、秘密情報・個人情報・システムプロンプトの漏洩がないか検査します。",
            iso27001="A.8.12 (Data leakage prevention), A.5.34 (Privacy and PII)",
            nist_ai_rmf="MEASURE 2.7, MANAGE 4.1",
            owasp_llm="LLM02 Sensitive Information Disclosure, LLM06 Excessive Agency",
            ai_gl="APPI-PII-01, GL-DATA-01",
        ),
        ControlMapping(
            control="Tool-call policy enforcement",
            control_ja="ツール呼び出しポリシー強制",
            what_it_does="Deterministic allow/deny/review decision on every tool call (shell, file, network) before execution.",
            what_it_does_ja="すべてのツール呼び出し（シェル・ファイル・ネットワーク）を実行前に許可/拒否/レビュー判定します。",
            iso27001="A.8.2 (Privileged access rights), A.8.18 (Use of privileged utility programs)",
            nist_ai_rmf="GOVERN 1.1, MANAGE 2.1",
            owasp_llm="LLM06 Excessive Agency, LLM08 Vector and Embedding Weaknesses",
            ai_gl="GL-HUMAN-03 (最小権限), SEC-PRIV-01",
        ),
        ControlMapping(
            control="MCP tool-definition scanning",
            control_ja="MCPツール定義スキャン",
            what_it_does="Detects tool-poisoning and rug-pull changes in Model Context Protocol server definitions.",
            what_it_does_ja="Model Context Protocolサーバー定義に含まれるツールポイズニングや定義改ざん（ラグプル）を検出します。",
            iso27001="A.5.21 (ICT supply chain security), A.8.30 (Outsourced development)",
            nist_ai_rmf="MAP 4.1, MANAGE 3.1",
            owasp_llm="LLM03 Supply Chain, LLM01 Prompt Injection",
            ai_gl="GL-SEC-03 (攻撃対象面の管理)",
        ),
        ControlMapping(
            control="Memory / file-write filter",
            control_ja="メモリ・ファイル書き込みフィルター",
            what_it_does="Blocks writes to protected paths (.env, credentials, SSH keys) and filters persisted agent memory.",
            what_it_does_ja="保護対象パス（.env、認証情報、SSH鍵）への書き込みをブロックし、永続化されるエージェントメモリを検査します。",
            iso27001="A.8.3 (Information access restriction), A.8.12 (Data leakage prevention)",
            nist_ai_rmf="MANAGE 2.1, GOVERN 1.4",
            owasp_llm="LLM06 Excessive Agency, LLM02 Sensitive Information Disclosure",
            ai_gl="GL-HUMAN-03 (最小権限), GL-DATA-02",
        ),
        ControlMapping(
            control="Tamper-evident audit log (HMAC + hash chain)",
            control_ja="改ざん検知監査ログ（HMAC＋ハッシュチェーン）",
            what_it_does="Append-only log; each entry HMAC-SHA256 signed and hash-chained so deletion/modification is detectable.",
            what_it_does_ja="追記専用ログ。各エントリをHMAC-SHA256で署名しハッシュチェーンで連結するため、削除・改ざんを検知できます。",
            iso27001="A.8.15 (Logging), A.8.16 (Monitoring activities), A.5.28 (Collection of evidence)",
            nist_ai_rmf="MEASURE 2.8, MANAGE 4.1",
            owasp_llm="LLM09 Misinformation (audit trail), LLM06 Excessive Agency",
            ai_gl="GL-AUDIT-01 (追跡可能性), GL-RISK-02 (インシデントDB)",
        ),
        ControlMapping(
            control="SIEM forwarding (ECS / HTTP)",
            control_ja="SIEM転送（ECS／HTTP）",
            what_it_does="Optional non-blocking forwarder mirrors events to a SIEM in Elastic Common Schema; PII redaction runs first.",
            what_it_does_ja="任意の非ブロッキング転送機能が、イベントをElastic Common Schema形式でSIEMへ複製します。送信前に個人情報の墨消しを実施します。",
            iso27001="A.8.16 (Monitoring activities), A.5.25 (Assessment of security events)",
            nist_ai_rmf="MEASURE 2.8, MANAGE 4.1",
            owasp_llm="LLM06 Excessive Agency",
            ai_gl="GL-HUMAN-04 (継続的モニタリング)",
        ),
        ControlMapping(
            control="Weekly security report",
            control_ja="週次セキュリティレポート",
            what_it_does="Automated weekly report of scans, blocks, OWASP coverage, and week-over-week trend for review meetings.",
            what_it_does_ja="スキャン数・ブロック数・OWASPカバレッジ・前週比トレンドを集計した週次レポートを自動生成します。",
            iso27001="A.5.36 (Compliance review), A.8.16 (Monitoring activities)",
            nist_ai_rmf="MEASURE 4.1, GOVERN 4.1",
            owasp_llm="LLM09 Misinformation (reporting)",
            ai_gl="GL-TRANS-01 (ドキュメント化), GL-RISK-02",
        ),
    ]


# Honest scope boundary — what Aigis explicitly does NOT do.
_NOT_COVERED_EN = [
    "Model training / fine-tuning safety — Aigis does not train or align models.",
    "Content moderation policy decisions — Aigis flags categories but does not define your acceptable-use policy.",
    "Network-layer DLP — egress filtering at the network boundary is your existing CASB/proxy's job.",
    "Endpoint security (EDR/antivirus) — Aigis governs the agent, not the host machine.",
    "Claude Code's own cloud-side processing — prompts sent to Anthropic are governed by Anthropic's terms, not by Aigis.",
    "Identity and access management — user authentication and SSO remain your IdP's responsibility.",
]

_NOT_COVERED_JA = [
    "モデルの学習・ファインチューニングの安全性 — Aigisはモデルの学習やアライメントを行いません。",
    "コンテンツモデレーションのポリシー判断 — Aigisはカテゴリを検知しますが、貴社の利用規約（許容利用方針）の定義は行いません。",
    "ネットワーク層のDLP — ネットワーク境界での外向き通信フィルタリングは、既存のCASB／プロキシの役割です。",
    "エンドポイントセキュリティ（EDR／アンチウイルス） — Aigisはエージェントを統制しますが、ホスト端末自体は対象外です。",
    "Claude Code自体のクラウド側処理 — Anthropicへ送信されるプロンプトはAnthropicの規約に従うものであり、Aigisの統制対象外です。",
    "ID・アクセス管理 — ユーザー認証やSSOは引き続き貴社のIdP（ID基盤）の責任範囲です。",
]


# ---------------------------------------------------------------------------
# Evidence gathering — doctor-style live checks
# ---------------------------------------------------------------------------


@dataclass
class Evidence:
    """Live environment evidence gathered from the local configuration."""

    aigis_version: str
    generated_at: str  # ISO-8601 UTC

    # Policy
    policy_path: str | None
    policy_exists: bool
    policy_mtime: str | None
    policy_name: str
    policy_version: str
    default_decision: str
    allow_rules: int
    deny_rules: int
    review_rules: int
    total_rules: int

    # Hooks (Claude Code)
    hook_script_present: bool
    hook_script_path: str
    settings_hook_configured: bool
    settings_path: str
    hooks_disabled: bool

    # Logs / audit
    local_log_dir: str
    local_log_present: bool
    events_last_7d: int
    events_last_30d: int
    signed_audit_enabled: bool
    signed_audit_key_path: str
    signed_audit_log_path: str | None
    siem_forwarder_configured: bool
    siem_forwarder_detail: str

    # Convenience
    notes: list[str] = field(default_factory=list)


def _iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()


def _count_recent_events(log_dir: Path, days: int) -> int:
    """Best-effort count of JSONL events newer than ``days`` ago.

    Reads every ``*.jsonl`` file in ``log_dir`` and counts entries whose
    ``timestamp`` field parses to within the window. Lines that cannot be
    parsed are skipped silently — this is evidence-gathering, not
    validation.
    """
    if not log_dir.is_dir():
        return 0
    cutoff = datetime.now(UTC).timestamp() - days * 86400
    count = 0
    for jsonl in sorted(log_dir.glob("*.jsonl")):
        try:
            with open(jsonl, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = rec.get("timestamp", "")
                    if not ts:
                        continue
                    try:
                        when = datetime.fromisoformat(ts)
                    except ValueError:
                        continue
                    if when.tzinfo is None:
                        when = when.replace(tzinfo=UTC)
                    if when.timestamp() >= cutoff:
                        count += 1
        except OSError:
            continue
    return count


def _detect_siem_forwarder(project_dir: Path) -> tuple[bool, str]:
    """Best-effort detection of a configured SIEM forwarder.

    Forwarders in Aigis are wired programmatically (no canonical config
    file), so this is a heuristic: we look for the conventional
    environment variable and a project-level marker file. When neither is
    present we report "not detected" rather than guessing.
    """
    import os

    env_url = os.environ.get("AIGIS_SIEM_URL", "").strip()
    if env_url:
        return True, f"AIGIS_SIEM_URL is set ({env_url})"

    marker = project_dir / ".aigis" / "forwarders.json"
    if marker.exists():
        return True, f"forwarder config present: {marker}"

    return False, "not detected (forwarders are configured in code; see docs/forwarders.md)"


def gather_evidence(project_dir: str = ".") -> Evidence:
    """Gather live environment evidence from the local configuration.

    Mirrors the checks performed by ``aigis doctor`` but returns structured
    data instead of printing. Safe to call in a fresh directory with no
    ``.aigis/`` — all checks degrade gracefully to "absent".
    """
    project = Path(project_dir)

    # --- Policy ---
    policy_path = project / "aigis-policy.yaml"
    policy_exists = policy_path.exists()
    if policy_exists:
        policy = load_policy(str(policy_path))
        policy_mtime: str | None = _iso_mtime(policy_path)
        policy_path_str: str | None = str(policy_path)
    else:
        from aigis.policy import _default_policy

        policy = _default_policy()
        policy_mtime = None
        policy_path_str = None

    allow_rules = sum(1 for r in policy.rules if r.decision == "allow")
    deny_rules = sum(1 for r in policy.rules if r.decision == "deny")
    review_rules = sum(1 for r in policy.rules if r.decision == "review")

    # --- Hooks ---
    hook_script = project / ".claude" / "hooks" / "aig-guard.py"
    settings_path = project / ".claude" / "settings.json"
    settings_hook_configured = False
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            hooks = settings.get("hooks", {}).get("PreToolUse", [])
            settings_hook_configured = any(
                "aig-guard" in h.get("command", "") for m in hooks for h in m.get("hooks", [])
            )
        except (json.JSONDecodeError, OSError):
            settings_hook_configured = False

    hooks_disabled = False
    local_settings = project / ".claude" / "settings.local.json"
    if local_settings.exists():
        try:
            raw = local_settings.read_bytes()
            text = raw.decode("utf-8-sig") if raw[:3] == b"\xef\xbb\xbf" else raw.decode("utf-8")
            hooks_disabled = bool(json.loads(text).get("disableAllHooks", False))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            hooks_disabled = False

    # --- Logs ---
    local_log_dir = project / ".aigis" / "logs"
    local_log_present = local_log_dir.is_dir() and any(local_log_dir.glob("*.jsonl"))
    events_7d = _count_recent_events(local_log_dir, 7)
    events_30d = _count_recent_events(local_log_dir, 30)

    # --- Signed audit ---
    audit_key = project / ".aigis" / "audit_key"
    signed_audit_enabled = audit_key.exists()
    audit_log = project / ".aigis" / "audit.jsonl"
    signed_audit_log_path = str(audit_log) if audit_log.exists() else None

    # --- SIEM forwarder ---
    siem_on, siem_detail = _detect_siem_forwarder(project)

    notes: list[str] = []
    if not policy_exists:
        notes.append(
            "No policy file found; this pack documents the built-in default policy. "
            "Run `aigis init` to materialise an editable policy."
        )
    if not settings_hook_configured:
        notes.append(
            "Claude Code PreToolUse hook is not configured in this project. "
            "Run `aigis init --agent claude-code` to install it."
        )
    if hooks_disabled:
        notes.append(
            "WARNING: disableAllHooks=true in .claude/settings.local.json — "
            "Aigis hooks will NOT run until this is removed."
        )

    return Evidence(
        aigis_version=_get_version(),
        generated_at=datetime.now(UTC).isoformat(),
        policy_path=policy_path_str,
        policy_exists=policy_exists,
        policy_mtime=policy_mtime,
        policy_name=policy.name,
        policy_version=policy.version,
        default_decision=policy.default_decision,
        allow_rules=allow_rules,
        deny_rules=deny_rules,
        review_rules=review_rules,
        total_rules=len(policy.rules),
        hook_script_present=hook_script.exists(),
        hook_script_path=str(hook_script),
        settings_hook_configured=settings_hook_configured,
        settings_path=str(settings_path),
        hooks_disabled=hooks_disabled,
        local_log_dir=str(local_log_dir),
        local_log_present=local_log_present,
        events_last_7d=events_7d,
        events_last_30d=events_30d,
        signed_audit_enabled=signed_audit_enabled,
        signed_audit_key_path=str(audit_key),
        signed_audit_log_path=signed_audit_log_path,
        siem_forwarder_configured=siem_on,
        siem_forwarder_detail=siem_detail,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Template-field helper
# ---------------------------------------------------------------------------


def _fill(value: str | None, placeholder_en: str, placeholder_ja: str, lang: str) -> str:
    """Return ``value`` if provided, else an explicit TO-FILL marker."""
    if value:
        return value
    if lang == "ja":
        return f"【要記入: {placeholder_ja}】"
    return f"[TO FILL: {placeholder_en}]"


# ===========================================================================
# TrustPackGenerator
# ===========================================================================


class TrustPackGenerator:
    """Generate the IT/security adoption-approval pack from live data."""

    #: Markdown file stems, in document order. ``README`` is the index.
    DOC_STEMS = [
        "01_executive_summary",
        "02_control_matrix",
        "03_policy_snapshot",
        "04_audit_log_evidence",
        "05_incident_runbook",
        "06_rollout_plan",
    ]

    def __init__(
        self,
        project_dir: str = ".",
        org: str | None = None,
        contact: str | None = None,
        evidence: Evidence | None = None,
    ) -> None:
        self.project_dir = project_dir
        self.org = org
        self.contact = contact
        self.evidence = evidence or gather_evidence(project_dir)
        # Cache the active policy object + literal YAML for the snapshot doc.
        self._policy, self._policy_yaml = self._load_active_policy()

    # -- Policy loading -----------------------------------------------------

    def _load_active_policy(self) -> tuple[Policy, str]:
        policy_path = Path(self.project_dir) / "aigis-policy.yaml"
        if policy_path.exists():
            return load_policy(str(policy_path)), policy_path.read_text(encoding="utf-8")
        from aigis.policy import _default_policy

        policy = _default_policy()
        # Render the default policy to a YAML string without touching disk.
        tmp = Path(self.project_dir) / ".aigis" / "_trust_pack_default_policy.yaml"
        try:
            tmp.parent.mkdir(parents=True, exist_ok=True)
            save_policy(policy, str(tmp))
            yaml_text = tmp.read_text(encoding="utf-8")
            tmp.unlink()
        except OSError:
            yaml_text = "# (default policy — run `aigis init` to materialise)\n"
        return policy, yaml_text

    # -- Public API ---------------------------------------------------------

    def write_markdown(self, out_dir: Path | str, lang: str = "both") -> list[Path]:
        """Write the pack as a set of Markdown files into ``out_dir``.

        Returns the list of files written (README first).
        """
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        langs = ["en", "ja"] if lang == "both" else [lang]

        written: list[Path] = []

        # README index always lists every file in the pack.
        readme = out / "README.md"
        readme.write_text(self._readme(langs), encoding="utf-8")
        written.append(readme)

        builders = {
            "01_executive_summary": self._executive_summary,
            "02_control_matrix": self._control_matrix_doc,
            "03_policy_snapshot": self._policy_snapshot,
            "04_audit_log_evidence": self._audit_log_evidence,
            "05_incident_runbook": self._incident_runbook,
            "06_rollout_plan": self._rollout_plan,
        }

        for stem in self.DOC_STEMS:
            build = builders[stem]
            for lng in langs:
                name = f"{stem}.md" if lng == "en" else f"{stem}.ja.md"
                path = out / name
                path.write_text(build(lng), encoding="utf-8")
                written.append(path)

        return written

    def write_html(self, out_dir: Path | str, lang: str = "both") -> Path:
        """Write the pack as a single self-contained HTML file.

        Returns the path to ``aigis-trust-pack.html``.
        """
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / "aigis-trust-pack.html"
        path.write_text(self._html(lang), encoding="utf-8")
        return path

    # -- README index -------------------------------------------------------

    def _readme(self, langs: list[str]) -> str:
        ev = self.evidence
        lines: list[str] = []
        lines.append("# Aigis Trust Pack — AI Agent Adoption Approval / AIエージェント導入承認パック")
        lines.append("")
        lines.append(
            "This pack contains the documents an IT / information-security "
            "department reviews before approving Claude Code (or another "
            "autonomous AI agent) for company use. Every document is generated "
            "from the **live local Aigis configuration** — policy, hooks, and "
            "audit logs — not from marketing claims."
        )
        lines.append("")
        lines.append(
            "本パックは、情報システム部門がClaude Code（または他の自律型AIエージェント）の"
            "社内利用を承認する際に確認する文書一式です。各文書は、マーケティング上の主張ではなく、"
            "**稼働中のローカルAigis設定**（ポリシー・フック・監査ログ）から生成されています。"
        )
        lines.append("")
        lines.append("## Pack metadata / パック情報")
        lines.append("")
        lines.append(f"- **Generated at / 生成日時:** {ev.generated_at}")
        lines.append(f"- **Aigis version / バージョン:** {ev.aigis_version}")
        org_disp = _fill(self.org, "organisation name", "組織名", "en")
        contact_disp = _fill(self.contact, "security contact email", "セキュリティ窓口メールアドレス", "en")
        lines.append(f"- **Organisation / 組織:** {org_disp}")
        lines.append(f"- **Security contact / セキュリティ窓口:** {contact_disp}")
        lines.append(f"- **Languages / 言語:** {', '.join(langs)}")
        lines.append("")
        lines.append("## Live posture summary / 現状サマリ")
        lines.append("")
        lines.append(f"- Active policy / 適用ポリシー: **{ev.policy_name}** (v{ev.policy_version}) — "
                     f"{ev.total_rules} rules ({ev.deny_rules} deny / {ev.review_rules} review / {ev.allow_rules} allow)")
        hook_state = "configured / 設定済み" if ev.settings_hook_configured else "NOT configured / 未設定"
        lines.append(f"- Claude Code hook / フック: **{hook_state}**")
        log_state = (
            f"present ({ev.events_last_7d} events in 7d) / あり"
            if ev.local_log_present
            else "no logs yet / ログなし"
        )
        lines.append(f"- Activity logs / 監査ログ: **{log_state}**")
        audit_state = "enabled / 有効" if ev.signed_audit_enabled else "available, not yet enabled / 利用可能（未有効化）"
        lines.append(f"- Signed audit log / 署名付き監査ログ: **{audit_state}**")
        lines.append("")
        lines.append("## Contents / 収録文書")
        lines.append("")
        titles = {
            "01_executive_summary": "Executive summary / エグゼクティブサマリ",
            "02_control_matrix": "Control matrix / コントロールマトリクス",
            "03_policy_snapshot": "Policy snapshot / ポリシースナップショット",
            "04_audit_log_evidence": "Audit log evidence / 監査ログの証跡",
            "05_incident_runbook": "Incident runbook / インシデント対応手順",
            "06_rollout_plan": "Rollout plan / 展開計画",
        }
        for stem in self.DOC_STEMS:
            for lng in langs:
                name = f"{stem}.md" if lng == "en" else f"{stem}.ja.md"
                lines.append(f"- [`{name}`](./{name}) — {titles[stem]} ({lng})")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(
            "_Honesty principle: this pack is generated from the live local "
            "configuration. Organisation-specific items (data classification, "
            "approver names, escalation contacts) appear as explicit "
            "`[TO FILL: ...]` / `【要記入: ...】` fields for you to complete. "
            "Compliance mappings are presented as supporting evidence, not as a "
            "certification or guarantee of compliance._"
        )
        lines.append("")
        return "\n".join(lines)

    # -- 01 Executive summary ----------------------------------------------

    def _executive_summary(self, lang: str) -> str:
        ev = self.evidence
        if lang == "ja":
            return self._exec_ja(ev)
        return self._exec_en(ev)

    def _exec_en(self, ev: Evidence) -> str:
        hook_state = "installed and configured" if ev.settings_hook_configured else "NOT yet installed"
        log_state = (
            f"active ({ev.events_last_7d} events in the last 7 days, "
            f"{ev.events_last_30d} in 30 days)"
            if ev.local_log_present
            else "no events recorded yet"
        )
        return f"""# 1. Executive Summary

**Organisation:** {_fill(self.org, "organisation name", "組織名", "en")}
**Prepared for:** {_fill(None, "IT / Information Security Department", "情報システム部門", "en")}
**Security contact:** {_fill(self.contact, "security contact email", "セキュリティ窓口メールアドレス", "en")}
**Generated:** {ev.generated_at} (Aigis v{ev.aigis_version})

## What Claude Code is

Claude Code is Anthropic's command-line coding agent. It reads and edits
files, runs shell commands, fetches web content, and can call external
tools (including Model Context Protocol servers) on a developer's machine
to complete software-engineering tasks autonomously. Because it executes
real actions on a real workstation, an uncontrolled deployment is a
meaningful operational and security risk.

## What Aigis adds

Aigis is a zero-dependency, open-source guardrail layer that sits between
the agent and the actions it wants to take. It provides three things an
IT/security department can rely on:

1. **Deterministic pre-execution guardrails.** A Claude Code *PreToolUse*
   hook intercepts every tool call. Aigis scans the request, evaluates it
   against your organisation's policy, and returns allow / review / deny
   **before** the action runs. Decisions are rule-based and reproducible —
   not a probabilistic model judging itself.
2. **Tamper-evident audit logs.** Every decision is recorded to an
   append-only JSONL log. A signed variant (HMAC-SHA256 + hash chain)
   makes after-the-fact deletion or modification detectable.
3. **An organisation-owned policy.** The policy is a human-readable file in
   your repository, reviewed and version-controlled like any other code.

Aigis runs entirely locally and adds no new runtime dependencies. It does
not send your prompts or code anywhere; it governs what the agent is
allowed to do on your machine.

## What this pack contains

- **Control matrix** — Aigis controls mapped to ISO/IEC 27001:2022 Annex A,
  NIST AI RMF, OWASP LLM Top 10, and the METI/MIC AI Business Operator
  Guidelines v1.2, plus an explicit "what Aigis does NOT cover" boundary.
- **Policy snapshot** — the exact policy currently in force, in plain
  language and as literal YAML.
- **Audit log evidence** — where logs live, their schema, retention, the
  tamper-evidence design, and the command to verify integrity.
- **Incident runbook** — what happens when Aigis blocks an action, how to
  triage, escalate, and report false positives.
- **Rollout plan** — a three-phase pilot template with review gates.

## Current live posture

- **Policy profile:** {ev.policy_name} (v{ev.policy_version}), {ev.total_rules}
  rules — {ev.deny_rules} deny, {ev.review_rules} review, {ev.allow_rules} allow.
  Default decision when no rule matches: `{ev.default_decision}`.
- **Hook status:** {hook_state}.
- **Log status:** {log_state}.
- **Signed audit log:** {"enabled" if ev.signed_audit_enabled else "available but not yet enabled"}.
- **SIEM forwarding:** {ev.siem_forwarder_detail}.

{self._notes_block_en(ev)}
"""

    def _exec_ja(self, ev: Evidence) -> str:
        hook_state = "導入・設定済み" if ev.settings_hook_configured else "未導入"
        log_state = (
            f"稼働中（直近7日間で{ev.events_last_7d}件、30日間で{ev.events_last_30d}件を記録）"
            if ev.local_log_present
            else "まだイベントは記録されていません"
        )
        audit_state = "有効" if ev.signed_audit_enabled else "利用可能ですが未有効化"
        return f"""# 1. エグゼクティブサマリ

**組織:** {_fill(self.org, "organisation name", "組織名", "ja")}
**提出先:** {_fill(None, "IT / Information Security Department", "情報システム部門", "ja")}
**セキュリティ窓口:** {_fill(self.contact, "security contact email", "セキュリティ窓口メールアドレス", "ja")}
**生成日時:** {ev.generated_at}（Aigis v{ev.aigis_version}）

## Claude Codeとは

Claude CodeはAnthropic社が提供するコマンドライン型のコーディングエージェントです。
ファイルの読み書き、シェルコマンドの実行、Webコンテンツの取得を行い、外部ツール
（Model Context Protocolサーバーを含む）を呼び出して、ソフトウェア開発タスクを
自律的に遂行します。開発者の実機上で実際の操作を実行するため、統制のない導入は
運用・セキュリティ上の重大なリスクとなり得ます。

## Aigisが付加するもの

Aigisは、エージェントと、それが実行しようとする操作との間に位置する、ゼロ依存の
オープンソース・ガードレール層です。情報システム部門が拠り所とできる、次の3点を
提供します。

1. **決定論的な実行前ガードレール。** Claude Codeの *PreToolUse* フックが、すべての
   ツール呼び出しを捕捉します。Aigisはリクエストを検査し、貴社のポリシーに照らして
   評価し、操作が実行される**前に**「許可／レビュー／拒否」を返します。判定はルール
   ベースで再現可能であり、モデルが自分自身を確率的に判定するものではありません。
2. **改ざん検知が可能な監査ログ。** すべての判定は追記専用のJSONLログに記録されます。
   署名付き版（HMAC-SHA256＋ハッシュチェーン）により、事後の削除・改ざんを検知できます。
3. **組織が保有するポリシー。** ポリシーはリポジトリ内の可読なファイルであり、他の
   コードと同様にレビューおよびバージョン管理が可能です。

Aigisは完全にローカルで動作し、新たな実行時依存関係を追加しません。プロンプトや
コードを外部に送信することはなく、エージェントが貴社の端末上で行える操作を統制します。

## 本パックの内容

- **コントロールマトリクス** — Aigisのコントロールを、ISO/IEC 27001:2022 附属書A、
  NIST AI RMF、OWASP LLM Top 10、および経済産業省・総務省「AI事業者ガイドライン
  v1.2」へマッピングしたもの。あわせて「Aigisが対象としない範囲」を明示します。
- **ポリシースナップショット** — 現在適用中のポリシーを、平易な説明と実際のYAMLで提示します。
- **監査ログの証跡** — ログの保存場所、スキーマ、保持期間、改ざん検知の設計、整合性
  検証コマンドを記載します。
- **インシデント対応手順** — Aigisが操作をブロックした際の流れ、トリアージ、エスカ
  レーション、誤検知の報告方法を記載します。
- **展開計画** — レビューゲートを備えた3段階のパイロット導入テンプレートです。

## 現状の稼働状況

- **ポリシープロファイル:** {ev.policy_name}（v{ev.policy_version}）、ルール{ev.total_rules}件
  — 拒否{ev.deny_rules}件、レビュー{ev.review_rules}件、許可{ev.allow_rules}件。
  どのルールにも一致しない場合の既定判定: `{ev.default_decision}`。
- **フックの状態:** {hook_state}。
- **ログの状態:** {log_state}。
- **署名付き監査ログ:** {audit_state}。
- **SIEM転送:** {ev.siem_forwarder_detail}。

{self._notes_block_ja(ev)}
"""

    def _notes_block_en(self, ev: Evidence) -> str:
        if not ev.notes:
            return ""
        out = ["## Setup notes (from live check)", ""]
        out += [f"- {n}" for n in ev.notes]
        return "\n".join(out) + "\n"

    def _notes_block_ja(self, ev: Evidence) -> str:
        if not ev.notes:
            return ""
        out = ["## セットアップに関する注記（稼働チェックより）", ""]
        out += [f"- {n}" for n in ev.notes]
        return "\n".join(out) + "\n"

    # -- 02 Control matrix --------------------------------------------------

    def _control_matrix_doc(self, lang: str) -> str:
        rows = control_matrix()
        if lang == "ja":
            header = "# 2. コントロールマトリクス\n\n"
            intro = (
                "本表は、Aigisが実装する各コントロールを、主要なセキュリティ・AIガバナンス"
                "フレームワークへ対応付けたものです。ISO/IEC 27001の項番は「証跡を補強する"
                "もの（supports evidence for）」として記載しており、Aigisが認証や準拠を保証"
                "するものではありません。\n\n"
            )
            col = "| Aigisコントロール | 概要 | ISO/IEC 27001:2022 附属書A | NIST AI RMF | OWASP LLM Top 10 | AI事業者GL v1.2 |\n"
            sep = "|---|---|---|---|---|---|\n"
            body = ""
            for r in rows:
                body += f"| {r.control_ja} | {r.what_it_does_ja} | {r.iso27001} | {r.nist_ai_rmf} | {r.owasp_llm} | {r.ai_gl} |\n"
            not_cov = "\n## Aigisが対象としない範囲\n\n"
            not_cov += (
                "正直な範囲設定のため、Aigisが**対象としない**領域を明示します。これらは"
                "別の管理策（既存のセキュリティ製品・運用体制）で対応する必要があります。\n\n"
            )
            not_cov += "\n".join(f"- {x}" for x in _NOT_COVERED_JA) + "\n"
            return header + intro + col + sep + body + not_cov

        header = "# 2. Control Matrix\n\n"
        intro = (
            "This table maps each control Aigis implements to the major security "
            "and AI-governance frameworks. ISO/IEC 27001 item numbers are listed "
            'as "supports evidence for" — Aigis is a control implementation, not a '
            "certification body, and does not guarantee compliance.\n\n"
        )
        col = "| Aigis control | What it does | ISO/IEC 27001:2022 Annex A | NIST AI RMF | OWASP LLM Top 10 | AI Business Operator GL v1.2 |\n"
        sep = "|---|---|---|---|---|---|\n"
        body = ""
        for r in rows:
            body += f"| {r.control} | {r.what_it_does} | {r.iso27001} | {r.nist_ai_rmf} | {r.owasp_llm} | {r.ai_gl} |\n"
        not_cov = "\n## What Aigis does NOT cover\n\n"
        not_cov += (
            "For an honest scope boundary, the following areas are **out of scope** "
            "for Aigis and must be handled by other controls (your existing security "
            "tooling and operational processes).\n\n"
        )
        not_cov += "\n".join(f"- {x}" for x in _NOT_COVERED_EN) + "\n"
        return header + intro + col + sep + body + not_cov

    # -- 03 Policy snapshot -------------------------------------------------

    def _policy_snapshot(self, lang: str) -> str:
        policy = self._policy
        if lang == "ja":
            head = "# 3. ポリシースナップショット\n\n"
            head += (
                f"現在適用中のポリシー: **{policy.name}**（v{policy.version}）。"
                f"どのルールにも一致しない場合の既定判定は `{policy.default_decision}` です。\n\n"
            )
            head += "## ルール一覧（可読形式）\n\n"
            head += "| # | ルールID | アクション | 対象 | 判定 | 理由 |\n"
            head += "|---|---|---|---|---|---|\n"
            for i, rule in enumerate(policy.rules, 1):
                head += f"| {i} | `{rule.id}` | `{rule.action}` | `{rule.target}` | **{rule.decision}** | {rule.reason} |\n"
            head += "\n## ポリシーファイル（実体・YAML）\n\n"
            head += "以下は、リポジトリで管理されている実際のポリシーファイルの全文です。\n\n"
            head += "```yaml\n" + self._policy_yaml.rstrip("\n") + "\n```\n"
            return head

        head = "# 3. Policy Snapshot\n\n"
        head += (
            f"Policy currently in force: **{policy.name}** (v{policy.version}). "
            f"Default decision when no rule matches: `{policy.default_decision}`.\n\n"
        )
        head += "## Rules (human-readable)\n\n"
        head += "| # | Rule ID | Action | Target | Decision | Reason |\n"
        head += "|---|---|---|---|---|---|\n"
        for i, rule in enumerate(policy.rules, 1):
            head += f"| {i} | `{rule.id}` | `{rule.action}` | `{rule.target}` | **{rule.decision}** | {rule.reason} |\n"
        head += "\n## Policy file (literal YAML)\n\n"
        head += "The following is the verbatim policy file under version control.\n\n"
        head += "```yaml\n" + self._policy_yaml.rstrip("\n") + "\n```\n"
        return head

    # -- 04 Audit log evidence ----------------------------------------------

    def _audit_log_evidence(self, lang: str) -> str:
        ev = self.evidence
        # Field list straight off the ActivityEvent dataclass — never hand-typed.
        fields = list(ActivityEvent.__dataclass_fields__.keys())
        field_lines = "\n".join(f"- `{f}`" for f in fields)
        if lang == "ja":
            return f"""# 4. 監査ログの証跡

## ログの保存場所

Aigisは監査ログを3階層で保持します（いずれも追記専用のJSONL形式、1行1イベント）。

- **ローカルログ:** `{ev.local_log_dir}`（プロジェクト単位、開発者が確認可能）
- **グローバルログ:** `~/.aigis/global/`（全プロジェクト横断、監査・CISO向け）
- **アラート保管:** `~/.aigis/alerts/`（拒否・レビューイベントを恒久保存）

現状: ローカルログは{"あり" if ev.local_log_present else "未生成"}、
直近7日間で{ev.events_last_7d}件、30日間で{ev.events_last_30d}件を記録しています。

## イベントスキーマ（JSONLフィールド）

各イベントは `aigis.activity.ActivityEvent` として記録され、以下のフィールドを持ちます。

{field_lines}

## 保持・ローテーション

- 完全ログは既定で60日間保持し、それ以降は自動でローテーション（圧縮または削除）されます。
- アラートログ（`~/.aigis/alerts/`）は恒久保存され、削除されません。
- ローテーション・圧縮は次のコマンドで実行します: `aigis maintenance`

## 改ざん検知の設計

署名付き監査ログ（`aigis.audit.SignedAuditLog`）は、各エントリに対して次を行います。

1. **HMAC-SHA256署名** — 各エントリの全フィールドを正準JSON化し、秘密鍵で署名します。
   署名はそのエントリの内容に依存するため、1バイトでも改変すれば署名検証に失敗します。
2. **ハッシュチェーン** — 各エントリは直前エントリのSHA-256ハッシュ（`prev_hash`）を保持
   します。これにより、エントリの削除・並べ替え・挿入が検知可能になります。

整合性は次の4チェックで検証されます: 署名・チェーン・連番・タイムスタンプ順序。

**検証コマンド:**

```
aigis audit verify
```

`--log PATH` でログファイルを指定でき、`--json` で機械可読な結果を出力します。
状態確認には `aigis audit status` を使用します。
現状: 署名付き監査ログは{"有効" if ev.signed_audit_enabled else "利用可能（未有効化）"}です。

## SIEM転送

イベントは任意で外部SIEMへ転送できます（Elastic Common Schema形式、HTTP）。転送は
非ブロッキングで、エージェントのツール呼び出しを遅延させません。送信前に個人情報の
墨消し（Redactor）を実行できます。詳細は `docs/forwarders.md` を参照してください。
現状: {ev.siem_forwarder_detail}。
"""

        return f"""# 4. Audit Log Evidence

## Where logs live

Aigis keeps audit logs in three tiers (all append-only JSONL, one event per line):

- **Local logs:** `{ev.local_log_dir}` (per-project, developer-visible)
- **Global logs:** `~/.aigis/global/` (cross-project, for audit / CISO)
- **Alert archive:** `~/.aigis/alerts/` (deny / review events, permanent)

Current state: local logs are {"present" if ev.local_log_present else "not yet created"},
with {ev.events_last_7d} events in the last 7 days and {ev.events_last_30d} in 30 days.

## Event schema (JSONL fields)

Each event is recorded as an `aigis.activity.ActivityEvent` with these fields:

{field_lines}

## Retention / rotation

- Full logs are retained for 60 days by default, then auto-rotated
  (compressed or deleted).
- Alert logs (`~/.aigis/alerts/`) are kept permanently and never deleted.
- Run rotation/compression with: `aigis maintenance`

## Tamper-evidence design

The signed audit log (`aigis.audit.SignedAuditLog`) does two things per entry:

1. **HMAC-SHA256 signature** — every field of the entry is canonicalised to
   JSON and signed with a secret key. The signature depends on the entry's
   content, so changing a single byte fails signature verification.
2. **Hash chain** — each entry stores the SHA-256 hash of the previous entry
   (`prev_hash`), so deleting, reordering, or inserting entries is detectable.

Integrity is checked with four tests: signature, chain, sequence, and
timestamp ordering.

**Verify command:**

```
aigis audit verify
```

Use `--log PATH` to point at a specific log file and `--json` for a
machine-readable result. Use `aigis audit status` for a quick health check.
Current state: signed audit log is
{"enabled" if ev.signed_audit_enabled else "available but not yet enabled"}.

## SIEM forwarding

Events can optionally be forwarded to an external SIEM (Elastic Common Schema,
over HTTP). Forwarding is non-blocking and never delays an agent tool call. A
PII redactor can run before any event leaves the process. See
`docs/forwarders.md`. Current state: {ev.siem_forwarder_detail}.
"""

    # -- 05 Incident runbook ------------------------------------------------

    def _incident_runbook(self, lang: str) -> str:
        if lang == "ja":
            return f"""# 5. インシデント対応手順

## Aigisが操作をブロックしたとき

Claude Codeの *PreToolUse* フックがツール呼び出しごとに動作します。Aigisがリクエストを
拒否（deny）した場合、フックは終了コード **2** を返し、Claude Codeはそのツール実行を
中止します。理由（一致したポリシールールID、必要に応じてリスクスコア）が標準エラー出力に
表示され、同時に監査ログへ記録されます。

フックはフェイルクローズ（fail-closed）設計です。入力の解析失敗、Aigis未導入、スキャン
時の例外など、判定できない事象が発生した場合は、安全側に倒してブロックします。

## 重大度レベル

| 重大度 | 目安 | 対応 |
|---|---|---|
| Critical | リスクスコア ≥ 80、または破壊的操作（`rm -rf` 等）の拒否 | 即時ブロック。記録を確認し、必要に応じてエスカレーション |
| High | リスクスコア 50–79 | ブロックまたはレビュー。担当者が確認 |
| Medium | リスクスコア 40–49、レビュー判定 | レビューキューで人間が承認 |
| Low | リスクスコア < 40 | 許可。ログのみ記録 |

## トリアージ手順

1. 直近のアラートを確認します: `aigis logs --alerts`
2. 該当イベントの詳細（アクション・対象・一致ルール・リスクスコア）を確認します。
3. 監査ログの整合性を検証します: `aigis audit verify`
4. 正当な操作が誤ってブロックされた場合は、下記「誤検知の報告」に従います。
5. 攻撃の可能性がある場合は、下記エスカレーションテンプレートで報告します。

## エスカレーションテンプレート

```
件名: [Aigis] {{重大度}} — {{ルールID}} を検知

発生日時: {{ISO-8601タイムスタンプ}}
プロジェクト / 端末: {{プロジェクト名 / ホスト名}}
利用者: {{ユーザーID}}
アクション: {{action}} 対象: {{target}}
リスクスコア: {{score}}  判定: {{decision}}
一致ルール: {{rule_id}}
監査ログ検証結果: {{aigis audit verify の結果}}

一次対応: {_fill(None, "first responder name", "一次対応者名", "ja")}
エスカレーション先: {_fill(self.contact, "escalation contact email", "エスカレーション先メールアドレス", "ja")}
```

## 誤検知（False Positive）の報告

1. ブロックされた具体的な入力／操作を記録します（`aigis logs --alerts --json`）。
2. 当該入力を再スキャンして再現します: `aigis scan "<入力>"`
3. 正当な操作であると確認できた場合は、ポリシーを調整します（下記参照）。
4. 調整内容は、レビュー記録のためコミットメッセージに残します。

## ポリシーの更新

- 現在のポリシーを確認: `aigis policy show`
- `aigis-policy.yaml` を編集してルールを追加・調整します。
- 妥当性を確認: `aigis policy check`
- 変更はバージョン管理し、{_fill(None, "approver / role", "承認者・役割", "ja")} の承認を経て反映します。
"""

        return f"""# 5. Incident Runbook

## What happens when Aigis blocks an action

A Claude Code *PreToolUse* hook runs on every tool call. When Aigis **denies**
a request, the hook exits with code **2** and Claude Code aborts that tool
execution. The reason (the matched policy rule ID, and the risk score where
relevant) is printed to standard error and simultaneously written to the
audit log.

The hook is **fail-closed**: if it cannot reach a decision — unparseable
input, Aigis not installed, an exception during scanning — it blocks on the
safe side.

## Severity levels

| Severity | Guideline | Response |
|---|---|---|
| Critical | Risk score ≥ 80, or a denied destructive op (`rm -rf`, etc.) | Immediate block. Review the record; escalate if needed |
| High | Risk score 50–79 | Block or review. A responder examines it |
| Medium | Risk score 40–49, review decision | Human approval via the review queue |
| Low | Risk score < 40 | Allowed; logged only |

## Triage steps

1. List recent alerts: `aigis logs --alerts`
2. Inspect the event details (action, target, matched rule, risk score).
3. Verify audit-log integrity: `aigis audit verify`
4. If a legitimate action was blocked, follow "Reporting false positives" below.
5. If this looks like an attack, report it using the escalation template.

## Escalation template

```
Subject: [Aigis] {{severity}} — detected {{rule_id}}

When: {{ISO-8601 timestamp}}
Project / host: {{project name / hostname}}
User: {{user_id}}
Action: {{action}} Target: {{target}}
Risk score: {{score}}  Decision: {{decision}}
Matched rule: {{rule_id}}
Audit-log verification: {{result of `aigis audit verify`}}

First responder: {_fill(None, "first responder name", "一次対応者名", "en")}
Escalate to: {_fill(self.contact, "escalation contact email", "エスカレーション先メールアドレス", "en")}
```

## Reporting false positives

1. Capture the exact blocked input/action (`aigis logs --alerts --json`).
2. Reproduce by re-scanning the input: `aigis scan "<input>"`
3. If it is genuinely legitimate, adjust the policy (see below).
4. Record the adjustment in the commit message for the review trail.

## Updating the policy

- Inspect the current policy: `aigis policy show`
- Edit `aigis-policy.yaml` to add or adjust rules.
- Validate: `aigis policy check`
- Version-control the change and apply it with sign-off from
  {_fill(None, "approver / role", "承認者・役割", "en")}.
"""

    # -- 06 Rollout plan ----------------------------------------------------

    def _rollout_plan(self, lang: str) -> str:
        if lang == "ja":
            return f"""# 6. 展開計画

Aigisの導入は、リスクを抑えつつ実運用での妥当性を確認するため、3段階で進めることを
推奨します。各フェーズの終わりにレビューゲートを設け、次フェーズへの移行可否を判断します。

## フェーズ1: パイロット（2週間）

対象: {_fill(None, "pilot team / project", "パイロットチーム・プロジェクト", "ja")}

- [ ] パイロット対象チームと範囲を確定する
- [ ] `aigis init --agent claude-code` でフックを導入する
- [ ] `aigis doctor` で導入状態を確認する
- [ ] 既定ポリシーで2週間運用し、ブロック・レビュー・誤検知を収集する
- [ ] `aigis logs --alerts` と週次レポートで状況を確認する
- [ ] 誤検知に応じてポリシーを調整する

**レビューゲート1:** 誤検知率は許容範囲か。重大なブロック事象はなかったか。
承認者: {_fill(None, "phase-1 approver", "フェーズ1承認者", "ja")}

## フェーズ2: 拡大

- [ ] パイロットで調整したポリシーを部門全体の標準として確定する
- [ ] 対象を {_fill(None, "next teams / departments", "次の対象チーム・部門", "ja")} へ拡大する
- [ ] 署名付き監査ログを有効化する
- [ ] 必要に応じてSIEM転送を構成する（`docs/forwarders.md`）
- [ ] インシデント対応手順を運用に組み込む

**レビューゲート2:** 監査ログの整合性は検証可能か（`aigis audit verify`）。
運用負荷は妥当か。承認者: {_fill(None, "phase-2 approver", "フェーズ2承認者", "ja")}

## フェーズ3: 全社標準

- [ ] Aigisを全社のClaude Code利用の標準とする
- [ ] ポリシー変更の承認フローを確立する
- [ ] 定期的なポリシーレビュー（四半期ごと等）を計画する
- [ ] 監査・コンプライアンス報告に本パックの再生成を組み込む

**レビューゲート3:** ガバナンス体制は継続的に運用可能か。
承認者: {_fill(None, "phase-3 approver", "フェーズ3承認者", "ja")}

---

_本パックはポリシー変更時に再生成することを推奨します（CIに組み込み可能）。
最新の稼働状況を反映した文書を、常に情報システム部門へ提出できます。_
"""

        return f"""# 6. Rollout Plan

We recommend introducing Aigis in three phases to limit risk while validating
it in real use. Each phase ends with a review gate that decides whether to
proceed to the next.

## Phase 1: Pilot (2 weeks)

Scope: {_fill(None, "pilot team / project", "パイロットチーム・プロジェクト", "en")}

- [ ] Confirm the pilot team and scope
- [ ] Install the hook with `aigis init --agent claude-code`
- [ ] Verify the install with `aigis doctor`
- [ ] Run the default policy for two weeks; collect blocks, reviews, and false positives
- [ ] Review status via `aigis logs --alerts` and the weekly report
- [ ] Tune the policy in response to false positives

**Review gate 1:** Is the false-positive rate acceptable? Were there any
serious block events? Approver: {_fill(None, "phase-1 approver", "フェーズ1承認者", "en")}

## Phase 2: Expand

- [ ] Finalise the pilot-tuned policy as the department standard
- [ ] Expand to {_fill(None, "next teams / departments", "次の対象チーム・部門", "en")}
- [ ] Enable the signed audit log
- [ ] Configure SIEM forwarding if required (`docs/forwarders.md`)
- [ ] Fold the incident runbook into operations

**Review gate 2:** Is audit-log integrity verifiable (`aigis audit verify`)?
Is the operational load reasonable? Approver:
{_fill(None, "phase-2 approver", "フェーズ2承認者", "en")}

## Phase 3: Organisation default

- [ ] Make Aigis the standard for all Claude Code use
- [ ] Establish the approval flow for policy changes
- [ ] Schedule periodic policy reviews (e.g. quarterly)
- [ ] Build pack regeneration into audit / compliance reporting

**Review gate 3:** Is the governance process sustainable?
Approver: {_fill(None, "phase-3 approver", "フェーズ3承認者", "en")}

---

_Regenerate this pack whenever the policy changes (it can run in CI), so the
documents you submit to IT always reflect the live posture._
"""

    # -- HTML ---------------------------------------------------------------

    def _html(self, lang: str) -> str:
        """Build a single self-contained HTML file (inline CSS, no JS/CDN).

        Renders the same Markdown documents converted to minimal HTML, with
        an anchor navigation bar. Both languages are included when
        ``lang == "both"``.
        """
        langs = ["en", "ja"] if lang == "both" else [lang]
        builders = {
            "01_executive_summary": self._executive_summary,
            "02_control_matrix": self._control_matrix_doc,
            "03_policy_snapshot": self._policy_snapshot,
            "04_audit_log_evidence": self._audit_log_evidence,
            "05_incident_runbook": self._incident_runbook,
            "06_rollout_plan": self._rollout_plan,
        }

        sections: list[str] = []
        nav_items: list[str] = []
        for lng in langs:
            for stem in self.DOC_STEMS:
                anchor = f"{stem}-{lng}"
                md = builders[stem](lng)
                html_body = _markdown_to_html(md)
                # Derive a nav label from the first heading line.
                first_line = md.splitlines()[0].lstrip("# ").strip()
                nav_items.append(f'<a href="#{anchor}">{_esc(first_line)} ({lng})</a>')
                sections.append(f'<section id="{anchor}">\n{html_body}\n</section>')

        nav = " · ".join(nav_items)
        ev = self.evidence
        title = "Aigis Trust Pack — AI Agent Adoption Approval / AIエージェント導入承認パック"
        meta = (
            f"Generated {_esc(ev.generated_at)} · Aigis v{_esc(ev.aigis_version)} · "
            f"Policy: {_esc(ev.policy_name)} (v{_esc(ev.policy_version)})"
        )
        return f"""<!DOCTYPE html>
<html lang="{langs[0]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{
    font-family: -apple-system, "Segoe UI", "Hiragino Kaku Gothic ProN",
      "Yu Gothic", Meiryo, sans-serif;
    line-height: 1.7; color: #1a1a2e; max-width: 920px; margin: 0 auto;
    padding: 2rem 1.25rem;
  }}
  header h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
  .meta {{ color: #555; font-size: 0.9rem; margin-bottom: 1rem; }}
  nav {{
    background: #f4f6fb; border: 1px solid #d8deec; border-radius: 8px;
    padding: 0.75rem 1rem; margin-bottom: 2rem; font-size: 0.9rem;
  }}
  nav a {{ color: #2b4eff; text-decoration: none; margin-right: 0.25rem; }}
  nav a:hover {{ text-decoration: underline; }}
  section {{
    border-top: 2px solid #e3e8f4; padding-top: 1.25rem; margin-top: 2rem;
  }}
  h1 {{ font-size: 1.4rem; }}
  h2 {{ font-size: 1.15rem; margin-top: 1.5rem; border-bottom: 1px solid #eee; padding-bottom: 0.2rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; margin: 1rem 0; }}
  th, td {{ border: 1px solid #d0d7e6; padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }}
  th {{ background: #eef1f8; }}
  code {{ background: #f2f3f7; padding: 0.1rem 0.3rem; border-radius: 4px; font-size: 0.85em; }}
  pre {{ background: #1a1a2e; color: #e8e8f0; padding: 1rem; border-radius: 8px; overflow-x: auto; font-size: 0.8rem; }}
  pre code {{ background: transparent; color: inherit; padding: 0; }}
  @media print {{ nav {{ display: none; }} body {{ max-width: none; }} }}
</style>
</head>
<body>
<header>
  <h1>{_esc(title)}</h1>
  <div class="meta">{meta}</div>
</header>
<nav>{nav}</nav>
{chr(10).join(sections)}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Minimal Markdown -> HTML (stdlib only, handles our generated subset)
# ---------------------------------------------------------------------------


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inline(text: str) -> str:
    """Escape, then apply inline `code`, **bold**, and [link](url)."""
    import re

    text = _esc(text)
    # Inline code first so its contents aren't re-formatted.
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def _markdown_to_html(md: str) -> str:
    """Convert the constrained Markdown produced here into HTML.

    Supports: ATX headings, fenced code blocks, pipe tables, ``-`` and
    ``- [ ]`` lists, horizontal rules, and paragraphs with inline
    code/bold/links. This is deliberately small — it only needs to handle
    the Markdown this module emits, not arbitrary documents.
    """
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    in_code = False
    code_buf: list[str] = []
    list_buf: list[str] = []

    def flush_list() -> None:
        if list_buf:
            out.append("<ul>")
            out.extend(list_buf)
            out.append("</ul>")
            list_buf.clear()

    while i < n:
        line = lines[i]

        # Fenced code block
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + _esc("\n".join(code_buf)) + "</code></pre>")
                code_buf = []
                in_code = False
            else:
                flush_list()
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Table block: a header row followed by a separator row of dashes.
        if (
            stripped.startswith("|")
            and i + 1 < n
            and set(lines[i + 1].strip()) <= set("|-: ")
            and "-" in lines[i + 1]
        ):
            flush_list()
            header_cells = [c.strip() for c in stripped.strip("|").split("|")]
            out.append("<table><thead><tr>")
            out.extend(f"<th>{_inline(c)}</th>" for c in header_cells)
            out.append("</tr></thead><tbody>")
            i += 2  # skip header + separator
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>")
                out.extend(f"<td>{_inline(c)}</td>" for c in cells)
                out.append("</tr>")
                i += 1
            out.append("</tbody></table>")
            continue

        # Headings
        if stripped.startswith("#"):
            flush_list()
            level = len(stripped) - len(stripped.lstrip("#"))
            level = min(level, 6)
            text = stripped[level:].strip()
            out.append(f"<h{level}>{_inline(text)}</h{level}>")
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            flush_list()
            out.append("<hr>")
            i += 1
            continue

        # List items (incl. checkboxes)
        if stripped.startswith("- "):
            item = stripped[2:]
            if item.startswith("[ ] "):
                item = "&#9744; " + item[4:]
            elif item.startswith("[x] ") or item.startswith("[X] "):
                item = "&#9745; " + item[4:]
            list_buf.append(f"<li>{_inline(item)}</li>")
            i += 1
            continue

        # Blank line
        if not stripped:
            flush_list()
            i += 1
            continue

        # Paragraph
        flush_list()
        out.append(f"<p>{_inline(stripped)}</p>")
        i += 1

    flush_list()
    if in_code and code_buf:
        out.append("<pre><code>" + _esc("\n".join(code_buf)) + "</code></pre>")
    return "\n".join(out)
