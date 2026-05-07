---
title: 「Otter.ai が会議終了後も録音してた件、議事録 AI ってもう使えないの？」と聞かれたときの答え方
tags:
  - ai
  - security
  - privacy
  - saas
  - meeting
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

# 「Otter.ai が会議終了後も録音してた件、議事録 AI ってもう使えないの？」と聞かれたときの答え方

先日、社内法務にこう聞かれた。

> 「Otter.ai が会議終了後も**数時間分**録音してた件、ニュースで見たけど、うちが導入検討してた議事録 AI、**結局どうしたらいいの？**」

ニュース見出しが先行して「議事録 AI 全部ダメ」と読めるが、実態はそんなに単純ではない。**訴訟の構成要件**と**AI 機能の中身**を切り分けると、「**何が違法・不適切だったか**」と「**どう作れば構造的にそれを満たさないか**」が綺麗に整理できる。

この記事では、(1) 5 月 20 日に却下申立て聴聞が控える Otter.ai 訴訟と Fireflies.ai の BIPA 訴訟、(2) その先で控える EU AI Act Article 12 ログ要件、(3) 「**ローカル / オンプレで動く議事録 AI**」を構造的に作るときの設計原則、までを書く。最後に Helm（私たちが開発しているセキュア会議 AI SaaS）を含む選択肢で何が違うかを整理する。

---

## TL;DR

- **Otter.ai 訴訟**: 「ホストが Zoom を切ってからも数時間録音した」「**voiceprint** を含む生体情報を**書面同意なし**に取得した」が 2 大論点。連邦 ECPA / カリフォルニア CIPA / イリノイ BIPA。**5/20 motion-to-dismiss** 聴聞。
- **Fireflies.ai 訴訟**: BIPA 違反（voiceprint の同意なし取得）で 2 件係属中。
- **大学の policy ban**: ワシントン大、Chapman 大、UC Riverside で Read AI / Otter 系を **policy で禁止**。
- 解決の方向は 3 つに収束する: ① **会議終了 = 録音停止** をプロトコル仕様レベルで証明、② **voiceprint を作らない / 持たない**、③ **オンプレ・プライベートクラウド配置**で第三者送信を構造的にゼロにする。
- これは「営業トーク」ではなく、**現に米国の訴訟で構成要件として問われている**項目。設計時の must。

---

## 1. 事実の整理 — 何が起きたか

### 1.1 Otter.ai「会議終了後も録音し続けた」

機械学習エンジニア Alex Bilzerian が、ある VC との Zoom 会議の後、Otter から議事録メールを受け取った。会議は予定通りに終了したが、添付された transcript には**会議終了後に数時間分**の録音が含まれていた。その時間帯、画面共有を切ったあとの投資家側で「**戦略的失敗**」「**数字の粉飾（cooked metrics）**」が議論されていた。

この件をきっかけに 4 件の class action が 2025 年 8〜9 月に提起され、現在は **In re Otter.AI Privacy Litigation** に統合済。**5/20 に motion-to-dismiss の聴聞**が予定されている。

訴状で問われている主な構成要件:

- 連邦 **ECPA**: 通信の傍受 / 録音における全当事者同意の不存在
- カリフォルニア **CIPA**: 録音通知の不存在
- イリノイ **BIPA**: voiceprint（声紋）を含む生体情報の**書面同意**なし取得・保存

「全当事者同意（two-party consent）」州では、**会議参加者全員の明示同意**がないと録音が違法になる。Otter の OtterPilot は Zoom / Google Meet にカレンダー連携で**自動参加**するため、招待されたゲストや退室後に会議室に残った人物に対して個別の同意取得フローが構造的に弱かった、というのが原告主張の核。

### 1.2 Fireflies.ai BIPA 訴訟（2026-03-10 提起）

- 参加者の**書面同意なし**に voiceprint を収集・保管したと主張。BIPA は同意取得・保存・破棄ポリシーの**書面公開**を義務化しており、要件が厳しい。
- 現在 **イリノイで 2 件**の class action が係属中。

BIPA は法定損害賠償金が**意図的違反 1 件あたり $5,000、過失 $1,000**。クラスアクション化したとき、対象人数 × 件数で簡単に億単位の請求になる。Facebook の例（$650M で和解）が分かりやすい。

