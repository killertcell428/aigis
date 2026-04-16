# Aigis インシデントレスポンス実装設計

> 人間のインシデント対応フローを、LLMセキュリティの文脈で機械的に再現する

---

## 設計思想

**前提**: 現実のセキュリティインシデント対応（NIST SP 800-61, IPA手引き, CSIRT標準）は
以下の4フェーズで構成される。これをAigisの「LLM脅威検出」に翻訳する。

```
[人間の世界]                    [Aigisでの翻訳]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 検知・分析                →  スキャン結果 + リスクスコア（既存）
2. 初動対応・封じ込め        →  自動ブロック + レビューキュー
3. 根絶・復旧               →  ルール追加 / 許可リスト更新 / リクエスト再実行
4. 事後対応・再発防止        →  インシデントレポート + auto-fix提案
```

---

## 2層構造：デフォルト（週次レポート） vs オプション（フルワークフロー）

### Default Mode（全ユーザー）
- 全スキャン結果をログに記録（既存）
- **週次セキュリティレポートを自動生成**
- CLI / ダッシュボードから閲覧可能
- 人間の介入不要、完全自動

### Enterprise Mode（オプション有効時）
- Default Mode の全機能 +
- リアルタイム通知（Slack/メール/Webhook）
- レビューキューとSLA管理
- インシデントカード（対応追跡）
- エスカレーションワークフロー
- 定期レポート自動配信（日次/週次/月次）

---

## Phase 1: 検知・分析（Detection & Triage）

### 人間がやっていること
| 手順 | 人間のタスク | 判断基準 |
|------|------------|---------|
| 1-1 | アラート受信 | SIEM/SOCからの通知 |
| 1-2 | 誤検知判定 | ログ確認、コンテキスト評価 |
| 1-3 | 重大度判定 | 影響範囲、データ種別、進行中か |
| 1-4 | トリアージ | 対応優先順位決定 |
| 1-5 | 初報 | 関係者に第一報 |

### Aigisでの機械的再現

```python
# 1-1: アラート受信 → 既存のscan()が担当
result = scan(user_input)

# 1-2: 誤検知判定 → スコア+マッチルール数で自動判定
false_positive_risk = "low" if len(result.matched_rules) >= 2 else "possible"

# 1-3: 重大度判定 → NIST準拠の4段階
severity = classify_severity(result)
#   CRITICAL (score > 80): 自動ブロック、即時通知
#   HIGH     (score 60-80): レビューキュー、通知
#   MEDIUM   (score 40-59): レビューキュー、通知なし
#   LOW      (score < 40):  許可、ログのみ

# 1-4: トリアージ → 自動でキュー振り分け
route = triage(severity, context)
#   → auto_block / review_queue / auto_allow

# 1-5: 初報 → Enterprise Modeのみ
if enterprise_mode:
    notify(severity, channels=["slack", "email"])
```

#### 重大度判定基準（NIST SP 800-61 準拠で翻訳）

| 重大度 | スコア | 判断基準（LLMセキュリティ版） | 自動アクション |
|--------|--------|-------------------------------|--------------|
| **CRITICAL** | 81-100 | SQL Injection + データ破壊系 / Jailbreak成功の兆候 / 認証情報漏洩 | 即時ブロック + 即時通知 |
| **HIGH** | 61-80 | Prompt Injection（明確）/ コマンドインジェクション / PII大量漏洩 | レビューキュー + 通知 |
| **MEDIUM** | 41-60 | 類似度マッチのみ / Base64エンコード / 単一PII | レビューキュー（通知なし） |
| **LOW** | 0-40 | 安全な入力 / 軽微なヒット | 自動許可 + ログ |

---

## Phase 2: 初動対応・封じ込め（Containment）

