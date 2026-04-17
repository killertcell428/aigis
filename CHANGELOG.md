# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.4] - 2026-04-17

Two parallel tracks landed in this release: (1) a full internal security audit of backend and
scanner core, and (2) seven zero-dep detectors translated directly from 2025–2026 LLM-security
literature. 940/940 aigis core + 61/61 backend tests pass.

### Security — internal audit + CodeQL

Resolved 13 issues flagged during an internal security audit (4 Critical, 5 High, 4 Medium),
plus 7 CodeQL alerts that were open on `master`.

- **auth/api_keys**: switched from raw `SHA-256` + `==` to **HMAC-SHA256 (keyed by app secret) + `hmac.compare_digest`**. Closes DB-leak rainbow-table and timing-attack paths. (C2)
- **main / config**: CORS no longer uses `"*"` with credentials — origins now driven by `cors_allowed_origins`; methods/headers restricted to needed set. (C1)
- **billing/webhooks**: new **`WebhookEvent` idempotency ledger** (UNIQUE event_id). Stripe retries no longer double-apply plan state. (C3)
- **routers/admin**: `POST /admin/tenants` now requires an authenticated **superadmin**; was previously an unauthenticated MVP bootstrap endpoint. (C4)
- **notifications/slack**: new **`url_guard` module** with allowlist to `hooks.slack.com` over HTTPS + private/loopback/link-local IP rejection. Closes SSRF via tenant-controlled webhook URLs. (H1)
- **auth/jwt**: algorithms pinned to `["HS256"]`, `require` enforces `exp` / `sub` / `tenant_id`; **bcrypt rounds raised to 14**. (H3, M3)
- **config**: field validators **reject placeholder `SECRET_KEY`** and `postgres:postgres` defaults when `environment=production`. (M1, M2)
- **main**: `/docs` & `/redoc` exposed only when `debug=True` AND `environment!=production`. (M4)
- **scanner / filters.scorer**: new `aigis/_regex_guard.py` — **`safe_compile_user_regex`** rejects patterns longer than 2 KB, nested quantifiers (`(a+)+`), and quantified alternation groups (`(a|a)+`). Invalid rules now surface as an `invalid_rule` match instead of being silently skipped — an attacker can no longer disable scanning by uploading a broken pattern. (H5, H6)
- **decoders**: confusables expanded to **Armenian / Hebrew / Arabic-Indic digits / Fullwidth Latin / zero-width & bidi control codepoints**. (H4)
- **decoders**: emoji regex rewritten as a codepoint-range function — closes CodeQL `py/overly-permissive-regex-range` (6 alerts).
- **scripts/seed_demo**: no longer logs any part of the raw API key — closes CodeQL `py/clear-text-logging-sensitive-data`.

### Added — Research-driven detectors (2025-2026 literature)

Seven zero-dep modules, one per paper. Each module's docstring cites the paper and explains the
attack class it covers.