### 1.3 大学の policy ban — ワシントン大 / Chapman / UC Riverside

判決を待たず、運用側が「**禁止**」に走り始めている。情シスの観点では、これは「クラウド型議事録 AI を会議に入れさせるかどうか」の入口判定が、**訴訟確定前に**現場で動き出していることを意味する。

### 1.4 Gartner Peer Community での議論

情シスの主流回答は 3 つ:

1. **検知 → 排除**: Zoom / Teams の Lobby（待機室）で外部 bot を待機させない・拒否する設定をデフォルト化
2. **同意フローのテンプレ化**: 会議冒頭で「録音されています」を全員が確認した記録を残す
3. **オンプレ / ローカル選択肢の評価**: そもそも第三者クラウドへ送らないアーキテクチャに置き換える

---

## 2. 「議事録 AI ってもう使えないの？」への答え方

「議事録 AI」と一括りにすると議論にならない。**3 つの軸**で分類すると、訴訟リスクが構造的に出る組み合わせとそうでない組み合わせが見える。

| 軸 | 安全側 | リスク側 |
|---|---|---|
| 録音停止 | 会議終了とハードに連動（プロトコル証明可能） | カレンダー / アプリ側の挙動依存（バグや UX 不一致がそのまま訴訟リスク） |
| 音声特徴 | テキスト化のみ、**voiceprint は作らない / 即破棄** | 話者識別のために voiceprint を**保存**（BIPA 要件直撃） |
| データ所在 | オンプレ / プライベートクラウド / 端末ローカル | ベンダの共有マルチテナント |

「議事録 AI」を一概にダメと言うのではなく、**「リスク側に 1 つでも該当しているなら、訴訟・規制リスクを取りに行っている自覚を持つ」**が情シス向けの正しい説明。

---

## 3. 設計原則 — 構造的に「訴訟構成要件を満たさない」議事録 AI

### 3.1 録音は会議終了時に**プロトコルで止まる**ことを証明可能に

「停止します」と言うだけでなく、**仕組みとして停止していること**を後から検証できる必要がある。具体的には:

- 会議基盤（Zoom / Meet / Teams）の**会議終了イベント** をフック → 録音プロセスへ SIGTERM
- 録音プロセスは **WAL（Write-Ahead Log）** に終了タイムスタンプを書く
- WAL は**改ざん耐性**のあるストア（append-only S3 + Object Lock など）に置く
- 終了から ε 秒以上 audio フレームが書かれた場合は**監査アラート**

これは「Otter は会議終了後も録音した（と原告が主張する）」という構成要件が、ベンダのコードを見るまでもなく**ログだけで反駁できる**形に持っていく設計。

### 3.2 voiceprint を作らない設計

話者分離（diarization）は voiceprint を作らずにできる。具体的には:

- **クラスタリング**で「話者 A / B / C」を区別するだけにとどめ、各話者ベクトルは**会議終了時に削除**
- 全話者ベクトルを 1 セッション内のみで使い、**永続化しない**
- 「同じ人かどうか」を会議横断で判定する機能は**意図的に持たない**（BIPA の構成要件に直接該当するため）

「同一話者の発言を会議横断でまとめる」価値があるのは事実だが、**それは voiceprint を持つことと等価**。BIPA や CCPA / EU GDPR Article 9（特殊カテゴリ生体データ）に正面から該当するため、**機能を持つ → 同意フロー＋書面ポリシー＋削除手続きを完備する**ことになる。多くの SaaS はそれを満たしていない。

### 3.3 データ所在を「**第三者に送らない**」前提で設計

- 文字起こしモデルは**オンデバイス**（Whisper や類似モデルのローカル実行）か、**顧客テナント内のプライベートクラウド**で実行
- LLM 要約・アクション抽出は**顧客の Azure OpenAI / AWS Bedrock テナント内**に閉じる
- ベンダ側のクラウドを通過しない経路を**デフォルト**にする

これは技術的には Whisper local + Bedrock VPC エンドポイント等で組める。**SaaS としては難しい**が、**プライベート配備 SaaS**（顧客 VPC 内に配備）であれば可能。

