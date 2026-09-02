# 2. コントロールマトリクス

本表は、Aigisが実装する各コントロールを、主要なセキュリティ・AIガバナンスフレームワークへ対応付けたものです。ISO/IEC 27001の項番は「証跡を補強するもの（supports evidence for）」として記載しており、Aigisが認証や準拠を保証するものではありません。

**表を読む前に知っておいていただきたい点が2つあります。** 1つ目は、「AI事業者GL v1.2」列のID（`GL-*` / `SEC-*` / `APPI-*`）は**Aigisが独自に定義したもの**で、ガイドライン本文から要件を抽出して番号を振ったものです。ガイドラインの公式項番ではないため、`GL-POISON-01` がガイドラインのどの条項に当たるかという問いには、本リポジトリの外では答えがありません。各IDの要件文は `aigis/compliance.py` に記載しています。2つ目は、本表の対応付けはすべて**自己評価**であり、第三者のレビューを受けていないことです。部分対応・未対応の項目が1件も存在しないため、測定されたカバレッジ率ではなく、「何を実装しているかの表明」として読んでください。

| Aigisコントロール | 概要 | ISO/IEC 27001:2022 附属書A | NIST AI RMF | OWASP LLM Top 10 | AI事業者GL v1.2 |
|---|---|---|---|---|---|
| 入力スキャン（プロンプトインジェクション・ジェイルブレイク・個人情報） | モデルに到達する前に、すべてのプロンプトを正規表現と類似度検知で決定論的に検査します。 | A.8.16 (Monitoring activities), A.5.7 (Threat intelligence) | MEASURE 2.7, MANAGE 2.1 | LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure | GL-POISON-01, SEC-PI-01 |
| 出力スキャン（情報漏洩・秘密情報・個人情報） | モデルの出力を返す前に、秘密情報・個人情報・システムプロンプトの漏洩がないか検査します。 | A.8.12 (Data leakage prevention), A.5.34 (Privacy and PII) | MEASURE 2.7, MANAGE 4.1 | LLM02 Sensitive Information Disclosure, LLM05 Improper Output Handling | APPI-PII-01, GL-DATA-01 |
| ツール呼び出しポリシー強制 | すべてのツール呼び出し（シェル・ファイル・ネットワーク）を実行前に許可/拒否/レビュー判定します。 | A.8.18 (Use of privileged utility programs) | GOVERN 1.1, MANAGE 2.1 | LLM06 Excessive Agency | GL-HUMAN-03 (最小権限), SEC-PRIV-01 |
| MCPツール定義スキャン | Model Context Protocolサーバー定義に含まれるツールポイズニングや定義改ざん（ラグプル）を検出します。 | A.5.21 (ICT supply chain security), A.5.19 (Information security in supplier relationships) | MAP 4.1, MANAGE 3.1 | LLM03 Supply Chain, LLM01 Prompt Injection | GL-SEC-03 (攻撃対象面の管理) |
| メモリ・ファイル書き込みフィルター | 保護対象パス（.env、認証情報、SSH鍵）への書き込みをブロックし、永続化されるエージェントメモリを検査します。 | A.8.3 (Information access restriction), A.8.12 (Data leakage prevention) | MANAGE 2.1, GOVERN 1.4 | LLM06 Excessive Agency, LLM02 Sensitive Information Disclosure | GL-HUMAN-03 (最小権限), GL-DATA-02 |
| 改ざん検知監査ログ（HMAC＋ハッシュチェーン） | 追記専用ログ。各エントリをHMAC-SHA256で署名しハッシュチェーンで連結するため、削除・改ざんを検知できます。 | A.8.15 (Logging), A.8.16 (Monitoring activities), A.5.28 (Collection of evidence) | MEASURE 2.8, MANAGE 4.1 | LLM06 Excessive Agency (logging & monitoring) | GL-AUDIT-01 (追跡可能性), GL-RISK-02 (インシデントDB) |
| SIEM転送（ECS／HTTP） | 任意の非ブロッキング転送機能が、イベントをElastic Common Schema形式でSIEMへ複製します。送信前に個人情報の墨消しを実施します。 | A.8.16 (Monitoring activities), A.5.25 (Assessment of security events) | MEASURE 2.8, MANAGE 4.1 | LLM06 Excessive Agency | GL-HUMAN-04 (継続的モニタリング) |
| 週次セキュリティレポート | スキャン数・ブロック数・OWASPカバレッジ・前週比トレンドを集計した週次レポートを自動生成します。横断的なコントロールであり、他のコントロールを集計するもので、独自のOWASPリスクカテゴリには対応しません。 | A.5.36 (Compliance review), A.8.16 (Monitoring activities) | MEASURE 4.1, GOVERN 4.1 | — | GL-TRANS-01 (ドキュメント化), GL-RISK-02 |

## Aigisが対象としない範囲

正直な範囲設定のため、Aigisが**対象としない**領域を明示します。これらは別の管理策（既存のセキュリティ製品・運用体制）で対応する必要があります。

- モデルの学習・ファインチューニングの安全性 — Aigisはモデルの学習やアライメントを行いません。
- コンテンツモデレーションのポリシー判断 — Aigisはカテゴリを検知しますが、貴社の利用規約（許容利用方針）の定義は行いません。
- ネットワーク層のDLP — ネットワーク境界での外向き通信フィルタリングは、既存のCASB／プロキシの役割です。
- エンドポイントセキュリティ（EDR／アンチウイルス） — Aigisはエージェントを統制しますが、ホスト端末自体は対象外です。
- Claude Code自体のクラウド側処理 — Anthropicへ送信されるプロンプトはAnthropicの規約に従うものであり、Aigisの統制対象外です。
- ID・アクセス管理 — ユーザー認証やSSOは引き続き貴社のIdP（ID基盤）の責任範囲です。
