---
title: "「議事録AIって安全なの？」と上司に聞かれたときの技術的な答え方"
emoji: "🎙️"
type: "tech"
topics: ["Python", "security", "LLM", "privacy", "AIエージェント"]
published: false
---

# 「議事録AIって安全なの？」と上司に聞かれたときの技術的な答え方

先週、プロダクトの全社キックオフで議事録 AI（Otter 系、Fireflies 系、Gemini Notes、各社あり）を導入するかの議論があった。情シスから「セキュリティ的にどうなの」と振られて数秒固まった。

「たぶん大丈夫です」で済ませられない問いなので、きちんと答えるための材料を 1 つにまとめた。本稿は、エンジニアが 15 分の雑談で上司 / 役員 / 情シスに技術的な根拠込みで返せるようになることを目標にしている。

## TL;DR

- 2026 年 4 月、**Fireflies.AI に対する集団訴訟** が提起された。原告は **「Fireflies のアカウントを作ったことも ToS に同意したことも、声紋収集に同意したこともない」** 側の参加者。イリノイ州 BIPA を根拠にしている。
- 医療現場では **自動参加した議事録 AI が、患者情報を含むサマリをメーリングリスト全員に配信してしまった事案**も報告されている。
- 「議事録 AI って安全なの？」という問いは実は **5 つの設計判断の合成**。先に判断を言語化すれば、導入可否は後から自然に決まる。
- 5 項目のうち **同意・保存先・配信範囲** は運用で解ける。**バイオメトリクス（声紋）・機微度** は技術で解かないと再現性が出ない。
- 本稿はその 5 項目の中身と、機微度判定 / 同意撤回ロールバック / PII レダクションの実装方針を示す。末尾にはこれをまとめて実装している OSS を 1 つだけ紹介する。

---

## 1. 上司の真の質問を 5 つに分解する

「議事録 AI って安全なの？」は実は次の 5 つの合成質問である。

1. **同意**: 会議参加者全員が、録音・文字起こし・AI 処理に同意したか？
2. **バイオメトリクス**: 音声（= 声紋）は BIPA / GDPR 上の「生体情報」に該当しないか？
3. **データ所在**: 文字起こしは誰のクラウドに保存されるのか。国外か、自社 VPC か、SaaS の共有テナントか。
4. **機微度**: 会議内容に PHI（医療）/ PII / 給与 / M&A / 人事が混入していないか。混入した場合どう扱うか。
5. **配信範囲**: サマリが誰に自動配信されるか。配信先がその機微度を保持できるクリアランスを持つか。

エンジニアが上司に返すべき第一声は **「安全 or 危険ではなくて、この 5 項目を先に決めると安全も危険も自動で決まります」** と置き換えること。「使う / 使わない」の二択を、5 つの判断に広げることで、会話が具体化する。

## 2. 2026 年春に実際に起きていること

### 2.1 Fireflies.AI 集団訴訟（2026-04）

公開されている訴状の要点は次の通り。

- 原告は **Fireflies のユーザーではない**。会議主催者が呼んだ自動参加 bot に声を捕捉された側の参加者。
- イリノイ州 **BIPA (Biometric Information Privacy Act)** は、生体情報の取得前に **書面同意** と **保持・破棄ポリシーの開示** を要求する。
- 原告は「書面同意を求められた事実がなく、保持期間も知らされていない」と主張。
- 類似の構造は **GDPR 第 9 条（特別カテゴリのデータ）** でも成立しうる。EU で会議を開く多国籍企業にとって対岸の火事ではない。

出典: Workplace Privacy Report (Jackson Lewis), 2026-04。

**技術的な教訓**: 「bot が会議に参加した時点で、参加者全員の声紋が取得される可能性がある」という前提で考える。同意取得は主催者が行うだけでは不十分で、**参加者一人一人が同意している状態** を記録できなければ、BIPA / GDPR のラインを越える可能性がある。

### 2.2 医療ミーティングでの PHI 誤配信

具体名は伏せるが、北米の医療機関で **自動参加した note-taker が議事録を患者向けニュースレター登録者全員に配信してしまった** という事案が報告されている。経路は単純で、

- 主催者が会議招待を「マーケ用 ML と同じリスト」で回した。
- note-taker は招待リスト = 配信先と解釈した。
- サマリには患者 ID と具体的な症例が含まれていた。

**技術的な教訓**: AI 自動配信は **人間の目を通さない分、事故の発見が遅れる**。配信前にサマリの機微度を判定するゲートが必要。

