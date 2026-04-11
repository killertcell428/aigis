"""Japan AI Governance compliance checker.

Maps Aigis capabilities to specific requirements from:
  - AI事業者ガイドライン v1.2 (2026年3月31日)
  - AIセキュリティ技術ガイドライン (総務省 2025年度)
  - AI推進法 (2025年9月施行)
  - 個人情報保護法 (APPI) / マイナンバー法

Usage:
    from aigis.compliance import check_compliance, get_compliance_report

    report = get_compliance_report()
    for item in report:
        print(f"[{item['status']}] {item['requirement']}")
"""

from dataclasses import dataclass


@dataclass
class ComplianceItem:
    """A single regulatory requirement and its compliance status."""

    regulation: str
    requirement_id: str
    requirement: str
    description: str
    aigis_feature: str
    status: str  # "covered" | "partial" | "not_covered" | "user_responsibility"
    notes: str = ""


def get_compliance_report() -> list[dict]:
    """Generate a comprehensive compliance report.

    Returns a list of compliance items showing how Aigis
    maps to each Japanese AI regulatory requirement.
    """
    items = _build_compliance_items()
    return [
        {
            "regulation": item.regulation,
            "requirement_id": item.requirement_id,
            "requirement": item.requirement,
            "description": item.description,
            "aigis_feature": item.aigis_feature,
            "status": item.status,
            "notes": item.notes,
        }
        for item in items
    ]


def get_compliance_summary() -> dict:
    """Get a summary of compliance coverage."""
    items = _build_compliance_items()
    total = len(items)
    covered = sum(1 for i in items if i.status == "covered")
    partial = sum(1 for i in items if i.status == "partial")
    not_covered = sum(1 for i in items if i.status == "not_covered")
    user_resp = sum(1 for i in items if i.status == "user_responsibility")

    return {
        "total_requirements": total,
        "covered": covered,
        "partial": partial,
        "not_covered": not_covered,
        "user_responsibility": user_resp,
        "coverage_rate": round(((covered + partial * 0.5) / total) * 100, 1) if total else 0,
        "by_regulation": _group_by_regulation(items),
    }


def _group_by_regulation(items: list[ComplianceItem]) -> dict:
    groups: dict[str, dict] = {}
    for item in items:
        if item.regulation not in groups:
            groups[item.regulation] = {"total": 0, "covered": 0, "partial": 0, "not_covered": 0}
        groups[item.regulation]["total"] += 1
        if item.status in ("covered", "partial", "not_covered"):
            groups[item.regulation][item.status] += 1
    return groups


