"""Tests for aigis.compliance module."""

from aigis.compliance import (
    ComplianceItem,
    get_compliance_report,
    get_compliance_summary,
    _build_compliance_items,
    _group_by_regulation,
)


class TestComplianceItem:
    def test_dataclass_fields(self):
        item = ComplianceItem(
            regulation="Test Reg",
            requirement_id="T-01",
            requirement="Test requirement",
            description="Test description",
            aigis_feature="Test feature",
            status="covered",
        )
        assert item.regulation == "Test Reg"
        assert item.requirement_id == "T-01"
        assert item.status == "covered"
        assert item.notes == ""  # default

    def test_notes_field(self):
        item = ComplianceItem(
            regulation="R",
            requirement_id="R-01",
            requirement="req",
            description="desc",
            aigis_feature="feat",
            status="partial",
            notes="Some note",
        )
        assert item.notes == "Some note"


class TestBuildComplianceItems:
    def test_returns_nonempty_list(self):
        items = _build_compliance_items()
        assert len(items) > 0

    def test_all_items_are_compliance_items(self):
        items = _build_compliance_items()
        for item in items:
            assert isinstance(item, ComplianceItem)

    def test_all_items_have_required_fields(self):
        items = _build_compliance_items()
        for item in items:
            assert item.regulation
            assert item.requirement_id
            assert item.requirement
            assert item.description
            assert item.aigis_feature
            assert item.status in ("covered", "partial", "not_covered", "user_responsibility")

    def test_covers_multiple_regulations(self):
        items = _build_compliance_items()
        regulations = {item.regulation for item in items}
        assert len(regulations) >= 5  # At least 5 different regulations

    def test_v12_guideline_present(self):
        items = _build_compliance_items()
        v12_items = [i for i in items if "v1.2" in i.regulation]
        assert len(v12_items) >= 20  # v1.2 has 20+ requirements

    def test_v12_agent_requirements(self):
        items = _build_compliance_items()
        agent_ids = {i.requirement_id for i in items if "AGENT" in i.requirement_id}
        assert "GL-AGENT-01" in agent_ids
        assert "GL-AGENT-02" in agent_ids

    def test_v12_new_risk_categories(self):
        items = _build_compliance_items()
        ids = {i.requirement_id for i in items}
        assert "GL-RISK-03" in ids  # ハルシネーション起因誤動作
        assert "GL-RISK-04" in ids  # 合成コンテンツ
        assert "GL-RISK-05" in ids  # AI過度依存
        assert "GL-RISK-06" in ids  # 感情操作

    def test_v12_hitl_mandatory(self):
        items = _build_compliance_items()
        ids = {i.requirement_id for i in items}
        assert "GL-HUMAN-01" in ids
        assert "GL-HUMAN-02" in ids  # 緊急停止
        assert "GL-HUMAN-03" in ids  # 最小権限
        assert "GL-HUMAN-04" in ids  # 継続的モニタリング

    def test_v12_governance_requirements(self):
        items = _build_compliance_items()
        ids = {i.requirement_id for i in items}
        assert "GL-GOV-01" in ids  # 攻めのガバナンス
        assert "GL-GOV-02" in ids  # 活用の手引き
        assert "GL-RESP-01" in ids  # RAG構築者責任
        assert "GL-RESP-02" in ids  # RAG安全設計
        assert "GL-POISON-01" in ids  # データ汚染対策

    def test_no_v11_references(self):
        items = _build_compliance_items()
        for item in items:
            assert "v1.1" not in item.regulation, (
                f"{item.requirement_id} still references v1.1"
            )


class TestGetComplianceReport:
    def test_returns_list_of_dicts(self):
        report = get_compliance_report()
        assert isinstance(report, list)
        assert len(report) > 0
        assert isinstance(report[0], dict)

    def test_dict_keys(self):
        report = get_compliance_report()
        expected_keys = {
            "regulation",
            "requirement_id",
            "requirement",
            "description",
            "aigis_feature",
            "status",
            "notes",
        }
        for item in report:
            assert set(item.keys()) == expected_keys

    def test_report_matches_items_count(self):
        items = _build_compliance_items()
        report = get_compliance_report()
        assert len(report) == len(items)


class TestGetComplianceSummary:
    def test_summary_keys(self):
        summary = get_compliance_summary()
        assert "total_requirements" in summary
        assert "covered" in summary
        assert "partial" in summary
        assert "not_covered" in summary
        assert "user_responsibility" in summary
        assert "coverage_rate" in summary
        assert "by_regulation" in summary

    def test_total_matches_sum(self):
        summary = get_compliance_summary()
        total = summary["covered"] + summary["partial"] + summary["not_covered"] + summary["user_responsibility"]
        assert total == summary["total_requirements"]

    def test_coverage_rate_range(self):
        summary = get_compliance_summary()
        assert 0 <= summary["coverage_rate"] <= 100

    def test_by_regulation_structure(self):
        summary = get_compliance_summary()
        by_reg = summary["by_regulation"]
        assert isinstance(by_reg, dict)
        assert len(by_reg) > 0
        for reg_name, counts in by_reg.items():
            assert "total" in counts
            assert "covered" in counts
            assert "partial" in counts
            assert "not_covered" in counts


class TestGroupByRegulation:
    def test_groups_items_correctly(self):
        items = [
            ComplianceItem("RegA", "A-01", "r", "d", "f", "covered"),
            ComplianceItem("RegA", "A-02", "r", "d", "f", "partial"),
            ComplianceItem("RegB", "B-01", "r", "d", "f", "not_covered"),
        ]
        groups = _group_by_regulation(items)
        assert "RegA" in groups
        assert "RegB" in groups
        assert groups["RegA"]["total"] == 2
        assert groups["RegA"]["covered"] == 1
        assert groups["RegA"]["partial"] == 1
        assert groups["RegB"]["total"] == 1
        assert groups["RegB"]["not_covered"] == 1

    def test_empty_list(self):
        groups = _group_by_regulation([])
        assert groups == {}