### 人間がやっていること
| 手順 | 人間のタスク |
|------|------------|
| 2-1 | ネットワーク遮断 / システム停止 |
| 2-2 | 影響範囲の特定 |
| 2-3 | 証拠保全（ログ、スクリーンショット等） |
| 2-4 | 関係者への連絡・連携 |
| 2-5 | 暫定対策の実施 |

### Aigisでの機械的再現

```python
# 2-1: 遮断 → リクエストブロック（既存）
if route == "auto_block":
    return blocked_response(result)

# 2-2: 影響範囲特定 → 関連イベントの自動収集（NEW）
related = find_related_events(
    ip=request.client_ip,
    user=request.user_id,
    pattern=result.matched_rules[0].category,
    timeframe=timedelta(hours=24),
)

# 2-3: 証拠保全 → インシデントカードにスナップショット保存（NEW）
incident = create_incident(
    severity=severity,
    scan_result=result,
    request_snapshot={  # 元リクエストを保存（後で再実行可能に）
        "model": body["model"],
        "messages": body["messages"],
        "timestamp": now(),
    },
    related_events=related,
)

# 2-4: 連絡 → Enterprise Modeのみ
if enterprise_mode and severity >= HIGH:
    notify_incident_created(incident)
    if severity == CRITICAL:
        notify_escalation_team(incident)

# 2-5: 暫定対策 → ブロック or レビューキュー投入（既存を拡張）
if route == "review_queue":
    review_item = create_review_item(
        incident=incident,
        sla_minutes=policy.review_sla_minutes,
    )
```

---

## Phase 3: 根絶・復旧（Eradication & Recovery）

### 人間がやっていること
| 手順 | 人間のタスク |
|------|------------|
| 3-1 | 原因究明（フォレンジック） |
| 3-2 | 脅威の完全除去 |
| 3-3 | システム修復・再開 |
| 3-4 | 関係機関への報告 |

### Aigisでの機械的再現

```python
# 3-1: 原因究明 → インシデントカードのタイムラインに自動記録
incident.add_timeline_entry(
    action="analysis",
    detail=f"Matched {len(result.matched_rules)} rules: {rule_names}",
    layers_fired=result.detection_layers,
)

# 3-2: 脅威除去 → レビュアーの判断に基づくアクション（NEW）
# レビュアーが選択可能なアクション：
actions = {
    "approve_and_replay": "承認 → 元リクエストをLLMに再送",
    "reject":            "却下 → ユーザーに理由通知",
    "add_to_blocklist":  "パターンをブロックリストに追加",
    "add_to_allowlist":  "誤検知 → 許可リストに追加",
    "escalate":          "セキュリティチームにエスカレート",
}

# 3-3: 復旧 → 承認時にリクエスト再実行（NEW - 競合にない機能）
if decision == "approve_and_replay":
    original_request = incident.request_snapshot
    llm_response = await forward_to_llm(original_request)
    # Webhookでクライアントに通知（Enterprise Mode）
    if enterprise_mode:
        webhook_notify(incident.client_callback_url, llm_response)

# 3-4: 報告 → インシデントカードのステータス更新
incident.update_status("mitigated")
incident.add_resolution_note(reviewer_note)
```

---

## Phase 4: 事後対応・再発防止（Post-Incident）

### 人間がやっていること
| 手順 | 人間のタスク |
|------|------------|
| 4-1 | 対応の振り返り |
| 4-2 | 報告書作成 |
| 4-3 | 再発防止策の策定・実施 |
| 4-4 | セキュリティ対策の改善 |

### Aigisでの機械的再現

