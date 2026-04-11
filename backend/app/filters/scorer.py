"""Risk scoring engine.

Aggregates matched pattern scores into a single risk score and level.
Each matched rule now carries OWASP references and remediation hints.
"""
from dataclasses import dataclass, field

from app.filters.patterns import DetectionPattern


@dataclass
class MatchedRule:
    """A pattern that matched during filtering, with remediation context."""

    rule_id: str
    rule_name: str
    category: str
    score_delta: int
    matched_text: str
    owasp_ref: str = ""
    remediation_hint: str = ""


@dataclass
class FilterResult:
    """Outcome of running a text through the filter."""

    risk_score: int
    risk_level: str  # low | medium | high | critical
    matched_rules: list[MatchedRule] = field(default_factory=list)
    is_blocked: bool = False
    reason: str = ""

    @property
    def remediation(self) -> dict:
        """Aggregated remediation guidance from all matched rules."""
        if not self.matched_rules:
            return {}
        hints = []
        refs = []
        for r in self.matched_rules:
            if r.remediation_hint and r.remediation_hint not in hints:
                hints.append(r.remediation_hint)
            if r.owasp_ref and r.owasp_ref not in refs:
                refs.append(r.owasp_ref)
        top = max(self.matched_rules, key=lambda r: r.score_delta)
        return {
            "primary_threat": top.rule_name,
            "primary_category": top.category,
            "owasp_refs": refs,
            "hints": hints,
        }


def score_to_level(score: int) -> str:
    """Convert a numeric score (0-100) to a risk level label."""
    if score <= 30:
        return "low"
    elif score <= 60:
        return "medium"
    elif score <= 80:
        return "high"
    else:
        return "critical"


def run_patterns(
    text: str,
    patterns: list[DetectionPattern],
    custom_rules: list[dict] | None = None,
) -> FilterResult:
    """Run all patterns against the text and return a scored FilterResult.

    Scoring strategy:
      - Each matching pattern contributes its base_score.
      - Multiple matches from the same category are capped (diminishing returns).
      - Final score is clamped to [0, 100].
    """
    import re

    matched: list[MatchedRule] = []
    category_scores: dict[str, int] = {}

    for pattern in patterns:
        if not pattern.enabled:
            continue
        m = pattern.pattern.search(text)
        if m:
            matched_text = m.group(0)[:200]  # cap to 200 chars for storage
            matched.append(
                MatchedRule(
                    rule_id=pattern.id,
                    rule_name=pattern.name,
                    category=pattern.category,
                    score_delta=pattern.base_score,
                    matched_text=matched_text,
                    owasp_ref=pattern.owasp_ref,
                    remediation_hint=pattern.remediation_hint,
                )
            )
            # accumulate per-category with diminishing returns (max 2x base)
            prev = category_scores.get(pattern.category, 0)
            category_scores[pattern.category] = min(
                prev + pattern.base_score, pattern.base_score * 2
            )

    # Run custom rules if provided
    if custom_rules:
        for rule in custom_rules:
            if not rule.get("enabled", True):
                continue
            try:
                pattern = re.compile(rule["pattern"], re.IGNORECASE | re.DOTALL)
                m = pattern.search(text)
                if m:
                    score_delta = int(rule.get("score_delta", 20))
                    matched.append(
                        MatchedRule(
                            rule_id=rule["id"],
                            rule_name=rule["name"],
                            category="custom",
                            score_delta=score_delta,
                            matched_text=m.group(0)[:200],
                            owasp_ref=rule.get("owasp_ref", ""),
                            remediation_hint=rule.get("remediation_hint", ""),
                        )
                    )
                    prev = category_scores.get("custom", 0)
                    category_scores["custom"] = min(prev + score_delta, score_delta * 2)
            except re.error:
                continue  # skip invalid regex

    total_score = min(sum(category_scores.values()), 100)
    level = score_to_level(total_score)

    reason = ""
    if matched:
        top_rule = max(matched, key=lambda r: r.score_delta)
        reason = f"Matched rule: {top_rule.rule_name} (category: {top_rule.category})"

    return FilterResult(
        risk_score=total_score,
        risk_level=level,
        matched_rules=matched,
        reason=reason,
    )