### 2.3 Chat App の大規模漏洩（参考）

Fireflies とは別件だが、2026 年 2 月に "Chat & Ask AI" の Firebase 設定不備で **3 億件のメッセージ / 2,500 万ユーザー分** が漏洩した事例が報告されている（Malwarebytes）。**会話ログは企業にとって新しい PII**、という構図が 2026 年に入ってから明確になっている。議事録は会話ログの一種である。

## 3. 5 項目を技術でどう埋めるか

### 3.1 同意 — 運用で解く

- 会議招待メール本文にテンプレの同意条項を埋める。
- 会議冒頭 15 秒で口頭アナウンス。
- 加えて、**「後から撤回したい」場合の経路を設ける**（Slack へ DM、等）。

### 3.2 バイオメトリクス — 声紋保存の有無を契約で切る

- SaaS ベンダーと契約する前に **「speaker diarization のための voiceprint を生成するか」「生成した場合どこに保存するか、保持期間はどのくらいか」** を確認。
- 生成する場合は BIPA 的に NG の可能性が高い。**生成しないベンダーを選ぶか、自社 VPC でのみ生成するオプションを取る**。

### 3.3 データ所在 — リージョン要件で切る

- 多くの SaaS は既定で米国保存。国内データレジデンシー要件がある場合は、**国内保存 / 専用テナント / VPC エンドポイント** のオプションがあるベンダーに絞る。
- on-prem / self-host 可能な OSS は選択肢の 1 つ。

### 3.4 機微度 — 技術で解く

ここが本稿のメインテーマ。「会議の内容の機微度を、サマリ生成前に判定する」仕組みを差し込む。

#### 判定対象の 4 段階

| レベル | 例 | 扱い |
|---|---|---|
| `public` | 挨拶、スケジュール調整 | 制約なし |
| `internal` | メール / 電話 / 顧客名 / 社内ロードマップ | 社外共有禁止 |
| `confidential` | 給与、解雇、M&A、営業秘密 | 役員・該当部門のみ |
| `regulated` | マイナンバー、PHI、クレカ、声紋 | 法定の保管・破棄ルール |

#### 判定ロジック

```python
import re

REGULATED = [
    re.compile(r"(患者|診断|処方|カルテ|医療記録)"),
    re.compile(r"\bpatient|PHI|HIPAA|medical\s+record\b", re.I),
    re.compile(r"(クレジットカード|カード番号|CVV)"),
    re.compile(r"(声紋|生体認証)"),
]
CONFIDENTIAL = [
    re.compile(r"(給与|年収|賞与|解雇|リストラ|人事評価)"),
    re.compile(r"\bsalary|compensation|layoff|severance\b", re.I),
    re.compile(r"(M&A|買収|合併|機密保持|社外秘)"),
]
PII = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    "phone_jp": re.compile(r"\b0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{4}\b"),
    "mynumber": re.compile(r"(?<!\d)\d{12}(?!\d)"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
}

def classify(text: str) -> str:
    if any(p.search(text) for p in REGULATED):
        return "regulated"
    if any(p.search(text) for p in CONFIDENTIAL):
        return "confidential"
    if any(p.search(text) for p in PII.values()):
        return "internal"
    return "public"
```

**ポイント**: 判定は **セグメント（話者 + タイムスタンプ + 発言）単位**でやる。会議全体を単一のレベルに押し込むと、「5 分間だけ CFO が年収を話したせいで全体が confidential になり共有できない」というレバー折れが起きる。粒度を下げて、問題の 5 分間だけ除外できる形にする。

### 3.5 配信範囲 — クリアランスゲート

セグメントごとに機微度が出たら、配信前のゲートは 1 行：

```python
def safe_to_summarize(overall: str, target_clearance: str) -> bool:
    order = ["public", "internal", "confidential", "regulated"]
    return order.index(overall) <= order.index(target_clearance)

if not safe_to_summarize(meeting_overall, target_clearance="internal"):
    raise RuntimeError(f"この会議は {meeting_overall}。internal 配信先には流せません。")
```

## 4. 忘れがちな論点: 同意撤回ロールバック

BIPA / GDPR 的に一番よく刺さるのは、**「誰かが途中で『録音しないでください』と言ったのに、その直前の発言まで保存されている」** ケース。

設計の原則：

1. 撤回表現を検出（"please stop recording", "録音しないでください", "議事録に残さないで" 等）。
2. 撤回発言の **直前 N 秒（10-15 秒）** まで遡って `consent_flag` を立てる。
3. `consent_flag` が立ったセグメントはサマリ生成の入力に入れない、かつ保存から削除する。