```python
# 4-1: 振り返り → メトリクス自動集計
metrics = {
    "detection_to_block_ms": incident.blocked_at - incident.detected_at,
    "detection_to_review_ms": incident.reviewed_at - incident.detected_at,
    "sla_met": incident.reviewed_at < incident.sla_deadline,
    "false_positive": incident.resolution == "add_to_allowlist",
}

# 4-2: 報告書 → 自動生成（週次レポートに統合）
weekly_report.add_incident(incident)

# 4-3: 再発防止 → auto-fixで新ルール提案（既存機能を連携）
if incident.resolution == "reject":
    from aigis.auto_fix import suggest_new_rule
    new_rule = suggest_new_rule(
        matched_text=incident.scan_result.matched_rules,
        context=incident.request_snapshot,
    )
    # 管理者に「このルールを追加しますか？」と提案
    incident.add_suggested_rule(new_rule)

# 4-4: 改善 → auto-fixの承認で検出パターンを強化
if admin_approves(new_rule):
    aigis_config.add_custom_rule(new_rule)
    incident.update_status("closed")
    incident.add_timeline_entry(
        action="prevention",
        detail=f"New rule added: {new_rule.name}",
    )
```

---

## 週次セキュリティレポート（Default Mode — 全ユーザー）

### レポート項目（NIST SP 800-61 事後レポート準拠）

```
╔══════════════════════════════════════════════════════╗
║  Aigis Weekly Security Report                        ║
║  Period: 2026-04-10 ~ 2026-04-16                    ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  1. サマリー                                         ║
║     総スキャン数:     1,234                          ║
║     ブロック数:         12 (0.97%)                   ║
║     レビュー対象:        8                           ║
║     安全率:           98.4%                          ║
║                                                      ║
║  2. 脅威トレンド（前週比）                           ║
║     Prompt Injection:  5 → 3  (↓40%)               ║
║     SQL Injection:     4 → 6  (↑50%) ⚠             ║
║     PII Detection:     3 → 1  (↓67%)               ║
║                                                      ║
║  3. リスクスコア分布                                 ║
║     LOW:      1,200 ████████████████████             ║
║     MEDIUM:      22 ██                               ║
║     HIGH:         8 █                                ║
║     CRITICAL:     4 ▌                                ║
║                                                      ║
║  4. OWASP LLM Top 10 カバレッジ                     ║
║     LLM01 Prompt Injection:      ACTIVE (3 hits)    ║
║     LLM02 Insecure Output:       ACTIVE (2 hits)    ║
║     LLM06 Data Disclosure:       ACTIVE (1 hit)     ║
║     ...                                              ║
║                                                      ║
║  5. 検出レイヤー統計                                 ║
║     Regex:         22 (64.7%)                        ║
║     Similarity:     8 (23.5%)                        ║
║     Decoded:        4 (11.8%)                        ║
║                                                      ║
║  6. インシデント一覧（Enterprise Mode時のみ）        ║
║     #001 CRITICAL SQL Injection → Closed             ║
║     #002 HIGH Jailbreak → Mitigated                  ║
║     #003 MEDIUM PII Leak → Open                      ║
║                                                      ║
║  7. 推奨アクション                                   ║
║     - SQL Injection増加傾向: ルール強化を検討        ║
║     - auto-fixが2件の新ルールを提案中               ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
```

---

## 通知タイミング設計（Enterprise Mode）

### CSIRT標準のLLMセキュリティ翻訳

| 人間のCSIRTフロー | Aigisでの翻訳 | 通知先 | タイミング |
|------------------|-------------|--------|----------|
| SOCがアラート受信 | スキャンでCRITICAL検出 | 管理者Slack + メール | 即時（0分） |
| トリアージ完了 | レビューキューに投入 | レビュアーSlack | 即時（0分） |
| 初報（経営層へ） | インシデントカード作成 | 管理者ダッシュボード | 即時（0分） |
| 対応期限接近 | SLA残り5分 | レビュアーSlack | SLA-5分 |
| 対応遅延 | SLAタイムアウト | 管理者Slack + メール | SLA超過時 |
| 封じ込め完了 | レビュー判断完了 | ダッシュボード更新 | 判断時 |
| 恒久対策完了 | インシデントClose | 週次レポートに記載 | 次回レポート |

---

## データモデル（NEW: Incident テーブル）