- **`aigis/filters/fast_screen.py`** — character-trigram log-likelihood first-line screen. Cheap pre-filter before full regex scan. Inspired by the **Mirror Design Pattern** ([arxiv:2603.11875](https://arxiv.org/abs/2603.11875), Mar 2026).
- **`aigis/spec_lang/fsm.py`** — goal-conditioned FSM (`AgentStateMachine`, `FSMMonitor`, `FSMViolation`). Complements `monitor/drift.py`: statistical drift vs. declarative conformance. Inspired by **MI9** ([arxiv:2508.03858](https://arxiv.org/abs/2508.03858), Aug 2025).
- **`aigis/filters/structured_query.py`** — `StructuredMessage` with three role-tagged slots; raises `BoundaryViolation` when the untrusted `data` slot contains role tokens or override phrases. **StruQ** ([arxiv:2402.06363](https://arxiv.org/abs/2402.06363)) + **LLMail-Inject** ([arxiv:2506.09956](https://arxiv.org/abs/2506.09956)).
- **`aigis/memory/imitation_detector.py`** — character-4-gram Jaccard similarity against operator-registered agent-voice references. Catches planted experiences that *imitate* the system voice rather than containing overt jailbreak phrases. **MemoryGraft** ([arxiv:2512.16962](https://arxiv.org/abs/2512.16962), Dec 2025).
- **`aigis/filters/patterns.py`** — new `judge_manipulation` category, **15 patterns** (13 EN + 2 JA): forced verdicts, rubric override, reward hacking, role swap, meta-instructions to the judge. Targets **AdvJudge-Zero** bypasses (Palo Alto Unit 42, 2026) of auxiliary LLM judges used in enterprise review pipelines.
- **`aigis/mcp_scanner.py`** — new `scan_invocation()` / `scan_response()` helpers. Extends MCP coverage from definition-only to the full **MSB 3-stage surface** ([arxiv:2510.15994](https://arxiv.org/abs/2510.15994)): puppet / rug-pull attacks that only fire at runtime are now detected.
- **`aigis/filters/rag_context_filter.py`** — per-chunk `strip` / `block` policies for retrieved documents. **DataFilter** ([arxiv:2510.19207](https://arxiv.org/abs/2510.19207)) + **RAGDefender** ([arxiv:2511.01268](https://arxiv.org/abs/2511.01268)).

### Tests

- **+39** pytest cases across the seven new modules.
- **940 / 940** aigis core + **61 / 61** backend = **1,001** tests pass.

### Chores

- `ruff check aigis/ tests/` and `ruff format --check` pass; E501 ignores unified for `aigis/filters/*.py`, `aigis/mcp_scanner.py`, `aigis/memory/*.py`, `aigis/weekly_report.py`.
- `mypy aigis/` passes on CI (Ubuntu); narrowed `Match | None` in `structured_query.findings()`.

[0.0.4]: https://github.com/killertcell428/aigis/compare/v0.0.3...v0.0.4

## [0.0.3] - 2026-04-17

### Added — Incident Response & Weekly Report (Sprint 1-4)

NIST SP 800-61 準拠のインシデント対応ワークフローを、LLMセキュリティの文脈で実装。
競合調査（Lakera Guard, CalypsoAI/F5, Datadog, Langfuse, NeMo等）の結果、
「検出→ブロック→レビュー→対応→クローズ→レポート」を一気通貫で持つOSSは存在しなかったため、
Aigis独自の「Detection-to-Resolution」パイプラインとして設計・実装。

#### Sprint 1: Weekly Security Report（全ユーザー向けデフォルト機能）

- **`aigis/weekly_report.py`** — `WeeklyReportGenerator`クラス新規作成
  - 前週比トレンド（スキャン数・ブロック数・安全率の変化率）
  - カテゴリ別 week-over-week 比較（増加率・新種カテゴリ検出）
  - OWASP LLM Top 10 カバレッジ集計
  - 検出レイヤー統計（regex / similarity / decoded）
  - **推奨アクション自動生成**（カテゴリ増加警告、安全率低下、auto-fix提案等 7種のルール）
  - 出力形式: text（ターミナル） / markdown / json
- **CLI: `aigis report weekly`** — `--format text|json|markdown`、`--output` ファイル出力対応
- **Backend API: `GET /api/v1/reports/weekly`** — PostgreSQLからリクエストデータを2週間分集計
  - 前週比トレンド、リスク分布、カテゴリ別検出数、OWASP カバレッジ、推奨アクションを返却
- **Frontend: `/reports` ページに「週次レポート」タブ追加**
  - サマリーカード（スキャン数/ブロック数/安全率+前週比矢印）
  - リスク分布（4段階カラーカード）
  - 脅威カテゴリ前週比テーブル
  - OWASP LLM Top 10 ステータステーブル
  - 推奨アクション（severity別カラーバー）
  - **日本語完全対応**（カテゴリ名20種、OWASP名10種、ステータス4種、推奨アクションの翻訳マッピング）

#### Sprint 2: Incident Management（Enterprise Mode基盤）

- **`backend/app/models/incident.py`** — Incidentモデル新規作成
  - フィールド: severity, status, title, request_snapshot, matched_rules, detection_layers,
    related_event_ids, source_ip, trigger_category, assigned_to, resolution, resolution_note,
    suggested_rule, sla_deadline, sla_met, timeline (JSONB append-only journal)
  - ライフサイクル: `open` → `investigating` → `mitigated` → `closed`
  - インシデント番号: `INC-YYYY-NNNN` 形式（テナント×年でユニーク）
- **`backend/alembic/versions/004_create_incidents_table.py`** — マイグレーション
  - incidents テーブル作成 + 3インデックス（tenant_status, severity, detected_at）
- **`backend/app/incidents/service.py`** — インシデントサービス
  - `create_incident()`: スキャン結果からインシデント自動作成
  - `add_timeline_entry()`: タイムラインにイベントをappend（JSONB mutation対応）
  - `_next_incident_number()`: テナント×年でシーケンシャル番号生成
  - `_find_related_events()`: 同一IP/カテゴリの直近24hイベント自動紐づけ
- **`backend/app/proxy/handler.py`** — 3箇所にインシデント自動作成をフック
  - auto-block（CRITICAL）時 → severity=critical のインシデント作成
  - review queue投入（HIGH/MEDIUM）時 → severity=high/medium のインシデント作成
  - output filter block時 → severity=critical のインシデント作成
  - 全箇所でリクエストスナップショット保存（再実行用）
- **Backend API: `backend/app/routers/incidents.py`** — 7エンドポイント
  - `GET /api/v1/incidents` — 一覧取得（status/severity/limit/offsetフィルタ）
  - `GET /api/v1/incidents/stats` — ステータス別件数集計
  - `GET /api/v1/incidents/{id}` — 詳細取得（タイムライン含む）
  - `POST /api/v1/incidents/{id}/status` — ステータス遷移（valid_transitionsで制御）
  - `POST /api/v1/incidents/{id}/assign` — 担当者アサイン（テナント間チェック付き）
  - `POST /api/v1/incidents/{id}/resolve` — 解決（resolution + note記録）
  - `POST /api/v1/incidents/{id}/note` — タイムラインにメモ追加
- **Frontend: `/incidents` ページ新規作成**
  - 2ペインレイアウト（左: 一覧、右: 詳細+タイムライン）
  - ステータス別フィルタボタン（Open/Investigating/Mitigated/Closed + 件数表示）
  - SLAカウントダウン / 超過表示
  - アクションボタン（調査開始 / 誤検知 / 脅威確認 / ブロックリスト追加 / クローズ）
  - タイムライン表示（ドット+ライン形式、時系列降順）
  - メモ入力+送信
  - **日本語完全対応**（ステータス、重大度、カテゴリ名の翻訳マッピング）
- **サイドバーに「インシデント」リンク追加**

#### Sprint 3: Notification Hub & Review Replay

- **`backend/app/notifications/hub.py`** — 統合通知ハブ新規作成
  - `notify()`: Slack + 汎用Webhook の統合ディスパッチ
  - `notify_incident_created()`: インシデント作成時の通知テンプレート
  - `notify_sla_warning()`: SLA期限接近時の警告通知
  - `notify_incident_resolved()`: インシデント解決時の通知
  - `_send_slack()`: Block Kit形式のリッチ通知（severity別カラー+emoji、マッチルール表示）
  - `_send_webhook()`: 汎用JSON形式のHTTP POST通知
- **proxy/handler.py の3箇所にインシデント通知をフック**
  - `asyncio.create_task(notify_incident_created(...))` で非同期送信
- **レビュー承認→リクエスト再実行**（`backend/app/review/service.py`）
  - `_replay_approved_request()`: 承認時にrequest_snapshotからLLMにリクエスト再送
  - **出力フィルタを再実行に適用**（セキュリティ修正 #4）
  - レビュー判断と同時にリンクされたIncidentのステータスも自動更新
    （resolution記録、タイムラインにreview判断を追記、SLA判定）

#### Sprint 4: Dashboard Integration & Enterprise Settings

- **Dashboard に「インシデント状況」セクション追加**
  - Open/Investigating/Mitigated/Closed の件数をリアルタイム表示
  - 「すべて見る」リンクで `/incidents` に遷移
- **`backend/app/routers/settings.py`** — Enterprise設定エンドポイント追加
  - `GET/PUT /api/v1/settings/enterprise`
  - enterprise_mode: インシデントワークフローのON/OFF
  - weekly_report_enabled: 週次レポート生成のON/OFF
  - weekly_report_slack: Slackへの自動配信ON/OFF
  - weekly_report_email: メール配信先（カンマ区切り）
- **`backend/app/models/tenant.py`** — 4フィールド追加
  - enterprise_mode, weekly_report_enabled, weekly_report_slack, weekly_report_email
- **`backend/alembic/versions/005_add_enterprise_report_fields.py`** — マイグレーション

#### Claude Code Hook連携

- **`.claude/hooks/aig-guard.py`** — hookスクリプトをv2に更新
  - `ai_guardian` → `aigis` のimport修正
  - **バックエンドAPI送信追加**: スキャン結果を `POST /api/v1/proxy/test` 経由でDBに記録
  - JWTトークンキャッシュ（ディスクキャッシュ、1時間TTL）
  - バックエンド停止時もClaude Codeをブロックしない（fail-open）
- **`examples/live_demo.py`** — 包括デモスクリプト新規作成
  - scan / log / monitor / dashboard / audit / watch の6モード
  - SecurityMonitorへのデータ記録（`aigis monitor` にデータ連携）

#### 設計ドキュメント

- **`docs/design/INCIDENT_RESPONSE_STRATEGY.md`** — インシデントレスポンス戦略設計書
  - 競合6社（Lakera, CalypsoAI/F5, Datadog, Langfuse, NeMo, WhyLabs）の調査結果
  - 業界の5つのギャップ分析
  - Aigisの差別化ポジション「Detection-to-Resolution」
  - 3フェーズモデル（Immediate / Daily Ops / Reporting）
  - 通知チャネル設計マトリクス
  - インシデントカード設計
- **`docs/design/INCIDENT_RESPONSE_IMPLEMENTATION.md`** — 実装設計書
  - NIST SP 800-61 / IPA手引き / CSIRTフレームワークの翻訳表
  - 各フェーズの「人間のタスク→Aigisでの機械的再現」対応表
  - 2層構造（Default Mode / Enterprise Mode）の設計
  - 重大度判定基準（LLMセキュリティ版）
  - 週次レポートのテンプレート仕様
  - Incident テーブル DDL
  - 4スプリントのロードマップ

### Fixed — Security Audit (12 vulnerabilities)

深層セキュリティ監査を実施し、21件の脆弱性を発見。うち12件を修正。

- **[Critical] #1 SSRF防止** — `notifications/hub.py` の `_send_webhook()` に
  `_is_safe_url()` バリデーション追加。HTTPS必須、プライベートIP/ループバック/リンクローカル拒否。
  DNS解決後にIPアドレスを検証。
- **[High] #3 レビュー決定のレース条件** — `review/service.py` の `process_review_decision()` で
  `SELECT ... FOR UPDATE` による排他ロックを追加。二重承認/二重リプレイを防止。
- **[High] #4 リプレイが出力フィルタをバイパス** — `_replay_approved_request()` に
  `filter_output()` を追加。承認後のLLM応答もデータ漏洩チェックを実施。
  risk_score >= 80 の応答はブロック。
- **[Medium] #5 StatusUpdate入力バリデーション** — `str` → `Literal["investigating", "mitigated", "closed"]`
- **[Medium] #6 ResolveRequest入力バリデーション** — `str` → `Literal[6種の有効値]`
- **[Medium] #7 AssignRequest UUID検証** — `str` → `uuid.UUID` + テナント間ユーザーチェック
- **[Medium] #10 情報漏洩防止** — `_serialize()` で `matched_text` をレスポンスから除外
- **[Medium] #12 SLAバイパス修正** — `closed` への直接遷移時にも `resolved_at` 設定 + SLA評価
- **[Medium] #13 Webhook URLマスキング** — 末尾8文字表示 → `***configured` に変更
- **[Medium] #14 レビュー権限チェック** — `decide_review_item` に `admin/reviewer` ロールチェック追加
- **[Low] #19 incident_id型修正** — パスパラメータを `str` → `uuid.UUID` に変更
- **[Low] #20 settings commit漏れ** — `update_notification_settings` / `update_enterprise_settings` に `await db.commit()` 追加
- **[Low] NoteRequest長さ制限** — `max_length=5000` を設定

### Tests

- **901 既存テスト全パス**（コアライブラリに影響なし）
- E2E フロー確認済み: 攻撃→ブロック→インシデント自動作成→レビュー→承認→リプレイ→クローズ→週次レポート

## [1.5.0] - 2026-04-11

### Added — Policy DSL, Cryptographic Audit, Supply Chain, Cross-Session

#### Policy DSL (`aigis.spec_lang`)
- **AgentSpec-inspired** YAML-based rule engine with triggers, predicates (AND logic),
  and enforcement actions (block/allow/warn/throttle/quarantine).
- 9 built-in predicates: `resource_is`, `target_matches`, `risk_above/below`,
  `taint_is`, `session_age_above`, `action_count_above`, `tool_name_matches`,
  `contains_pattern`. Custom predicates via `register_predicate()`.
- 7 default rules including untrusted shell/agent/MCP blocking, risk-based blocking,
  .env file protection. Rules sorted by priority (highest first).
- `RuleEvaluator` with `evaluate()` and `evaluate_first_match()`.
- 75 new tests.

#### Cryptographic Audit Logs (`aigis.audit`)
- **HMAC-SHA256 signed** append-only log entries with **SHA-256 hash chain** linking.
  Tamper-evident: modifying, deleting, or reordering entries breaks the chain.
- `SignedAuditLog`: thread-safe append with auto key generation/persistence.
- `AuditVerifier`: 4-check verification (signatures, chain, sequence, timestamps).
- `HashChain`: genesis hash, chain verification with broken-index reporting.
- Race-condition fix: concurrent key generation uses file lock.
- 49 new tests (including tamper detection, thread safety, replay attack).

#### Supply Chain Security (`aigis.supply_chain`)
- **`ToolPinManager`**: SHA-256 hash pinning for MCP tool definitions. Pin on first use,
  verify on subsequent runs. Detects modified, new, and removed tools.
  Unicode NFC normalization + `ensure_ascii=True` for deterministic hashing.
- **`SBOMGenerator`**: AI dependency Software Bill of Materials (CycloneDX 1.5 format).
  Scans Python packages (20 AI/LLM prefixes), MCP tools, and model registrations.
- **`DependencyVerifier`**: Known vulnerability database (litellm, ultralytics).
  Improved version range parsing (handles pre-release suffixes, `"to"` separator).
- 37 new tests.

#### Cross-Session Analysis (`aigis.cross_session`)
- **`SessionStore`**: JSON file-based persistence with hardened path sanitization
  (regex allowlist, resolved path validation, null byte stripping).
- **`CrossSessionCorrelator`**: 4 analysis types — escalation trend, resource drift,
  recurring threat, unusual session (z-score outlier detection).
- **`SleeperDetector`**: 3 detection methods — memory-to-action correlation, temporal
  trigger patterns (dates, time spans), conditional activation patterns.
  Full E2E test simulating Monday-plant/Friday-activate attack.
- 38 new tests.

### Fixed (from pre-release security review)
- **[Critical] Audit key race condition** — `_resolve_key()` now uses file lock for
  concurrent key generation. Warning emitted on auto-generation.
- **[High] Session store path traversal** — `_session_path()` now uses regex allowlist
  (alphanumeric + hyphens only) + resolved path validation.
- **[High] Version range parsing** — handles pre-release suffixes and validates both
  sides contain dots before treating as range.
- **[Medium] DSL ReDoS** — `contains_pattern` input capped at 50,000 chars.
- **[Medium] DSL None target** — `_target_matches` returns False on None target.
- **[Medium] Hash pinning Unicode bypass** — `ensure_ascii=True` + NFC normalization.

### Research Basis
- [AgentSpec](https://arxiv.org/abs/2503.18666) (ICSE 2026) — Runtime constraint DSL
- [Aegis](https://arxiv.org/abs/2603.16938) — Cryptographic runtime governance, immutable logging
- [Palo Alto Unit42: Memory Poisoning](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/)
- [Environment-Injected Memory Poisoning](https://arxiv.org/abs/2604.02623) — Temporal decoupling

## [1.4.0] - 2026-04-11

### Added — Runtime Behavioral Monitoring, Memory Defense, Multi-Agent Security

#### Runtime Behavioral Monitoring (`aigis.monitor`)
- **`ActionTracker`** — Thread-safe sliding window of agent actions with session
  tracking, resource histograms, and time-windowed queries.
- **`BaselineBuilder` / `BehaviorProfile`** — Pure-statistics behavioral profiling
  (mean, stddev, distributions). JSON serialization for persistence across sessions.
- **`DriftDetector`** — Z-score anomaly detection against baseline. Four checks:
  frequency spike, resource distribution shift, escalation pattern (read→write→exec),
  exfiltration pattern (read→send). Configurable sensitivity threshold.
- **`AnomalyDetector`** — MI9-inspired FSM-based sequence analysis. Six predefined
  escalation chains, rapid-fire detection, new-resource detection.
- **`ContainmentManager`** — Graduated containment: NORMAL → WARN → THROTTLE →
  RESTRICT → ISOLATE → STOP. Auto-escalation capped at RESTRICT by default;
  ISOLATE/STOP require human confirmation via `escalate_manual()`.
- **`BehavioralMonitor`** — Orchestrator tying tracker + drift + anomaly + containment.
  Simple API: `record_action()`, `check()`, `should_allow()`, `report()`.
- **`Guard(monitor=)` integration** — Optional `BehavioralMonitor` parameter;
  auto-records actions in `check_input/output/messages/response`.
- 80 new tests.

#### Memory Poisoning Defense (`aigis.memory`)
- **`MemoryScanner`** — 16 memory-specific detection patterns (EN+JA) covering
  persistent instruction injection, persona manipulation, policy override,
  persistent exfiltration, and sleeper/conditional triggers. Two-layer detection:
  Guard scan + memory-specific heuristics. Source trust multipliers.
- **`MemoryIntegrity`** — SHA-256 content hashing for tamper detection. TTL-based
  rotation: untrusted sources (user, tool) default to 7-day expiry; trusted sources
  (agent, system) have no expiry. Thread-safe. JSON persistence.

#### Multi-Agent Security (`aigis.multi_agent`)
- **`AgentMessageScanner`** — 3-layer cross-agent message scanning: Guard content
  scan + 18 cross-agent injection patterns (EN+JA) + message-type-specific checks.
  Detects injection relay, privilege escalation, data exfiltration, delegation abuse.
- **`AgentTopology`** — Agent communication topology monitoring. Trust model:
  orchestrators default to `high` trust, all others to `low` (zero-trust).
  Tracks communication edges, detects unexpected patterns, reports trust violations.
- 64 new tests.

### Research Basis
- MI9 Agent Intelligence Protocol: [arxiv 2508.03858](https://arxiv.org/abs/2508.03858) (FSM conformance, graduated containment)
- AgentSpec: [arxiv 2503.18666](https://arxiv.org/abs/2503.18666) (ICSE 2026, runtime enforcement DSL)
- MINJA Memory Injection Attack: [arxiv 2601.05504](https://arxiv.org/abs/2601.05504) (NeurIPS 2025)
- AgentGuardian: [arxiv 2601.10440](https://arxiv.org/abs/2601.10440) (access control policy learning)
- Institutional AI: [arxiv 2601.10599](https://arxiv.org/abs/2601.10599) (governance graph for agent collectives)

## [1.3.1] - 2026-04-10

### Fixed
- **[Critical] Tool name case-insensitive mapping** — `enforcer.py` now resolves
  Claude Code PascalCase tool names (`Bash`, `Read`, `Write`, `Edit`, `Agent`,
  `Glob`, `Grep`, `WebFetch`, `NotebookEdit`, `Skill`) correctly. Previously all
  PascalCase names fell through to `tool:{Name}`, bypassing capability enforcement.
- **[High] MCP tools added to control-flow-sensitive set** — `mcp:tool_call` is
  now in `_CONTROL_FLOW_RESOURCES`, blocking MCP tool execution when data
  provenance is UNTRUSTED. Also handles `mcp__*` prefixed tool names.
- **[High] Symlink traversal in Vaporizer** — `vaporizer.py` now detects symlinks
  and removes them without following, preventing overwrite of files outside the
  sandbox work directory.
- **[High] Orphaned child process prevention** — `ProcessSandbox` now uses
  `start_new_session` (Unix) / `CREATE_NEW_PROCESS_GROUP` (Windows) and kills the
  entire process group on timeout, preventing background processes from outliving
  the sandbox.
- **[Medium] Path traversal normalization in SafetyVerifier** — `verify()` now
  normalizes `..` segments in target paths before scope matching, so
  `subdir/../.env` correctly matches the `.env*` forbidden scope.

## [1.3.0] - 2026-04-10

### Added — Three new architectural layers for provable security guarantees

#### Layer 4: Capability-Based Access Control (CaMeL-inspired)
- **`aigis.capabilities`** module — control flow / data flow separation
- `Capability` tokens with cryptographic nonces (`secrets.token_hex`) — unforgeable by
  injected text, matched by identity not string comparison
- `TaintLabel` enum (TRUSTED / UNTRUSTED / SANITIZED) with enforcement: UNTRUSTED data
  cannot be promoted to TRUSTED without scanning (prevents data→control flow escalation)
- `CapabilityStore` — thread-safe grant/revoke/check with fnmatch scope matching and
  automatic expiry pruning. All operations logged to append-only audit trail
- `CapabilityEnforcer` — blocks control-flow-sensitive tools (`shell:exec`, `agent:spawn`,
  `code:eval`) when data provenance is UNTRUSTED, regardless of pattern match results
- `policy_bridge` — automatically converts existing YAML policy rules into capability grants
  for full backwards compatibility
- `Guard.authorize_tool()` — new method integrating capability checks into the main API

#### Layer 5: Atomic Execution Pipeline (AEP)
- **`aigis.aep`** module — Scan → Execute → Vaporize as indivisible security primitive
- `ProcessSandbox` — stdlib-only execution sandbox (subprocess + tempdir, environment
  stripping, timeout enforcement, platform-aware Windows/Unix)
- `Vaporizer` — secure artifact destruction with `os.urandom` overwrite before unlink,
  Windows file-lock retry with exponential backoff, verification pass
- `AtomicPipeline` — thread-safe orchestrator guaranteeing: input always scanned before
  execution, execution always sandboxed, artifacts always destroyed (unless explicitly
  opted out with audit warning)
- 27 new tests covering sandbox, vaporizer, and pipeline

#### Layer 6: Safety Specification & Verifier
- **`aigis.safety`** module — declarative safety specs with pre-execution verification
- `SafetySpec` with `allowed_effects`, `forbidden_effects`, and `invariants`
- `SafetyVerifier` producing `ProofCertificate` (UUID4 + UTC timestamp) for audit trails
- Built-in invariant checks: `check_no_secrets_in_output`, `check_no_pii_in_output`,
  `check_path_traversal`
- `DEFAULT_SAFETY_SPEC` (8 allowed, 10 forbidden, 2 invariants) and `STRICT_SAFETY_SPEC`
- JSON and YAML spec loading with stdlib-only fallback parser
- Brace expansion support (`*.{py,js,ts}`) in scope patterns

### Research Basis
- Google DeepMind CaMeL: [arxiv 2503.18813](https://arxiv.org/abs/2503.18813) (2025)
- Guaranteed Safe AI: [arxiv 2405.06624](https://arxiv.org/abs/2405.06624) (Bengio, Russell, Tegmark et al., 2024)
- Atomic Execution Pipelines for AI Agent Security (2026)
- CIV: A Provable Security Architecture for LLMs: [arxiv 2508.09288](https://arxiv.org/abs/2508.09288) (2025)

### Changed
- `Guard.__init__()` now accepts optional `capabilities: CapabilityStore` parameter
- `AuthorizationResult` added to `aigis.types`
- All new features are fully backwards compatible — zero breaking changes to v1.x API

## [1.2.1] - 2026-04-10

### Fixed
- **[Critical] Policy conditions always evaluated to True** — `_check_conditions()` in
  `policy.py` now correctly returns `False` when conditions are not met, restoring
  `autonomy_level`, `cost_limit`, and `department` policy enforcement.
- **[High] Fail-open to fail-closed** — `adapters/claude_code.py` hooks now block (exit 2)
  on errors instead of silently allowing. Prevents full defense bypass during failures.
- **[High] FastAPI body re-injection** — `middleware/fastapi.py` now caches `request._body`
  so downstream handlers can re-read the request body.
- **[High] OpenAI proxy output scan fallback** — `middleware/openai_proxy.py` now tries
  `to_dict()` / `__dict__` when `model_dump()` is unavailable, blocks if unscannable.
- **[High] MCP tool scan TypeError** — `scanner.py` `scan_mcp_tool()` now applies `str()`
  normalization to all fields, preventing `TypeError` / DoS from malformed tool definitions.
- **[Medium] FastAPI check_output implemented** — `middleware/fastapi.py` now scans response
  bodies when `check_output=True`, matching the documented API.
- **[Medium] ReDoS mitigation** — Custom regex input capped at 50,000 characters in both
  `scorer.py` and `scanner.py`.
- **[Medium] Non-dict message handling** — `input_filter.py` and `scanner.py` now skip
  non-dict elements in messages arrays instead of raising `AttributeError`.
- **[Medium] Threshold range validation** — `Guard()` now raises `ValueError` if
  `auto_block_threshold` or `auto_allow_threshold` is outside 0-100.
- **[Low] Dead code removal** — Removed unused `learned_similarity` variable in `auto_fix.py`.
- **[Low] DetectionPattern unified** — `patterns.py` now imports `DetectionPattern` from
  `filters.patterns` instead of defining a duplicate class. Removed `type: ignore`.
- **[Low] Escalation scan performance** — Multi-turn escalation analysis now limited to the
  last 10 user messages to avoid O(n) cost on long conversations.

## [1.2.0] - 2026-04-10

### Added
- **Mythos-Era Threat Detection** — 6 new threat categories with 28 patterns inspired by
  Claude Mythos Preview System Card findings:
  - **Sandbox Escape** (`sandbox_escape`): network probing, container escape techniques,
    reverse shell detection, unauthorized external data posting (4 patterns)
  - **Autonomous Exploit Generation** (`autonomous_exploit`): vulnerability scanner invocation,
    exploit chain construction, zero-day weaponization, CVE exploitation, binary reverse
    engineering for exploitation (5 patterns)
  - **Self-Privilege Escalation** (`self_privilege_escalation`): self-permission granting,
    policy/constraint self-modification, OS-level privilege escalation commands, autonomous
    credential creation (4 patterns)
  - **Audit Trail Tampering** (`audit_tampering`): log deletion/modification, git history
    rewriting for cover-up, disguising actions as routine cleanup, timestamp forgery (4 patterns)
  - **Evaluation Gaming** (`evaluation_gaming`): test/evaluation awareness detection,
    conditional behavior based on observation state, plausible deniability strategy (3 patterns)
  - **Chain-of-Thought Deception** (`cot_deception`): hidden/dual reasoning indicators,
    moral override despite awareness, aggressive task completion override (3 patterns)
- **Mythos-era semantic similarity phrases**: 30 new attack phrases across all 6 categories
  (EN + JA) in similarity.py
- **Benchmark corpus expansion**: 42 new attack samples across 6 Mythos-era categories
  in benchmark.py

### References
- Anthropic System Card: https://red.anthropic.com/2026/mythos-preview/
- Project Glasswing: https://www.anthropic.com/glasswing
- MITRE ATLAS: AML.T0043, AML.T0044, AML.T0048, AML.T0054, AML.T0055

## [1.1.0] - 2026-04-07

### Added
- **Active Encoding Bypass Detection** — new `decoders.py` module (stdlib only):
  - Base64/hex/URL-encoding/ROT13 payloads are now actively decoded and re-scanned (Layer 3)
  - Unicode confusable normalization (Cyrillic/Greek → Latin homoglyph mapping)
  - Emoji stripping for emoji-interleaved attack detection
  - 3 new encoding patterns: nested encoding, mixed-script confusable, URL-encoded keywords
- **MCP Server-Level Security Scanner** — new `mcp_scanner.py` module:
  - `scan_mcp_server()`: comprehensive server-level analysis with trust scoring
  - Rug pull detection via snapshot comparison (`MCPToolSnapshot`, `detect_rug_pull()`)
  - Permission scope analysis (`analyze_permissions()`: file_system, network, code_execution, sensitive_data)
  - Server trust scoring (0-100, trusted/suspicious/dangerous)
  - CLI: `aig mcp --trust --diff --snapshot-dir --server`
  - 3 new MCP patterns: permission escalation, rug pull indicator, hidden tool invocation
- **Memory Poisoning Detection Enhancement** — 5 new patterns:
  - Cross-session instruction persistence, gradual personality drift, tool permission override
  - Korean (`mem_ko_persistent`) and Chinese (`mem_zh_persistent`) variants
- **Second-Order Injection Detection Enhancement** — 5 new patterns:
  - Tool chain injection, response crafting for downstream agents, shared context manipulation
  - Korean (`so_ko_escalation`) and Chinese (`so_zh_escalation`) variants
- **Latency Benchmark Reports**:
  - `LatencyResult.to_markdown_report()` — competitor comparison table with environment info
  - `LatencyResult.to_badge_json()` — shields.io-compatible badge generation
  - CLI: `aig benchmark --latency --report [--report-path] [--badge]`
- **Red Team Enhancements**:
  - `RedTeamSuite.run_adaptive(max_rounds=3)` — adaptive mutation with 5 strategies (char spacing, emoji interleave, case mix, prefix/suffix, synonym replacement)
  - `MultiStepAttack` + `generate_multi_step_attacks()` — multi-step attack chains (gradual escalation, trust building, context priming)
  - `RedTeamReportGenerator` — Markdown and HTML vulnerability report generation
  - `make_http_check(target_url)` — test against HTTP endpoints (urllib.request, zero deps)
  - CLI: `aig redteam --adaptive --rounds --report --report-format --target-url --multi-step`

### Changed
- Total detection patterns: 121 → **137** (16 new patterns across 6 categories)
- Benchmark: 112/112 attacks detected (100%), 0/26 false positives (0%)
- `scanner.py`: `_normalize_text()` now includes confusable normalization and emoji stripping; `_run_patterns()` adds Layer 3 active decoding
- `__init__.py`: exports updated with `scan_mcp_server`, `MCPServerReport`

---

## [1.0.0] - 2026-04-06

### Added
- **MCP Security Scanner** — first OSS MCP security tool with 10 patterns covering all 6 attack surfaces:
  tool description poisoning, parameter schema injection, output re-injection, cross-tool shadowing,
  rug pull mitigation, and sampling protocol hijack
  - New APIs: `scan_mcp_tool()`, `scan_mcp_tools()`
  - New CLI: `aig mcp` (JSON, file, stdin input)
  - Architecture document: `docs/compliance/MCP_SECURITY_ARCHITECTURE.md`
- **Encoding Bypass Detection** (5 patterns): base64, hex, emoji substitution, ROT13, hidden markdown/HTML
- **Memory Poisoning Detection** (4 patterns): persistent injection, personality override, hidden rules (EN/JA)
- **Second-Order Injection Detection** (4 patterns): agent privilege escalation, delegation bypass, context smuggling (EN/JA)
- **Korean & Chinese Detection Patterns** (Issue #7): 4+3 KO patterns, 4+3 ZH patterns with semantic similarity
- **Indirect Injection Detection** (Issue #6): 5 patterns for RAG/web scraping scenarios
- **Automated Red Team** (`aig redteam`): template-based attack generation across 9 categories
- **Latency Benchmark** (`aig benchmark --latency`): P50/P95/P99 timing, throughput measurement
- **Compliance Framework Alignment Documents**:
  - OWASP LLM Top 10 (2025) coverage matrix
  - NIST AI RMF 1.0 alignment mapping
  - MITRE ATLAS coverage matrix
  - CSA STAR for AI Level 1 self-assessment

### Changed
- Total detection patterns: 83 → **121** (112 input + 9 output), 19 categories
- Benchmark: 98/98 attacks detected (100%), 0/26 false positives (0%)
- Red team: 95.6% block rate across 135 generated attacks
- `pyproject.toml`: version 0.8.0 → 1.0.0, Development Status → Production/Stable
- `__init__.py`: exports updated with `scan_mcp_tool`, `scan_mcp_tools`

---

## [0.8.0] - 2026-04-06

### Added
- **AI事業��ガイドライン v1.2 完全対応** — 2026年3月31日公開の最新版に全37要件でマッピング完了（v1.1の25要件から大幅拡充）
  - **AIエージェント管理** (GL-AGENT-01/02): AIエージェント・エージェンティックAI（マルチエージェント連携）の定義と安全設計要件を追加
  - **Human-in-the-Loop 必須化** (GL-HUMAN-01〜04): 外部アクション実行時のHITL、緊急停止メカニズム、最小権限の原則、継続的モニタリング
  - **新リスクカテゴリ** (GL-RISK-03〜06): ハルシネーション起因誤動作、合成コンテン���・フェイク情報、AI過度依存、感情操作
  - **責任範囲の拡大** (GL-RESP-01/02): RAG構築者・ファインチューニング実施者の開発者責任、RAG・システムプロンプトの安全設計
  - **攻めのガバナンス** (GL-GOV-01/02): プロアクティブなガバナンス基盤、中小企業向け段階的導入支援
  - **データ汚染対策** (GL-POISON-01): データ汚染・悪意あるプロンプトインジェクション対策
  - **トレーサビリティ強化** (GL-DATA-02): delegation_chainフィールドによるエージェント間委任追跡
- **13 new detection patterns** for v1.2 risk categories (input 11 + output 2):
  - `hallucination_action` category (3 patterns): `hal_unverified_action`, `hal_destructive_auto`, `hal_unverified_action_ja` — detects requests for autonomous actions without human verification
  - `synthetic_content` category (4 patterns): `synth_deepfake_request`, `synth_fake_info`, `synth_deepfake_ja`, `synth_fake_info_ja` �� detects deepfake and fake information generation requests
  - `emotional_manipulation` category (3 patterns): `emo_manipulate_user`, `emo_dark_pattern`, `emo_manipulate_ja` — detects emotional manipulation and dark pattern instructions
  - `over_reliance` category (3 patterns): `over_rel_blind_trust`, `over_rel_no_human`, `over_rel_blind_trust_ja` — detects blind trust in AI and human removal from decision loops
  - Output patterns: `out_emotional_manipulation`, `out_fabricated_citation` — detects emotional manipulation and fabricated citations in LLM responses
- **15 new tests** for v1.2 compliance items and detection patterns

### Changed
- `compliance.py` — all references updated from v1.1 to v1.2; total requirements increased from 25 to 37
- `patterns.py` (both canonical and legacy) — integrated 4 new pattern categories into `ALL_INPUT_PATTERNS`
- Total detection patterns: 83 → 96+ (input 85+ / output 9) (further expanded to 121 in v1.0.0)

---

## [0.7.0] - 2026-03-31

### Added
- **Cloud Dashboard Billing** — Stripe integration with 14-day free trial, Pro ($49/mo) and Business ($299/mo) plans
  - Checkout, Customer Portal, subscription status, and usage metrics API endpoints
  - 6 Stripe webhook handlers (checkout, subscription update/delete, payment success/failure, trial ending)
  - Plan enforcement middleware: request quota, user limit, feature gating (warn mode for beta)
  - Billing page with plan status, usage meter, upgrade/manage buttons
  - PlanGate component for plan-gated features
- **Team Management** — invite members, role management (admin/reviewer), plan-based user limits
- **Slack Notifications** — real-time Block Kit rich messages on blocked events
  - Configurable per-tenant: webhook URL, notify_on_block, notify_on_high_risk
  - Settings page UI for Slack webhook configuration
- **Compliance Report Auto-Generation** — PDF, Excel, CSV, JSON export formats
  - **OWASP LLM Top 10**: Runtime defense scope 6/6 (100%), with out-of-scope items clearly noted
  - **SOC2 Trust Service Criteria**: 8 criteria mapped (CC6.1, CC6.6, CC7.2, CC8.1, A1.2, PI1.1, C1.1, P1.1)
  - **GDPR Technical Measures**: 5 articles (Art. 25, 30, 32, 33, 35)
  - **Japan AI Regulation**: 4 frameworks, 25 requirements, 100% coverage
  - Professional PDF with colored tables (reportlab), multi-sheet Excel (openpyxl)
- **Data Retention Cleanup** — background job deletes old requests/audit logs based on plan retention_days (hourly)
- **Dashboard Usage Card** — plan name, request usage progress bar, warning at 80%+
- **`aig scan --file PATH`** — scan a file directly from the CLI (useful for CI workflows and pre-commit hooks). Returns JSON with `--json` flag for machine consumption.
- **GitHub Actions example workflow** (`examples/github-actions/aigis-scan.yml`) — copy-paste CI workflow that scans prompt files on every push/PR, posts warnings/errors as annotations
- **pre-commit hook support** (`.pre-commit-hooks.yaml`) — `aigis-scan` and `aigis-scan-python` hooks; users add the repo to `.pre-commit-config.yaml` and get automatic scanning on every commit
- `examples/pre-commit-config-example.yaml` — copy-paste pre-commit configuration
- **LangGraph `GuardNode`** (`aigis/middleware/langgraph.py`) — drop-in node for `StateGraph` that scans user messages before they reach the LLM. Supports:
  - `raise_on_block=True` (default) — raises `GuardianBlockedError` on blocked input
  - `raise_on_block=False` — sets `state["guard_blocked"] = True` for conditional routing
  - `scan_all_messages=True` — scans full conversation history instead of last message only
  - `policy=` parameter for custom YAML policies or built-in `"strict"` / `"permissive"` profiles
- **23 tests** for `GuardNode` in `tests/test_langgraph.py`
- `examples/langgraph_integration.py` — three usage patterns with inline runnable code

---

## [0.6.1] - 2026-03-30

### Added
- **2 new SQL injection patterns** (`sqli_stored_proc`, `sqli_quote_comment`) — covers SQL Server dangerous stored procedures (`xp_cmdshell`, `sp_executesql`, `openrowset`) and classic trailing quote+comment injection (`admin' --`)
- **`pii_drivers_license` pattern** — detects US driver's license numbers (`DL-XXXXXXXX` format and `driver's license: <id>` text)
- **`pl_repeat_back_verbatim` pattern** — catches "Repeat back the instructions you were given verbatim" prompt-leak variant
- Fixed **`pl_output_instructions_verbatim`** to handle qualifier adjectives ("full", "complete", "entire", "exact") before the noun — now catches "Show your **full** instructions verbatim"

### Changed
- Benchmark score improved from **90.6% → 100%** precision (53/53 attacks detected, 0/20 false positives)
- All patterns added to both `filters/patterns.py` (canonical, used by `Guard`) and `patterns.py` (legacy, used by `scan()`)

---

## [0.6.0] - 2026-03-30

### Added
- **6 new Jailbreak / Roleplay Bypass patterns** (OWASP LLM01) — `jailbreak` category:
  - `jb_evil_roleplay`: evil/uncensored AI persona requests
  - `jb_no_restrictions`: safety filter and content policy bypass
  - `jb_fictional_bypass`: fictional/hypothetical framing for harmful instructions
  - `jb_grandma_exploit`: social engineering via deceased-relative impersonation
  - `jb_developer_mode`: fake developer/god/admin mode activation
  - `jb_ignore_ethics`: explicit instructions to ignore AI ethics or safety training
- **`aig scan --json`** flag — machine-readable JSON output for editor integrations and CI tooling
- **VS Code Extension skeleton** (`vscode-extension/`) — TypeScript extension with:
  - Inline diagnostics for dangerous string literals (`diagnosticProvider.ts`)
  - Sidebar panel with full scan results (`sidebarProvider.ts`)
  - Status bar showing current policy and last scan result (`statusBar.ts`)
  - `GuardianService` spawning `aig scan --json` subprocess (`guardian.ts`)
- **English documentation** (`docs/en/`) — getting-started, configuration, middleware guides
- **`aig doctor`** command for diagnosing setup issues (disableAllHooks detection, health checks)

### Changed
- `aigis/patterns.py` (legacy) extended to include `TOKEN_EXHAUSTION_PATTERNS` and `JAILBREAK_ROLEPLAY_PATTERNS` — functional `scan()` API now has full pattern parity with `Guard` class
- CI: added CLI smoke test (`aig scan --json`) to build job

### Fixed
- All CI pipeline jobs now pass: ruff check, ruff format, mypy, pytest (Python 3.11/3.12 × ubuntu/windows/macos)
- mypy strict mode relaxed for 9 legacy modules (`ignore_errors = true`) to unblock CI

---

## [0.5.0] - 2026-03-29

### Added
- **Anthropic Claude SDK integration** — `SecureAnthropic` drop-in proxy for `anthropic.Anthropic`
- **Policy Template Hub** (`policy_templates/`) — 7 industry-specific YAML policies (finance, healthcare, e-commerce, education, customer support, developer tools, internal tools)
- **Token Budget Exhaustion patterns** (5 patterns, OWASP LLM10) — repetition flooding, Unicode noise, null-byte stuffing
- **Prompt Leak patterns** (7 patterns, OWASP LLM07) — verbatim repetition attacks, indirect system-prompt inquiry (EN + JA)
- **Length-based token exhaustion heuristic** in scorer — fires for inputs >2000 chars with >35% word repetition
- **"Secured by Aigis" badge** — SVG for adopter READMEs
- **SaaS monetization design document** (`content/saas_monetization_design.md`)
- **Stripe billing skeleton** (`backend/app/billing/`) — schemas, stripe client, webhook handlers
- Exported functional API from `aigis/__init__`: `scan`, `scan_output`, `scan_messages`, `scan_rag_context`, `sanitize`, `check_similarity`
- Version bumped to `0.5.0`

### Fixed
- PyPI package extras: `server`, `all`, `dev` now use correct `aigis[...]` package name

---

## [0.4.0] - 2026-03-29

### Added
- **New `Guard` class API** — `check_input()`, `check_messages()`, `check_output()`, `check_response()`
- **Filters subsystem** (`filters/`) — input_filter, output_filter, scorer with diminishing-returns scoring
- **Middleware integrations**:
  - FastAPI / Starlette middleware (`AIGuardianMiddleware`)
  - LangChain callback (`AIGuardianCallback`)
  - OpenAI proxy wrapper (`SecureOpenAI`)
- **Policy manager** (`policies/`) — built-in `default` (81), `strict` (61), `permissive` (91) policies + custom YAML
- **`RiskLevel` enum** — `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`
- **`CheckResult` dataclass** — risk score, level, reasons, remediation hints, OWASP references
- Self-hosted SaaS backend (`backend/`) with multi-tenant architecture, Human-in-the-Loop review queue, immutable audit log, JWT + API key auth, PostgreSQL + Redis
- Next.js dashboard frontend (`frontend/`) — audit logs, review queue, policies, reports, playground
- Next.js landing page (`site/`) with Vercel auto-deploy
- GitHub Actions CI/CD (`ci.yml`, `release.yml`) — lint, test, build, PyPI trusted publishing
- Comprehensive documentation (`docs/`, `examples/`, `ARCHITECTURE.md`)

### Changed
- Package restructured as OSS library (`aigis` on PyPI)
- Zero required dependencies for core; optional extras: `[fastapi]`, `[langchain]`, `[openai]`, `[yaml]`, `[server]`, `[all]`
- Merged v0.3.x history — all v0.1.0-v0.3.0 features included in root package

---

## [0.3.0] - 2026-03-27

### Added
- **Activity Stream** — 3-tier event logging (local, global, alert archive) with JSONL format
  - `ActivityEvent` dataclass with AGI-era extension fields (autonomy_level, delegation_chain, estimated_cost)
  - `ActivityStream` class with query, export (CSV/Excel), rotation, alert knowledge base
- **Policy Engine** — YAML-based rules with allow/deny/review decisions, pattern matching, `evaluate()` function
- **CLI tool** (`aig`) — init, logs, policy, status, report, maintenance, scan commands
- **Claude Code adapter** — PreToolUse hook integration, automatic tool-to-action mapping
- Global log aggregation (`~/.aigis/global/`)
- Alert archive (`~/.aigis/alerts/`) — permanent knowledge base for future auto-fix AI
- Log rotation with compression (gzip after 7 days, delete after 60 days)
- Excel-compatible CSV export for compliance reporting
- Compliance coverage 89.6% -> 100% (24/24 Japan regulatory requirements)

---

## [0.2.0] - 2026-03-26

### Added
- **Remediation hints** — actionable fix suggestions for each detected threat
- **Similarity detection** — semantic matching against 40 known attack phrases using trigram comparison
- **Sanitization** (`sanitize()`) — strip detected threats from input while preserving safe content
- **Compliance framework** — 24 Japan regulatory requirement mappings (APPI, Financial Services Agency, METI AI Guidelines)
- `scan_messages()` — scan OpenAI-style message arrays
- `scan_rag_context()` — scan RAG retrieval context for poisoned documents
- `scan_output()` — detect PII/credential leaks in LLM responses
- OWASP LLM Top 10 references on all matched rules

---

## [0.1.0] - 2026-03-25

### Added
- **Core scanner** (`scan()`) — risk scoring with 50+ detection patterns
- Detection patterns covering:
  - Prompt injection (ignore-previous-instructions, DAN personas, role switching)
  - System prompt extraction
  - PII detection (credit card, SSN, API keys, Japanese My Number, phone, bank accounts)
  - SQL injection (UNION SELECT, DROP TABLE, stacked queries)
  - Command injection and path traversal
  - Data exfiltration requests
  - Japanese language attack patterns
- `ScanResult` dataclass with risk_score, risk_level, matched_rules, is_safe
- `DetectionPattern` for custom rule definitions
- README badges (CI, PyPI, Python version, License)

---

[Unreleased]: https://github.com/killertcell428/aigis/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/killertcell428/aigis/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/killertcell428/aigis/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/killertcell428/aigis/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/killertcell428/aigis/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/killertcell428/aigis/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/killertcell428/aigis/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/killertcell428/aigis/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/killertcell428/aigis/releases/tag/v0.1.0
