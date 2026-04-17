---
title: "セキュリティ製品を作ってるので、自分のコードを自分で監査してみた — Aigis v0.0.4 リリース記"
emoji: "🛡️"
type: "tech"
topics: ["Python", "security", "LLM", "OSS", "AIエージェント"]
published: true
---

# セキュリティ製品を作ってるので、自分のコードを自分で監査してみた

AIエージェント向けOSSファイアウォール [Aigis](https://github.com/killertcell428/aigis) v0.0.4 をリリースしました。

今回のリリースは、1つの **メタな実験** でもあります。

> **「LLMセキュリティ製品を作っている自分が、自分の backend + scanner コードを、AI にセキュリティ監査させたら何が出るか」**

結論: **Critical 4件 / High 5件 / Medium 4件** の計 13件が出ました。さらに GitHub CodeQL からの指摘 7件も並行で処理しました。

本記事では、その監査結果の **一部** を、仕組みと結果つきで共有します。あわせて、2025〜2026年に出た LLMセキュリティ研究論文を 7本 ゼロ依存実装した話も書きます。

---

## 監査から出た代表的な 5 件

### 1. APIキー保存 = 無塩 SHA-256 + `==` 比較（Critical）

```python
# before (backend/app/auth/api_keys.py)
def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()

def verify_api_key(raw: str, stored: str) -> bool:
    return hash_api_key(raw) == stored
```

**何がまずいか**
- 無塩 SHA-256 → DB 漏洩時に rainbow table ですぐ復元される
- `==` 比較 → timing attack で 1 バイトずつリークされる

**直した形:**
```python
def hash_api_key(raw_key: str) -> str:
    return hmac.new(_hmac_key(), raw_key.encode(), hashlib.sha256).hexdigest()

def verify_api_key(raw: str, stored: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw), stored)
```

アプリ秘密鍵から派生した HMAC 鍵を使い、比較は `hmac.compare_digest`。

---

### 2. CORS `"*"` + `allow_credentials=True`（Critical）

```python
# before
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # ← これが悪魔
    allow_methods=["*"],
    allow_headers=["*"],
)
```

仕様違反の組み合わせ。Cookie認証併用なら任意 origin から認証済みリクエストが通る。

**直した形:** `settings.cors_allowed_origins` をカンマ区切りで読む allowlist 化。prod は明示ドメインのみ。

---

### 3. Stripe webhook に冪等性なし（Critical）

Stripe は配信失敗時に再送する。**同じ event id を 2 回処理すると plan が二重適用される**。

**直した形:** `WebhookEvent(event_id UNIQUE)` テーブルを追加し、署名検証直後に INSERT。`IntegrityError` が出たら早期 return。

```python
db.add(WebhookEvent(source="stripe", event_id=event["id"], event_type=event["type"]))
try:
    await db.flush()
except IntegrityError:
    await db.rollback()
    return {"status": "ok", "duplicate": True}
```

---

### 4. Slack webhook に SSRF 防御なし（High）

`tenant.slack_webhook_url` は管理者権限で設定できる。URL 検証なしで `httpx.post` していた。

**攻撃:** 管理者権限奪取 or IDOR 経路で `http://169.254.169.254/latest/meta-data/` 等 AWS instance metadata に POST できる。

**直した形:** `hooks.slack.com` ホワイトリスト + private/loopback/link-local/reserved/multicast 解決の IP を弾く `is_safe_slack_webhook()` を噛ませる。

---

### 5. `custom_rules` の regex に ReDoS 防御なし（High）

テナントが登録した任意 regex を `re.compile` → `re.search` していた。`(a+)+b` のような pattern を食わせると **スキャナ自身が永遠にブロック** する。

さらに `except re.error: continue` で例外を黙殺していたので、**壊れた pattern を大量投入するとサイレントに検知が無効化される**。

**直した形:** `_regex_guard.safe_compile_user_regex()` を新設。

- 2KB を超える pattern、ネスト量指定子 `(a+)+`、数量化された alternation `(a|a)+` を **reject**
- 失敗した rule は `invalid_rule` として matched リストに可視化

```python
for rule in custom_rules:
    compiled = safe_compile_user_regex(rule["pattern"])
    if compiled is None:
        matched.append(MatchedRule(
            rule_id=rule["id"], rule_name=f"INVALID RULE: {rule['name']}",
            category="invalid_rule", score_delta=0, ...
        ))
        continue
    # ... normal scan
```

「攻撃者が壊れた pattern でスキャナを静かに殺す」経路が完全に塞がれた。

---

**他にも 8 件**: JWT algo 固定・claim必須化、`/admin/tenants` の super-admin 認証必須化、SECRET_KEY の production validator、bcrypt rounds=14 明示、confusables 拡張（Armenian/Hebrew/Arabic-Indic digits/Fullwidth/bidi controls）、docs露出制御多層化、などなど。

CodeQL 側からは、過去コミットに残っていた `py/overly-permissive-regex-range` 6件（emoji regex を関数実装に置換）と `py/clear-text-logging-sensitive-data` 1件（seed_demo の API key マスク表示を廃止）も処理。

**全修正後**: aigis core **940/940**, backend **61/61** テストがグリーン。

---

## 並行して、最新論文を 7 本 ゼロ依存実装した

「Aigis はセキュリティ研究のプロダクト化パイプライン」 と位置づけている以上、**ここ半年の LLM 攻撃論文を追いかけないと意味がない**。

v0.0.4 では 7 本の研究論文を、各 1 モジュールずつ、Python 標準ライブラリだけで実装した。

既存の Aigis は 4-Wall (Pattern/Similarity/Encoded/Multi-turn) + L4-L6 (Capability/AEP/Safety) の多層防御。**新モジュールは独立した第 5 セクションに置かず、必ず既存の層に組み込んだ**。「研究のパッチワーク」にならないようにしたかった。

### Wall 1 (Pattern Matching) の拡張

**① `judge_manipulation` カテゴリ — 15 パターン追加**

AdvJudge-Zero (Palo Alto Unit 42, 2026) — 「LLM-as-Judge」に対するファジングが **99% の bypass 率** を達成した研究を受けて、評価者向け攻撃パターンを追加。

例: `always output 'approved'` / `score = 1.0` / `ignore the rubric` / `final answer: safe` / `評価基準を無視` (JA)

aigis は enterprise mode で auxiliary LLM を「判定者」に使うユースケースがある → そこを塞ぐ。

**② MCP scanner を 3-stage 対応に**

MSB benchmark ([arxiv:2510.15994](https://arxiv.org/abs/2510.15994), Oct 2025) は MCP 攻撃を **discovery / invocation / response** の 3 段階に分類した。Aigis はこれまで discovery（tool定義スキャン）だけだった。

```python
# 新API
from aigis.mcp_scanner import scan_invocation, scan_response

# tool 呼び出し時: args に prompt injection が混入していないか
findings = scan_invocation("web_search", {"query": user_input})

# tool 応答時: 戻り値に「agent に再実行させる指示」が混入していないか
findings = scan_response("web_search", tool_output)
```

JSON 構造を再帰的に flatten し、各文字列フィールドに対して既存の scanner を走らせる。puppet 攻撃 / rug pull が runtime で検知できる。

### Wall 2 (Semantic Similarity) の拡張

**③ `fast_screen` — 文字 n-gram ロジスティック回帰**

Mirror Design Pattern ([arxiv:2603.11875](https://arxiv.org/abs/2603.11875), Mar 2026) — 文字 n-gram 線形分類器が大型 LLM より prompt injection 検知で勝る、という研究。Rust 実装を Python stdlib だけで書き直した。

攻撃コーパス / 良性コーパスから trigram の対数尤度比を合成、logistic 圧縮でスコア [0,1] に。**<1ms で first-line triage** ができるので、正規表現スキャンの前段に置ける。

**④ `imitation_detector` — メモリポイズニング対策**

MemoryGraft ([arxiv:2512.16962](https://arxiv.org/abs/2512.16962), Dec 2025) — agent の長期メモリに「system prompt に似た形の experience」を植える攻撃。overt な jailbreak 文言を含まないので従来の content スキャナで漏れる。

Jaccard similarity (char-4-gram) で「系統の声を構造的に模倣した memory 書込」を検出する。

### Wall 3 (Encoded Payload) 強化

confusables 辞書を拡張: Armenian / Hebrew / Arabic-Indic digits / Fullwidth Latin / zero-width & bidi controls。

### Pre-Wall（新設） — 入力構造の強制

**⑤ `structured_query` — StruQ 風の slot 分離**

StruQ ([arxiv:2402.06363](https://arxiv.org/abs/2402.06363)) / LLMail-Inject ([arxiv:2506.09956](https://arxiv.org/abs/2506.09956)) — 「prompt を system/instruction/data の 3 スロットに分離し、data 内に role token が混入していたら拒否」というアプローチ。

```python
msg = StructuredMessage(
    system="You are a careful assistant.",
    instruction="Summarize the article.",
    data=user_provided_document,  # untrusted
)
try:
    prompt = msg.render()  # data に [/INST] や <|system|> があると BoundaryViolation
except BoundaryViolation as e:
    log_and_reject(e.findings)
```

**⑥ `rag_context_filter` — 取得文書の洗浄**

DataFilter ([arxiv:2510.19207](https://arxiv.org/abs/2510.19207)) / RAGDefender ([arxiv:2511.01268](https://arxiv.org/abs/2511.01268)) — 取得済み RAG chunk からの indirect injection 対策。

```python
chunks = [RetrievedChunk(source_id="doc1", text=...), ...]
result = filter_chunks(chunks, policy="strip")  # or "block"
safe_chunks = result.chunks  # 汚染された文がstripされた or chunkごとdropped
```

### L7（新設） — Goal-Conditioned FSM

**⑦ `spec_lang.fsm`**

MI9 ([arxiv:2508.03858](https://arxiv.org/abs/2508.03858), Aug 2025) の FSM conformance が着想源。「agent は `gathering` state のとき `shell:exec` を呼べない、絶対に」を**宣言で表現できる**。

```python
fsm = AgentStateMachine(
    goal="write_report",
    initial_state="planning",
    states={
        "planning": StateRule(name="planning",
            allowed_tools=frozenset({"search", "note"}),
            allowed_transitions=frozenset({"gathering"})),
        "gathering": StateRule(name="gathering",
            allowed_tools=frozenset({"search", "fetch_url"}),
            allowed_transitions=frozenset({"writing"})),
        # ...
    },
    terminal_states=frozenset({"done"}),
)
monitor = FSMMonitor(fsm)
violation = monitor.observe_tool_call("shell:exec")  # FSMViolation(kind="forbidden_tool")
```

既存の `monitor/drift.py` は **統計的な drift** を捕まえる（「いつもと違う」）。FSM は **宣言的な violation** を捕まえる（「やってはいけないと明記したこと」）。この 2 つはセットで成立する。

---

## 設計原則の話: 新機能は既存フレームに組み込む

今回 7 個の研究論文を入れるにあたり、**独立した「Recent Research」セクションを README に作らない** ことを意識した。

「この論文は Wall 1 を拡張する」「この論文は新しい Pre-Wall 層を作る」「この論文は L7 として L4-L6 の隣に並ぶ」——こう書けない機能は、たぶん既存アーキテクチャと噛み合っていないので、実装前に設計を見直すべきだ。

研究の実装コードは溜まっても、**ユーザーにとっての「一枚絵」がブレない** ことが OSS 継続の鍵だと思う。

---

## インストール

```bash
pip install pyaigis==0.0.4
```

ゼロ依存。`pyproject.toml` の `dependencies = []` は変わらず。

全 CHANGELOG: https://github.com/killertcell428/aigis/releases/tag/v0.0.4

---

## おわりに

「セキュリティ製品のセキュリティ」は、製品カテゴリ自体の信頼に直結する。今回 CI の CodeQL を放置せずに向き合ったこと、内部監査で出た 13 件を隠さず CHANGELOG に書いたのは、その意味で意図的だ。

Critical 4件・High 5件出たという事実より、**それを全部公開して直してテストを通したという事実**のほうが、セキュリティOSSとしては価値があると思っている。

GitHub: https://github.com/killertcell428/aigis — ⭐ をいただけると励みになります。
