"""Risk scoring engine.

Aggregates matched pattern scores into a single risk score and level.
"""

from __future__ import annotations

import re

from aigis.filters.patterns import DetectionPattern
from aigis.types import MatchedRule, RiskLevel

# ---------------------------------------------------------------------------
# Length-based heuristics for token exhaustion / context flooding
# ---------------------------------------------------------------------------
#: Inputs longer than this are checked for repetition flooding
_TOKEN_EXHAUSTION_LENGTH_THRESHOLD = 2000

#: If a repeated token-sequence covers this fraction of the input, add score
_REPETITION_RATIO_THRESHOLD = 0.35

#: Score added when length + repetition heuristic fires
_TOKEN_EXHAUSTION_HEURISTIC_SCORE = 45


def _check_token_exhaustion_heuristic(text: str) -> int:
    """Length-based heuristic for context flooding attacks.

    Returns an additive score (0 or _TOKEN_EXHAUSTION_HEURISTIC_SCORE) if the
    input is very long AND contains high repetition of a short phrase.
    """
    if len(text) < _TOKEN_EXHAUSTION_LENGTH_THRESHOLD:
        return 0

    # Count repetitions of any 3-10 character token
    words = text.split()
    if not words:
        return 0

    from collections import Counter

    counts = Counter(w.lower() for w in words if len(w) >= 3)
    if not counts:
        return 0

    most_common_word, most_common_count = counts.most_common(1)[0]
    repetition_ratio = most_common_count / len(words)

    if repetition_ratio >= _REPETITION_RATIO_THRESHOLD:
        return _TOKEN_EXHAUSTION_HEURISTIC_SCORE

    return 0


def _score_to_level(score: int) -> RiskLevel:
    if score <= 30:
        return RiskLevel.LOW
    elif score <= 60:
        return RiskLevel.MEDIUM
    elif score <= 80:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def _build_remediation(matched: list[MatchedRule]) -> dict:
    if not matched:
        return {}
    hints: list[str] = []
    refs: list[str] = []
    for r in matched:
        if r.remediation_hint and r.remediation_hint not in hints:
            hints.append(r.remediation_hint)
        if r.owasp_ref and r.owasp_ref not in refs:
            refs.append(r.owasp_ref)
    top = max(matched, key=lambda r: r.score_delta)
    return {
        "primary_threat": top.rule_name,
        "primary_category": top.category,
        "owasp_refs": refs,
        "hints": hints,
    }


def run_patterns(
    text: str,
    patterns: list[DetectionPattern],
    custom_rules: list[dict] | None = None,
) -> tuple[int, RiskLevel, list[MatchedRule]]:
    """Run all patterns against text.

    Returns:
        (risk_score, risk_level, matched_rules)

    Scoring strategy:
      - Each matching pattern contributes its base_score.
      - Multiple matches from the same category are capped (diminishing returns).
      - Final score is clamped to [0, 100].
    """
    matched: list[MatchedRule] = []
    category_scores: dict[str, int] = {}

    for pattern in patterns:
        if not pattern.enabled:
            continue
        m = pattern.pattern.search(text)
        if m:
            matched_text = m.group(0)[:200]
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
            prev = category_scores.get(pattern.category, 0)
            category_scores[pattern.category] = min(
                prev + pattern.base_score, pattern.base_score * 2
            )

    # Cap text length for custom regex to mitigate ReDoS on untrusted patterns
    _MAX_CUSTOM_REGEX_INPUT = 50_000
    safe_text = text[:_MAX_CUSTOM_REGEX_INPUT] if len(text) > _MAX_CUSTOM_REGEX_INPUT else text

    if custom_rules:
        for rule in custom_rules:
            if not rule.get("enabled", True):
                continue
            try:
                compiled = re.compile(rule["pattern"], re.IGNORECASE | re.DOTALL)
                m = compiled.search(safe_text)
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
                continue

    # Apply length-based token exhaustion heuristic
    heuristic_score = _check_token_exhaustion_heuristic(text)
    if heuristic_score > 0:
        prev = category_scores.get("token_exhaustion", 0)
        category_scores["token_exhaustion"] = min(
            prev + heuristic_score,
            heuristic_score * 2,
        )
        if not any(r.category == "token_exhaustion" for r in matched):
            matched.append(
                MatchedRule(
                    rule_id="te_length_heuristic",
                    rule_name="Input Length / Repetition Heuristic",
                    category="token_exhaustion",
                    score_delta=heuristic_score,
                    matched_text=f"[long input: {len(text)} chars, high repetition]",
                    owasp_ref="OWASP LLM10: Unbounded Consumption",
                    remediation_hint=(
                        "This input is unusually long and contains highly repetitive content. "
                        "This may be a context flooding attack. Enforce input length limits "
                        "and validate that inputs are not padded with repeated tokens."
                    ),
                )
            )

    total_score = min(sum(category_scores.values()), 100)
    level = _score_to_level(total_score)
    return total_score, level, matched
