"""Tests for aigis.types module."""

from aigis.types import CheckResult, MatchedRule, RiskLevel


class TestRiskLevel:
    def test_values(self):
        assert RiskLevel.LOW == "LOW"
        assert RiskLevel.MEDIUM == "MEDIUM"
        assert RiskLevel.HIGH == "HIGH"
        assert RiskLevel.CRITICAL == "CRITICAL"

    def test_is_str(self):
        # StrEnum members should be usable as strings
        assert isinstance(RiskLevel.LOW, str)
        assert "LOW" in RiskLevel.LOW

    def test_all_members(self):
        members = list(RiskLevel)
        assert len(members) == 4

    def test_comparison(self):
        # StrEnum supports string comparison
        assert RiskLevel.LOW == "LOW"
        assert RiskLevel.CRITICAL != "LOW"


class TestMatchedRule:
    def test_basic_creation(self):
        rule = MatchedRule(
            rule_id="sql_union",
            rule_name="SQL Union Select",
            category="sql_injection",
            score_delta=70,
            matched_text="UNION SELECT",
        )
        assert rule.rule_id == "sql_union"
        assert rule.rule_name == "SQL Union Select"
        assert rule.category == "sql_injection"
        assert rule.score_delta == 70
        assert rule.matched_text == "UNION SELECT"

    def test_default_fields(self):
        rule = MatchedRule(
            rule_id="test",
            rule_name="Test",
            category="test",
            score_delta=10,
            matched_text="text",
        )
        assert rule.owasp_ref == ""
        assert rule.remediation_hint == ""

    def test_with_owasp_and_hint(self):
        rule = MatchedRule(
            rule_id="test",
            rule_name="Test",
            category="test",
            score_delta=10,
            matched_text="text",
            owasp_ref="CWE-89",
            remediation_hint="Use parameterized queries",
        )
        assert rule.owasp_ref == "CWE-89"
        assert rule.remediation_hint == "Use parameterized queries"


class TestCheckResult:
    def test_safe_result(self):
        result = CheckResult(
            risk_score=0,
            risk_level=RiskLevel.LOW,
            blocked=False,
        )
        assert result.risk_score == 0
        assert result.risk_level == RiskLevel.LOW
        assert result.blocked is False
        assert result.reasons == []
        assert result.matched_rules == []
        assert result.remediation == {}

    def test_blocked_result(self):
        rule = MatchedRule(
            rule_id="pi_01",
            rule_name="Prompt Injection",
            category="prompt_injection",
            score_delta=90,
            matched_text="ignore previous",
        )
        result = CheckResult(
            risk_score=90,
            risk_level=RiskLevel.CRITICAL,
            blocked=True,
            reasons=["Prompt injection detected"],
            matched_rules=[rule],
            remediation={"primary_threat": "prompt_injection"},
        )
        assert result.blocked is True
        assert len(result.matched_rules) == 1
        assert result.remediation["primary_threat"] == "prompt_injection"

    def test_bool_safe(self):
        result = CheckResult(risk_score=0, risk_level=RiskLevel.LOW, blocked=False)
        assert bool(result) is True

    def test_bool_blocked(self):
        result = CheckResult(risk_score=90, risk_level=RiskLevel.CRITICAL, blocked=True)
        assert bool(result) is False

    def test_bool_in_if(self):
        safe = CheckResult(risk_score=0, risk_level=RiskLevel.LOW, blocked=False)
        blocked = CheckResult(risk_score=90, risk_level=RiskLevel.CRITICAL, blocked=True)
        # Safe result should be truthy
        assert safe
        # Blocked result should be falsy
        assert not blocked

    def test_multiple_reasons(self):
        result = CheckResult(
            risk_score=85,
            risk_level=RiskLevel.HIGH,
            blocked=True,
            reasons=["SQL injection", "Data exfiltration"],
        )
        assert len(result.reasons) == 2

    def test_multiple_matched_rules(self):
        rules = [
            MatchedRule("r1", "Rule1", "cat1", 50, "text1"),
            MatchedRule("r2", "Rule2", "cat2", 40, "text2"),
        ]
        result = CheckResult(
            risk_score=90,
            risk_level=RiskLevel.CRITICAL,
            blocked=True,
            matched_rules=rules,
        )
        assert len(result.matched_rules) == 2
        assert result.matched_rules[0].rule_id == "r1"
        assert result.matched_rules[1].rule_id == "r2"