### 3.4 同意取得を**会議の冒頭で残せる**フロー

法務がよく要求するが SaaS で実装が薄いのがここ。

- 会議冒頭の最初の発言者に「録音同意 / 拒否」を**音声で確認**
- 拒否者がいた場合、**その発言者の音声区間を transcript から除去**（あるいはそもそも文字起こししない）
- 同意の音声 + タイムスタンプを **separate な audit ストア**に保存

訴訟になったときに「**個別の同意を取った記録がある**」が出せるかどうかで、被告側の戦況が大きく変わる。

---

## 4. EU AI Act Article 12 ログ要件 — 8/2 まで残り 3 ヶ月

訴訟リスクの先には規制執行が控える。EU AI Act の Annex III（高リスク AI）対象の議事録 AI（特に**雇用・面接転記**用途）は、**8/2 から Article 12 のログ要件**が執行可能になる。罰則は **最大 €15M または年間売上 3%**。

要点:

- **自動ログ生成** がライフタイム全期間で可能（マニュアル文書ではダメ）
- **6 ヶ月以上**の保存
- **入力 / 出力 / 意思決定ポイント / タイムスタンプ / 操作者** をすべてキャプチャ
- エージェント挙動を含むなら **ツール呼び出し / 中間ステップ / 全実行パス** も記録

これは「ログ機能を**後付け**する」設計だと到底間に合わない。**最初から各推論呼び出しが構造化ログを吐く**設計にしておく必要がある。実務的には以下のような最小スキーマで十分:

```json
{
  "session_id": "uuid",
  "step": 17,
  "ts": "2026-05-02T10:32:01Z",
  "actor": "diarizer | transcriber | summarizer | tool_caller",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "decision": "speaker=A | redact_pii | tool=calendar.create",
  "policy_version": "1.4.0"
}
```

「入出力そのもの」ではなく「**入出力のハッシュ**」を残せば、PII 漏洩を増やさずに後から再現性検証ができる。再現が必要な場合は**顧客テナント内の暗号化アーカイブ**から復元する 2 段階構成が安全。

---

## 5. ベンダ選定の 5 つの実務質問

法務 / 情シスが議事録 AI ベンダに対して聞くべき質問。**書面で回答が来ないなら採用見送り**で良い。

1. 会議終了タイムスタンプ以降に音声フレームが取得されないことを、**プロトコル仕様**でどう保証していますか？
2. voiceprint（声紋ベクトル）を**保存していますか / していませんか**。していないならその技術的根拠（diarization の方式）を提示してください。
3. データの**所在**: 文字起こし・要約・LLM 推論はそれぞれどのリージョン・どのテナントで実行されますか？
4. **書面同意フロー**を組み込めますか。冒頭の同意確認をログ化して、特定の参加者を transcript から除外できますか？
5. EU AI Act Article 12 ログを **6 ヶ月リテンション**で吐ける構造化ログ機能はありますか？

これら 5 点を満たさないベンダを選ぶことは、**情シスがリスクを引き受けて承認した**ことと同義になる。

---

## 6. ポジショニングとして — Helm の場合

私たちが開発している Helm（セキュア会議 AI SaaS）は、上の 5 つの質問に対して以下を構造的に保証している:

- **会議終了 = 録音停止**: 会議基盤の終了イベントを SIGTERM のトリガーにし、改ざん耐性のある終了タイムスタンプを WAL に残す
- **voiceprint 非保存**: 話者分離はセッション内クラスタリングのみ。会議終了時に話者ベクトルは破棄
- **配置**: 顧客 VPC 内のプライベート配備 SaaS。文字起こしは Whisper / Distil-Whisper オンデバイス、LLM 要約は顧客テナントの Azure OpenAI / Bedrock
- **同意フロー**: 冒頭同意の音声＋タイムスタンプを別 audit ストアに保存。同意拒否者の区間を transcript から除外可能
- **Article 12 ログ**: 構造化ログを 6 ヶ月以上、改ざん耐性ストアに保存。policy_version をすべての推論呼び出しに付与

これらは「営業トーク」ではなく、**現に Otter / Fireflies で問われている構成要件をひとつずつ設計レベルで否定**したもの。