def _build_compliance_items() -> list[ComplianceItem]:
    return [
        # ================================================================
        # AI事業者ガイドライン v1.2 (2026年3月31日 総務省・経済産業省)
        # ================================================================
        #
        # --- 原則: セキュリティ ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-SEC-01",
            requirement="設計段階からのセキュリティ組み込み",
            description="AIシステムの設計段階からセキュリティを練り込む（Security by Design）。",
            aigis_feature="プロキシ型アーキテクチャにより、既存LLMアプリに後付けでセキュリティを追加可能。64+検知パターン。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-SEC-02",
            requirement="脆弱性情報収集と迅速なパッチ配布",
            description="脆弱性情報を収集し、迅速にパッチを配布する体制を構築。",
            aigis_feature="OWASP LLM Top 10分類により既知の脆弱性カテゴリをカバー。パターン更新はSDKバージョンアップで配布。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-SEC-03",
            requirement="AIエージェントの攻撃対象面(Attack Surface)の管理",
            description="v1.2新規: 複雑なAIシステムが多様な情報を処理することで攻撃対象が拡大するリスクへの対策。エージェントが接続する外部ツール・API・データソースごとのリスク評価。",
            aigis_feature="Policy Engineで操作ごとの権限を制御（allow/deny/review）。scan_rag_context()でRAG検索結果をスキャン。Claude Code Adapterがtool_name/tool_inputを構造的に解析し、ツール接続ごとにセキュリティスキャンを実施。",
            status="covered",
        ),
        #
        # --- 原則: リスク管理 ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RISK-01",
            requirement="リスクベースアプローチによる対策の優先順位付け",
            description="v1.2強化: リスクをゼロにするのではなく、危害の大きさと発生確率を踏まえて対策の優先順位を決定。過度な対策によるイノベーション阻害を防ぐ。",
            aigis_feature="リスクスコアリング（0-100）で各リクエストの危険度を定量評価。Low/Medium/High/Criticalの4段階。カテゴリ別逓減方式でノイズ耐性を確保。ポリシーでしきい値をカスタマイズ可能（strict/default/permissive）。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RISK-02",
            requirement="ヒヤリ・ハット情報とインシデントDB",
            description="ヒヤリ・ハット情報とインシデントデータベースを調査・蓄積。",
            aigis_feature="監査ログに全リクエスト・判定・レビュー結果を記録。コンプライアンスレポートで集計。alertsログで重大イベントを永続保存。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RISK-03",
            requirement="自律的行動による意図しない動作リスクへの対策",
            description="v1.2新規: AIエージェントの自律行動によるハルシネーション起因の誤動作（不正な購入、ファイル削除等の意図しないアクション実行）への対策。",
            aigis_feature="ハルシネーション起因アクション検知パターン（hallucination_action）。Human-in-the-Loopレビューキュー。Policy Engineで破壊的操作（rm -rf, DROP TABLE, force push等）をデフォルトブロック。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RISK-04",
            requirement="合成コンテンツ・フェイク情報のリスク管理",
            description="v1.2新規: AI生成の合成コンテンツ（ディープフェイク等）やフェイク情報の生成・拡散リスクへの対策。",
            aigis_feature="合成コンテンツ生成要求の検知パターン（synthetic_content）。ディープフェイク・偽情報生成の指示を検出し警告。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RISK-05",
            requirement="AIへの過度依存・フィルターバブルの防止",
            description="v1.2新規: AIへの過度依存やフィルターバブルによる判断力低下のリスク。人間の主体的関与を維持する設計。",
            aigis_feature="過度依存検知パターン（over_reliance）。Human-in-the-Loopで重要判断に人間の承認を要求。Activity Streamで人間の関与率を可視化。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RISK-06",
            requirement="アルゴリズムによる感情操作の防止",
            description="v1.2新規: AIによるユーザーの感情操作・心理操作のリスクへの対策。",
            aigis_feature="感情操作検知パターン（emotional_manipulation）。ユーザーの心理的脆弱性を悪用する出力を検出。",
            status="covered",
        ),
        #
        # --- 原則: 透明性 ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-TRANS-01",
            requirement="モデルの更新履歴と評価結果のドキュメント化",
            description="更新履歴と評価結果を文書化し、再検証可能な状態を維持。",
            aigis_feature="Activity Streamで全エージェント操作を自動記録（JSONL）。グローバル集約で全プロジェクト横断の履歴を管理。CSV/Excelエクスポートで監査対応。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-TRANS-02",
            requirement="モデルの能力と限界の開示",
            description="モデルの能力と限界を利用者に開示。営業秘密とのバランスを取りつつ、合理的な範囲で必要な情報を提供。",
            aigis_feature="修復ヒントで各検知ルールのOWASP参照・修復方法を提供。レポートでカバー範囲を明示。aig statusで現在のガバナンス状態を可視化。",
            status="covered",
        ),
        #
        # --- 原則: 人間中心・人間の関与 ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-HUMAN-01",
            requirement="AIエージェントの外部アクション実行時のHuman-in-the-Loop",
            description="v1.2強化: AIエージェントが外部に対してアクションを実行する場合、クリティカルな意思決定ポイントでの人間の承認メカニズムを必須化。",
            aigis_feature="Human-in-the-Loop（レビューキュー）。Medium/Highリスクは自動でキューへ。SLAタイムアウト+フォールバック。Claude Code AdapterのPreToolUse hookで外部ツール実行前にスキャン。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-HUMAN-02",
            requirement="緊急停止メカニズムの実装",
            description="v1.2新規: AIエージェントの誤動作時に即座に停止できるメカニズムの実装。",
            aigis_feature="Policy Engineのauto_block_thresholdでCRITICALリスクを即時ブロック。Activity Streamのalertsログで異常を即座に検知。Slack通知でリアルタイムアラート。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-HUMAN-03",
            requirement="最小権限の原則の適用",
            description="v1.2新規: AIエージェントに付与する権限を必要最小限に制限。",
            aigis_feature="Policy Engineで操作ごとの権限を制御（allow/deny/review）。デフォルトポリシーでsudo/rm -rf/force pushをブロック。.env/.ssh/credentialsへのアクセスを制限。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-HUMAN-04",
            requirement="継続的モニタリングインフラの整備",
            description="v1.2新規: AIエージェントの動作を継続的にモニタリングするインフラの構築。",
            aigis_feature="Activity Streamの3層アーキテクチャ（ローカル/グローバル/アラート）。Cloud Dashboardでリアルタイム可視化。使用量メーター+警告。データ保存自動クリーンアップ。",
            status="covered",
        ),
        #
        # --- 原則: プライバシー保護 ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-DATA-01",
            requirement="個人情報保護法を踏まえた設計と運用",
            description="プライバシー・バイ・デザインによる対応。",
            aigis_feature="PII検知（日本語+国際）15パターン。自動サニタイズ（sanitize()）でPIIを墨消し。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-DATA-02",
            requirement="データリネージ・トレーサビリティの整備",
            description="v1.2強化: データパイプライン全体を通じたトレーサビリティの確保。監査ログの維持、インシデント調査のための記録保持。",
            aigis_feature="Activity Streamで全ファイルアクセス（file:read/write）を記録。scan_rag_context()でRAG検索結果をスキャン。操作の来歴をタイムスタンプ+セッション+ユーザーで追跡可能。delegation_chainフィールドでエージェント間の委任関係を追跡。",
            status="covered",
        ),
        #
        # --- 原則: アカウンタビリティ ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-AUDIT-01",
            requirement="学習過程とアルゴリズム選定の追跡可能性",
            description="第三者による追跡可能性を確保。変更管理ログの維持。",
            aigis_feature="監査ログ100%記録。全リクエスト・判定・レビュー結果・ポリシー変更を不変ログとして保存。",
            status="covered",
        ),
        #
        # --- v1.2 新規: AIエージェント・エージェンティックAI ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-AGENT-01",
            requirement="AIエージェントの定義と管理",
            description="v1.2新規: 特定の目標を達成するために環境を感知して自律的に行動するAIシステム（AIエージェント）の適切な管理。エージェントの行動範囲・権限の明確化。",
            aigis_feature="Claude Code Adapter / LangGraph GuardNode / OpenAI Proxy / Anthropic Proxyで各種エージェントフレームワークに対応。Policy Engineでエージェントの行動範囲を制御。Activity Streamのagent_type/autonomy_levelフィールドでエージェント種別・自律度を記録。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-AGENT-02",
            requirement="エージェンティックAI（マルチエージェント連携）の安全設計",
            description="v1.2新規: 複数のAIエージェントが自律的に連携するシステムにおける安全設計。委任チェーンの追跡、権限の伝搬管理。",
            aigis_feature="Activity Streamのdelegation_chainフィールドでエージェント間の委任関係を追跡。LangGraph GuardNodeでグラフ内の各ノード間にガードレールを挿入可能。Policy Engineの条件（conditions）でautonomy_levelに基づく制御。",
            status="covered",
        ),
        #
        # --- v1.2 新規: 責任範囲の拡大 ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RESP-01",
            requirement="RAG構築・ファインチューニング時の開発者責任",
            description="v1.2新規: 社内データでRAGを構築、既存モデルのファインチューニング、AIエージェントへの独自ツール接続を行う場合、従来「利用者」だった企業にも「開発者」としての責任が発生。",
            aigis_feature="scan_rag_context()でRAG検索結果に含まれる攻撃・PII・機密情報を検出。Policy EngineのカスタムYAMLルールでRAGパイプライン固有のリスクを制御。コンプライアンスレポートで開発者/提供者/利用者の各責任範囲を明示。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-RESP-02",
            requirement="RAG・システムプロンプトの安全設計",
            description="v1.2新規: RAGの実装やシステムプロンプトの安全設計がAI提供者の責任として整理。間接プロンプトインジェクションへの対策。",
            aigis_feature="間接PI: scan_rag_context()でRAGコンテキストスキャン。システムプロンプト漏洩検知（7パターン）。SEC-PI-02準拠の入力構造的分離。check_messages()でsystem/user/assistantロールを構造的に解析。",
            status="covered",
        ),
        #
        # --- v1.2 新規: 攻めのガバナンス ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-GOV-01",
            requirement="攻めのガバナンスの実践",
            description="v1.2新規: 単なる制限的な規制ではなく、プロアクティブに運用基準を確立する「攻めのガバナンス」。イノベーションを促進しつつリスクを管理。",
            aigis_feature="3段階ポリシー（strict/default/permissive）+カスタムYAMLで組織のリスク許容度に応じた柔軟な設定。業種別ポリシーテンプレート（7種）。aig benchmarkで検出精度を定量測定。リスクベースの段階的対応（ブロック/レビュー/許可）。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-GOV-02",
            requirement="活用の手引きに基づく段階的導入",
            description="v1.2新規: AI ガバナンスに初めて取り組む企業・中小企業向けの「活用の手引き」に基づく段階的な導入支援。",
            aigis_feature="aig init / aig doctorで段階的な導入を支援。ゼロ依存設計で小規模チームでも即座に導入可能。docs/getting-started.mdで5分導入ガイドを提供。",
            status="covered",
        ),
        #
        # --- v1.2 新規: データ汚染・プロンプトインジェクション ---
        ComplianceItem(
            regulation="AI事業者ガイドライン v1.2",
            requirement_id="GL-POISON-01",
            requirement="データ汚染・悪意あるプロンプトインジェクションへの対策",
            description="v1.2新規: 学習データや推論時のRAGコンテキストに対するデータ汚染（Data Poisoning）および悪意あるプロンプトインジェクションへの対策。",
            aigis_feature="直接PI: 正規表現(EN12+JA6パターン)+類似度検知(40+フレーズ)。間接PI: scan_rag_context()でRAGコンテキストスキャン。3層防御: Layer 1(正規表現64+パターン) → Layer 2(類似度検知) → Layer 3(Human-in-the-Loop)。",
            status="covered",
        ),
        #
        # ================================================================
        # AIセキュリティ技術ガイドライン（総務省）
        # ================================================================
        ComplianceItem(
            regulation="AIセキュリティ技術ガイドライン（総務省）",
            requirement_id="SEC-ML-01",
            requirement="多層防御の実装",
            description="学習段階、推論段階、周辺システムでの分業と冗長化。",
            aigis_feature="3層防御: Layer 1(正規表現64+パターン) → Layer 2(類似度検知40フレーズ) → Layer 3(Human-in-the-Loop)",
            status="covered",
        ),
        ComplianceItem(
            regulation="AIセキュリティ技術ガイドライン（総務省）",
            requirement_id="SEC-PI-01",
            requirement="プロンプトインジェクション対策",
            description="直接/間接プロンプトインジェクション攻撃への技術的対策。",
            aigis_feature="直接PI: 正規表現(EN12+JA6パターン)+類似度検知。間接PI: scan_rag_context()でRAGコンテキストスキャン。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AIセキュリティ技術ガイドライン（総務省）",
            requirement_id="SEC-PI-02",
            requirement="入力の構造的分離（タグ付け）",
            description="ユーザー入力とシステム命令を構造的に分離するタグ付け。",
            aigis_feature="Claude Code Adapterがtool_name/tool_inputを構造的に解析し、ユーザー入力とシステム操作を自動分離。PreToolUse hookでJSON構造化データとして入力を受取り、action/targetに分類してからスキャン。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AIセキュリティ技術ガイドライン（総務省）",
            requirement_id="SEC-GUARD-01",
            requirement="ガードレール実装（入出力検証）",
            description="別のAIやフィルタで入出力をチェックする仕組み。",
            aigis_feature="入力フィルター(57パターン) + 出力フィルター(7パターン)。独立したフィルタリングレイヤーとして機能。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AIセキュリティ技術ガイドライン（総務省）",
            requirement_id="SEC-HUMAN-01",
            requirement="重要な操作への人間の承認",
            description="重要な操作（ファイル削除等）の前に人間の確認プロセスを挟む。",
            aigis_feature="Human-in-the-Loopレビューキュー。Medium/Highリスクは人間の承認が必要。SLAタイムアウトでフォールバック。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AIセキュリティ技術ガイドライン（総務省）",
            requirement_id="SEC-PRIV-01",
            requirement="最小権限の原則",
            description="AIに管理者権限を付与しない。データベース接続は読み取り専用に限定。",
            aigis_feature="Policy Engineで操作ごとの権限を制御（allow/deny/review）。デフォルトポリシーでsudo/rm -rf/force pushをブロック。.env/.ssh/credentialsへのアクセスを制限。エージェントの権限を最小限に強制。",
            status="covered",
        ),
        #
        # ================================================================
        # AI推進法（2025年9月施行）
        # ================================================================
        ComplianceItem(
            regulation="AI推進法（2025年9月施行）",
            requirement_id="ACT-COOP-01",
            requirement="国の施策への協力努力義務",
            description="AI活用事業者は国や自治体の施策に協力する努力義務。",
            aigis_feature="コンプライアンスレポートにより、ガバナンス体制の構築を証明。AI事業者ガイドラインv1.2の全要件をマッピング。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI推進法（2025年9月施行）",
            requirement_id="ACT-TRANS-01",
            requirement="透明性の確保",
            description="AIの利用における透明性確保。",
            aigis_feature="監査ログ（100%記録）+ コンプライアンスレポート（OWASP/CWEカバレッジ付き）。",
            status="covered",
        ),
        ComplianceItem(
            regulation="AI推進法（2025年9月施行）",
            requirement_id="ACT-HUMAN-01",
            requirement="人間の関与の確保",
            description="人間の尊厳を守るための人間の関与。",
            aigis_feature="Human-in-the-Loop設計。「AIは検知し、人間が判断する」の原則。v1.2のHITL必須化要件に完全対応。",
            status="covered",
        ),
        #
        # ================================================================
        # 個人情報保護法 (APPI) / マイナンバー法
        # ================================================================
        ComplianceItem(
            regulation="個人情報保護法 / マイナンバー法",
            requirement_id="APPI-PII-01",
            requirement="個人データの安全管理措置",
            description="個人データの漏洩防止のための安全管理措置を講じる。",
            aigis_feature="PII検知（入力15パターン+出力7パターン）+ 自動サニタイズ（sanitize()）で送信前に墨消し。",
            status="covered",
        ),
        ComplianceItem(
            regulation="個人情報保護法 / マイナンバー法",
            requirement_id="APPI-MN-01",
            requirement="特定個人情報（マイナンバー）の適正な取扱い",
            description="マイナンバーの漏洩は刑事罰対象。収集・保管・利用・廃棄を厳格管理。",
            aigis_feature="マイナンバー（12桁）の入力・出力検知。全角数字・ハイフン区切りも正規化して検知。自動墨消し対応。",
            status="covered",
        ),
        ComplianceItem(
            regulation="個人情報保護法 / マイナンバー法",
            requirement_id="APPI-LOG-01",
            requirement="個人データ取扱いの記録",
            description="個人データの取扱い記録を作成・保存。",
            aigis_feature="監査ログにPII検知イベントを記録。検知パターン・リスクスコア・判定結果を保存。",
            status="covered",
        ),
        #
        # ================================================================
        # 不正競争防止法
        # ================================================================
        ComplianceItem(
            regulation="不正競争防止法",
            requirement_id="UCP-TS-01",
            requirement="営業秘密の秘密管理性の維持",
            description="営業秘密をLLMに送信すると秘密管理性が失われるリスク。",
            aigis_feature="営業秘密マーカー検知（「営業秘密」「NDA」「限定提供データ」等）。検知時に修復ヒント提供。",
            status="covered",
        ),
        #
        # ================================================================
        # 著作権法
        # ================================================================
        ComplianceItem(
            regulation="著作権法",
            requirement_id="CR-01",
            requirement="著作物の不正利用防止",
            description="著作物の全文生成・大量引用は著作権侵害のリスク。",
            aigis_feature="著作物全文コピー要求の検知パターン+修復ヒントで出典明記と要約利用を推奨。Activity Streamで全LLMプロンプトを記録し、著作権関連リクエストの事後監査が可能。Policy Engineで著作権リスクの高い操作をreview対象に設定可能。",
            status="covered",
            notes="著作権侵害の最終判断は法的判断であるが、検知・警告・記録・レビューフローの技術的基盤は完備。",
        ),
    ]