擬似コード：

```python
CONSENT_RE = re.compile(
    r"(録音(しないで|をやめて|を停止)|議事録に残さないで|同意していません|"
    r"stop\s+recording|don'?t\s+record\s+me|i\s+do\s+not\s+consent)",
    re.IGNORECASE,
)

def apply_consent_lookback(segments, lookback_sec=15):
    flags = [bool(CONSENT_RE.search(s.text)) for s in segments]
    for i, flagged in enumerate(flags):
        if not flagged:
            continue
        cutoff = segments[i].ts - lookback_sec
        for j in range(i - 1, -1, -1):
            if segments[j].ts < cutoff:
                break
            flags[j] = True
    return flags
```

これだけで、発見遅れによる「意図せず記録された数秒」をポリシー的に切り落とせる。

## 5. PII の非破壊レダクション

メール・電話・マイナンバー・クレカなどの PII は、**サマリに出すときは置換し、原文はマッピング表で別管理** するのが鉄板。

```python
def redact(text: str) -> tuple[str, dict[str, str]]:
    mapping = {}
    def _sub(kind):
        def inner(m):
            token = f"[REDACTED_{kind.upper()}_{len(mapping)+1}]"
            mapping[token] = m.group(0)
            return token
        return inner
    out = text
    for kind, pat in PII.items():
        out = pat.sub(_sub(kind), out)
    return out, mapping
```

サマリは redact 済みで出す、監査ログには原文 + `mapping` を暗号化保存、という形にする。BIPA / GDPR / EU AI Act Art. 26（deployer logging）のどれに対しても「出したもの」と「元データ」を分離しておく運用が効く。

## 6. 上司に返す 1 ページサマリ

以上を踏まえて、会議の場で上司に返せる 1 枚の表：

| 質問 | 推奨デフォルト | 根拠 |
|---|---|---|
| 誰の同意を取るか | 会議招待 + 冒頭口頭、両方 | BIPA / GDPR |
| 声紋は保存するか | しない（NG ベンダーは除外） | Fireflies 訴訟のリスク |
| データ所在 | 国内 or 自社 VPC。SaaS 既定保存は禁止 | データレジデンシー |
| 機微度の扱い | セグメント単位で 4 段階分類 | 医療 PHI 誤配信事例 |
| 配信範囲 | 機微度 → 配信先クリアランスを対応表で固定 | 事故予防 |

「便利だから入れる」でも「怖いから禁止」でもなく、**5 つの設計判断を先に文章化して、技術でコード化する**。これが 2026 年春の時点で返せる最も誠実な答え。

## 7. 実装を端折るなら（参考 OSS）

上の 3.4 / 3.5 / 4 / 5 を **ゼロ依存 Python で書いた OSS** として [aigis](https://github.com/killertcell428/aigis) を公開している（MIT ライセンス）。今回書いたロジックが `aigis.filters.meeting_transcript` にほぼそのまま入っている。

```bash
pip install aigis
```

```python
from aigis.filters.meeting_transcript import (
    Segment, classify_transcript, safe_to_summarise,
)

segments = load_from_your_bot()  # [(speaker, ts, text), ...]
report = classify_transcript(
    [Segment(speaker=s, ts=t, text=x) for s, t, x in segments],
    redact=True,
)

assert safe_to_summarise(report, target_clearance="internal")

summariser_input = [
    s for s, c in zip(report.redacted_segments, report.classifications)
    if not c.consent_flag
]
```

日本語の同意撤回表現（`録音しないで`, `議事録に残さないで`, `同意していません`）、マイナンバー、日本のパスポート番号などは最初から検知対象に入れてある。

もちろん LLM Guard、Presidio、Guardrails AI など既存 OSS でも同じ機能は部分的に実装できる。**重要なのはツールではなく、5 項目のうちどれを自分のアーキテクチャで埋めているかを説明できる状態にしておくこと**。

---

参考:
- Workplace Privacy Report (Jackson Lewis), "AI Meeting Assistants And Biometric Privacy" (2026-04)
- Medium, "Your AI Meeting Assistant Might Be the Biggest Security Risk in Your Office" (2026-04)
- Malwarebytes, "AI chat app leak exposes 300 million messages" (2026-02)
- Privacy Guides, "Data Breach Roundup Apr 3–9, 2026"
- BIPA (740 ILCS 14), GDPR Article 9