---

## 7. 「5 分で試せるクイックスタート」 — aigis を議事録 AI パイプラインに挟む

Helm のような完成形を待てない人向けに、「**手元の議事録 AI パイプラインを Article 12 互換の構造化ログ + PII フィルタ**で守る」最小構成を OSS で書ける。aigis（OSS LLM ファイアウォール）を使うと 3 行で挟まる。

```bash
pip install pyaigis
```

```python
# minutes_pipeline.py
from aigis import Aigis
from aigis.audit import StructuredLogger

guard = Aigis(profile="meeting")  # 会議用プロファイル: PII redaction + voiceprint 検出
audit = StructuredLogger(sink="s3://my-meetings-audit/", retention_days=180)

def transcribe_step(audio_chunk, session_id):
    # 1) 文字起こし（ローカル Whisper）
    text = local_whisper.transcribe(audio_chunk)

    # 2) aigis でスキャン: PII / 機微情報の自動 redaction
    verdict = guard.scan_text(text, context="meeting_transcript")
    redacted = verdict.redacted_text

    # 3) Article 12 互換の構造化ログ
    audit.log({
        "session_id": session_id,
        "actor": "transcriber",
        "input_hash": guard.hash(audio_chunk),
        "output_hash": guard.hash(redacted),
        "decision": f"redact={len(verdict.redactions)}",
        "policy_version": guard.policy_version,
    })

    return redacted
```

これだけで「PII を会話文から自動マスク」「6 ヶ月の改ざん耐性ログ」「policy バージョンの追跡可能性」までカバーできる。voiceprint を作っていないか確認するのは別レイヤだが、**少なくとも transcript 経路の Article 12 ログ要件は満たせる**スターター。

---

## 8. まとめ

- 「議事録 AI ってもう使えないの？」の答えは「**会議終了で確実に止まる / voiceprint を作らない / 第三者に送らない**を満たすベンダだけ使え」。
- これは構造的に Otter / Fireflies の訴訟構成要件を**そもそも該当させない**設計の型。
- **5/20 の motion-to-dismiss 結果**と **8/2 の EU AI Act Article 12 執行**は連動して効いてくる。残り 3 ヶ月で「ベンダ見直し」と「ログ整備」を並行する必要がある。
- すぐ着手するなら、aigis を議事録パイプラインに 3 行で挟んで、Article 12 互換の構造化ログ + PII redaction を**今週中**に動かしておくのが最小コストの保険になる。

「全部ダメ」でも「全部 OK」でもなく、**設計レベルで構成要件を否定したかどうか**が分水嶺。次に法務に聞かれたら、上の 5 つの質問を提示すると話が早い。

---

## ソース

- UC Today, *Otter.ai Lawsuit: AI Meeting Bot 'Kept Listening' After Call Ended*
- Workplace Privacy Report (2026-04), *AI Meeting Assistants and Biometric Privacy: Governance Lessons from the Fireflies.AI Lawsuit*
- Epstein Becker Green, *AI Meeting Assistants and Biometric Privacy: Lessons from the Fireflies.AI Lawsuit*
- AllAboutLawyer, *Fireflies.AI Lawsuit 2026: Was Your Voice Data Collected?*
- Top Class Actions, *Fireflies.AI sued over alleged unlawful data collection from meeting participants*
- VoIP Review (2026-04-27), *AI Notetakers' Legal Battle - Otter.ai and Industry Impacts*
- Meetily Blog, *Are AI Meeting Assistants Safe? Privacy Risks Exposed (2026 Guide)*
- Gartner Peer Community, *How are you managing the risk of AI transcription bots like otter.ai and fireflies.ai?*
- Help Net Security (2026-04-16), *What the EU AI Act requires for AI agent logging*
- EU Artificial Intelligence Act, *Article 12: Record-Keeping for High-Risk AI Systems*
- Raconteur, *EU AI Act Compliance: a technical audit guide for the 2026 deadline*

---

*Helm（セキュア会議 AI SaaS）は 2026 年 Q3 ベータ公開予定。aigis（OSS LLM セキュリティレイヤー）は GitHub の `aigis-firewall/aigis` で公開中。フィードバック歓迎。*
