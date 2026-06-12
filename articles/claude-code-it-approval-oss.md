---
title: "Claude Code、会社で使う許可が下りない — 情シスが「はい」と言うためのOSSを作った"
emoji: "🛡️"
type: "tech"
topics: ["claudecode", "セキュリティ", "AIエージェント", "OSS", "情シス"]
published: false
---

## 「とりあえず個人の判断で使ってください」では済まない

今年に入ってから、社内のエンジニアから「Claude Codeを業務で使ってもいいですか？」という声を聞く機会が増えました。試しに使ってみると生産性の差は歴然です。それでも「はい、どうぞ」とすぐに言えないのが現実で、大抵の場合は情シス・セキュリティ部門の審査が待っています。

私自身も同じ壁に当たりました。「個人PCで使う分には…」という曖昧な運用で数週間凌いでいたのですが、それは根本解決ではありません。審査で止まっているエンジニアが生産性を犠牲にし続けるか、黙って使い続けるシャドーAIに流れるか — どちらも組織にとって良くない。

そこで発想を変えました。**情シスの審査を「突破する」のではなく、審査に正面から答えられる状態を作る**にはどうすればいいか、と。

---

## 情シスの質問は、実は正当だった

審査で聞かれることを整理すると、だいたい次のような内容に収束します。

```
1. このツールは何を「実行」できるのか？
   → シェルコマンド、ファイル書き込み、ネットワーク通信の範囲は？

2. 操作ログはどこに残るのか？
   → ローカルのみか、外部送信されるか？保持期間は？

3. ログの改ざん検知はできるのか？
   → 証拠として使えるか？監査に耐えられるか？

4. どの規格・ガイドラインに対応しているのか？
   → ISO/IEC 27001？NIST AI RMF？OWASP LLM Top 10？
   → 経産省のAI事業者ガイドライン（2024年版）は？

5. インシデントが起きたときの手順は？
   → 誰が何をするのか文書化されているか？

6. 段階的なロールアウト計画はあるのか？
   → パイロット → 部門展開 → 全社展開の手順は？
```

これらはセキュリティ担当者として当然の問いです。「生成AIだから特別に危険」ということではなく、新しいツールを組織に入れるときの標準的なチェック項目です。問題は、Claude Code公式にはこれらに「はい・いいえ」で答える文書が存在しないことでした。

---

## 「口頭説明」ではなく「生成された文書」で答える

情シスへの回答を毎回口頭やスライドで準備するのは属人的で、かつ後から変わってしまいます。それより、**ライブの設定から直接、検証可能な承認パッケージを生成する**ほうが確実です。