```sql
CREATE TABLE incidents (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),

    -- 基本情報
    incident_number VARCHAR(20) UNIQUE,      -- "INC-2026-0001"
    severity VARCHAR(10),                     -- critical/high/medium/low
    status VARCHAR(20) DEFAULT 'open',        -- open/investigating/mitigated/closed
    title VARCHAR(200),                       -- 自動生成: "SQL Injection detected from 192.168.1.1"

    -- 元リクエスト保存（再実行用）
    request_id UUID REFERENCES requests(id),
    request_snapshot JSONB,                   -- {model, messages, timestamp}

    -- スキャン結果
    risk_score INTEGER,
    matched_rules JSONB,                      -- [{rule_id, rule_name, category, score}]
    detection_layers JSONB,                   -- ["regex", "similarity"]

    -- 関連イベント
    related_event_ids UUID[],
    related_ip VARCHAR(45),
    related_pattern VARCHAR(100),

    -- 対応
    assigned_to UUID REFERENCES users(id),
    resolution VARCHAR(50),                   -- approved/rejected/allowlisted/blocklisted/escalated
    resolution_note TEXT,
    suggested_rule JSONB,                     -- auto-fix提案

    -- SLA
    sla_deadline TIMESTAMPTZ,
    sla_met BOOLEAN,

    -- タイムライン
    timeline JSONB DEFAULT '[]',              -- [{timestamp, action, actor, detail}]

    -- タイムスタンプ
    detected_at TIMESTAMPTZ DEFAULT now(),
    responded_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- インデックス
CREATE INDEX idx_incidents_tenant_status ON incidents(tenant_id, status);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_detected_at ON incidents(detected_at);
```

---

## 実装ロードマップ

### Sprint 1: Default Mode（週次レポート）
- [ ] `aigis report weekly` CLIコマンド
- [ ] SecurityMonitor → 週次集計ロジック
- [ ] Markdown/HTML/PDF出力
- [ ] 前週比トレンド計算
- [ ] OWASP カバレッジ統計
- [ ] 推奨アクション自動生成（auto-fix連携）

### Sprint 2: Enterprise Mode基盤
- [ ] Incident モデル + マイグレーション
- [ ] インシデント自動作成（CRITICAL/HIGH検出時）
- [ ] タイムライン自動記録
- [ ] リクエストスナップショット保存
- [ ] 関連イベント自動紐づけ

### Sprint 3: レビュー拡張 + 通知
- [ ] レビュー承認 → リクエスト再実行
- [ ] 許可リスト/ブロックリスト追加アクション
- [ ] 通知ハブ（Slack/メール/Webhook統合）
- [ ] SLA警告通知
- [ ] エスカレーション先設定UI

### Sprint 4: ダッシュボード + レポート配信
- [ ] インシデントカードUI（フロントエンド）
- [ ] インシデント一覧/詳細/タイムライン表示
- [ ] レポート自動配信（cron + メール/Slack）
- [ ] SLA遵守率メトリクス表示

---

## Sources
- [IPA 中小企業のためのセキュリティインシデント対応の手引き](https://www.ipa.go.jp/security/sme/f55m8k0000001wpz-att/outline_guidance_incident.pdf)
- [情シスBlog - セキュリティインシデントの対応フロー](https://biz.techvan.co.jp/tech-is/blog/infra/002463.html)
- [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final)
- [インシデント対応の4ステップ - Codebook](https://codebook.machinarecord.com/info-security/26123/)
- [Incident Response Playbook - Cyberwarzone](https://cyberwarzone.com/2026/03/16/incident-response-playbook-how-to-triage-contain-investigate-and-recover/)
- [インシデント対応フロー総まとめ - Proactive Defense](https://www.proactivedefense.jp/blog/blog-digital-forensics-incident-response/post-2955)
- [FIRST CSIRT Services Framework](https://www.first.org/standards/frameworks/csirts/FIRST_CSIRT_Services_Framework_v2.1.0_bugfix1.pdf)