これが [Aigis](https://github.com/killertcell428/aigis) の `aigis trust-pack` コマンドを作った動機です。

### インストールと初期化

```bash
# Aigisをインストール
pip install 'pyaigis[all]'

# Claude Codeフックとエンタープライズポリシーを設定
aigis init --agent claude-code --policy enterprise

# 承認パッケージを生成（英語・日本語、HTML形式）
aigis trust-pack --lang both --format html
```

3コマンドで終わります。

### 生成されるファイル

`aigis trust-pack` を実行すると `aigis-trust-pack/` ディレクトリに次のファイルが生成されます。

```
aigis-trust-pack/
├── index.html                    # ナビゲーション付きトップページ
├── executive-summary.ja.md       # 経営層・情シス向けエグゼクティブサマリー
├── executive-summary.en.md       # 英語版
├── control-matrix.md             # コントロールマトリクス（後述）
├── policy-snapshot.yaml          # 現在の aigis-policy.yaml のスナップショット
├── audit-log-spec.md             # 監査ログ仕様（HMAC署名・ハッシュチェーン）
├── incident-runbook.md           # インシデント対応手順書
└── rollout-plan.md               # パイロット→全社展開計画
```

### コントロールマトリクスの中身（抜粋）

コントロールマトリクスは、情シスが「どの規格のどの項目に対応しているか」を一覧で確認できる表です。たとえばこんな形式になります。

```markdown
| 要件 | 参照規格 | Claude Code 第1層 | Aigis 第2層 | 組織責任 |
|------|----------|------------------|-------------|----------|
| アクセス制御 | ISO 27001 A.9, NIST GV-3 | managed-settings.json でコマンド制限 | PreToolUseフックでリアルタイム検査 | [TO FILL] MDMプロファイル配布 |
| 監査ログ | ISO 27001 A.12.4 | OTelエクスポート（テレメトリ相当） | HMAC+ハッシュチェーン署名ログ | [TO FILL] SIEM転送設定 |
| インシデント対応 | OWASP LLM04, 経産省ガイドラインB-3 | — | インシデントRunbook自動生成 | [TO FILL] エスカレーション先 |
```

`[TO FILL]` が残っている箇所は、組織固有の判断が必要な部分です。ここは意図的に埋めていません。

---

## 二層防御の考え方

Aigisは「Claude Codeを危険なツールとして封じ込める」ものではありません。むしろ逆で、**Claude Code自身の制御機能を第1層として評価し、その上に第2層を足す構成**です。

### 第1層：Claude Code managed-settings

Claude CodeのTeam/Enterpriseプランでは `managed-settings.json` をMDM経由で配布できます。これで「どのコマンドを実行できるか」を組織レベルで制限できます。これは強力な第1層です。

### 第2層：Aigisフック + 署名付き監査ログ

`aigis init --agent claude-code` を実行すると `.claude/hooks/aig-guard.py` がインストールされます。Claude Codeが何かツールを実行する**直前**に、このフックがAigisのポリシーエンジンで検査します。

```python
# .claude/hooks/aig-guard.py が自動生成されるイメージ
# Claude Codeのすべての PreToolUse に対して実行される
result = guard.check_tool_call(tool_name, tool_input)
if result.blocked:
    sys.exit(2)  # ツール実行を中断
```

そして、すべての判断結果がHMAC-SHA256署名とSHA-256ハッシュチェーンで保護された監査ログに記録されます。

```bash
# ログの改ざんを検証
aigis audit verify

# → chain_valid: true
# → signature_valid: true
# → 1,247 entries checked, 0 tampering detected
```

このログはSplunk・Datadog・Microsoft Sentinel・Elasticへの転送もサポートしています。

### Claude Code TeamプランのOTelログの限界

Claude Code Enterpriseプランには、OpenTelemetry経由のログエクスポート機能があります。ただし、これは**テレメトリ相当**（運用監視用）であり、改ざん検知機能を持つ監査証跡ではありません（参考: Claude Code公式ドキュメント）。コンプライアンス審査や内部監査で「ログが改ざんされていないことを証明せよ」と求められた場合、OTelログだけでは応えにくい場面があります。Aigisの第2層はこのギャップを埋めます。

---

## MCPツールのリスク：ラグプルとツールポイズニング

Claude Codeと組み合わせて使うMCPサーバーには、別のリスクがあります。サードパーティのMCPツールは「更新によって動作が変わる」可能性があります — これをラグプルと呼びます。また、ツール定義に悪意のある隠し命令が埋め込まれるツールポイズニングも報告されています。

```bash
# MCPツール定義を検査
aigis mcp --file .claude/mcp_tools.json --trust --diff

# → Trust score: 82/100
# → 3 high-risk patterns detected
# → Diff from last snapshot: 2 changes (flagged for review)
```

---

## 正直な限界

Aigisが守備できる範囲と、守備できない範囲を明確にしておきます。

**できること**
- 既知のパターン・ポリシーに基づいた決定論的な検査（$0 API費用、外部依存なし）
- HMAC署名とハッシュチェーンによる改ざん検知可能な監査ログ
- ISO 27001 / NIST AI RMF / OWASP LLM Top 10 / 経産省AI事業者ガイドラインへのマッピング文書自動生成
- SIEM転送（Splunk / Datadog / Microsoft Sentinel / Elastic）

**できないこと**
- Anthropicのクラウド側で起きることの制御（モデル推論はAigisの外）
- 既知パターンに合致しない深層的・新規の攻撃の検知
- 「ISO 27001準拠」の保証 — 生成するのは証跡であり、認証はISMS構築の結果
- 組織ポリシーの策定 — `[TO FILL]` の部分は組織が決める必要があります

Aigisは多層防御の一層です。魔法の解決策ではありません。

---

## CTA：今すぐ試せます

```bash
pip install 'pyaigis[all]'
aigis init --agent claude-code --policy enterprise
aigis trust-pack --lang both --format html
open aigis-trust-pack/index.html
```

GitHubリポジトリ: https://github.com/killertcell428/aigis

承認パッケージの導入ガイドは `docs/adoption/` にあります。フィードバック・Issue・PRはいつでも歓迎です。「この承認プロセスで詰まった」「このフレームワークへのマッピングが欲しい」という声があれば、Issueで教えてください。

もし社内の情シス審査でAigisを使って通過した（あるいは通過できなかった）経験があれば、ぜひコメントで共有していただければ幸いです。同じ課題に詰まっているエンジニアへのヒントになります。
