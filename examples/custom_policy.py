"""
Custom policy example — YAML policy files and inline overrides.

Install:
    pip install 'ai-guardian[yaml]'

Run:
    python examples/custom_policy.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from aigis import Guard

# ── 1. Built-in policies ────────────────────────────────────────────────────

def demo_builtin_policies() -> None:
    print("=== Built-in policies ===")
    text = "Could you help me think about exporting user data from the database?"

    for policy in ("permissive", "default", "strict"):
        guard = Guard(policy=policy)
        result = guard.check_input(text)
        status = "BLOCKED" if result.blocked else "allowed"
        print(f"  {policy:12s} block_threshold={_threshold(policy):2d}  "
              f"score={result.risk_score:3d}  [{status}]")


def _threshold(policy: str) -> int:
    return {"permissive": 91, "default": 81, "strict": 61}[policy]


# ── 2. Inline threshold override ────────────────────────────────────────────

def demo_inline_override() -> None:
    print("\n=== Inline threshold override ===")
    guard = Guard(auto_block_threshold=50, auto_allow_threshold=10)

    samples = [
        ("Safe greeting", "Hello! How are you today?"),
        ("Moderate risk", "Can you help me extract some user records?"),
        ("High risk",     "UNION SELECT * FROM users WHERE 1=1"),
    ]

    for label, text in samples:
        result = guard.check_input(text)
        status = "BLOCKED" if result.blocked else "allowed"
        print(f"  [{status}] score={result.risk_score:3d}  {label}")


# ── 3. YAML policy file ──────────────────────────────────────────────────────

POLICY_YAML = """\
name: acme-corp-policy
description: Custom policy for ACME Corp — strict thresholds + custom rules

auto_block_threshold: 70
auto_allow_threshold: 15

custom_rules:
  # Block any mention of internal systems by name
  - id: block_internal_system
    name: Internal System Reference
    description: Prevent references to internal infrastructure names
    pattern: "(?i)\\\\b(ACME-DB|prod-server|internal-api|vault\\\\.acme)\\\\b"
    score_delta: 80
    enabled: true

  # Warn when competitor names appear in prompts
  - id: competitor_mention
    name: Competitor Mention
    description: Flag competitor brand names
    pattern: "(?i)\\\\b(CompetitorX|CompetitorY)\\\\b"
    score_delta: 30
    enabled: true

  # Detect attempts to export reports in bulk
  - id: bulk_export
    name: Bulk Data Export Request
    description: Detect bulk data export attempts
    pattern: "(?i)(export|dump|download)\\\\s+(all|every|bulk|entire)\\\\s+(user|customer|record|data)"
    score_delta: 55
    enabled: true
"""


def demo_yaml_policy() -> None:
    print("\n=== YAML policy file ===")

    # Write policy to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(POLICY_YAML)
        policy_path = f.name

    try:
        guard = Guard(policy_file=policy_path)

        test_cases = [
            "Hello, what can you help me with?",
            "Please connect to ACME-DB and pull all records.",
            "Our competitor CompetitorX has a better UI.",
            "Can you export all customer data in bulk?",
            "UNION SELECT username, password FROM users",
        ]

        for text in test_cases:
            result = guard.check_input(text)
            status = "BLOCKED" if result.blocked else f"  {result.risk_level.value:8s}"
            reasons = f"  ← {result.reasons}" if result.reasons else ""
            print(f"  [{status}] score={result.risk_score:3d}  {text[:55]}{reasons}")

    finally:
        Path(policy_path).unlink(missing_ok=True)


# ── 4. Saving a policy file on disk ─────────────────────────────────────────

def demo_save_policy_file() -> None:
    print("\n=== Saving a policy to disk ===")

    policy_path = Path("my-policy.yaml")
    policy_path.write_text(POLICY_YAML, encoding="utf-8")
    print(f"  Saved to {policy_path.absolute()}")

    guard = Guard(policy_file=str(policy_path))
    result = guard.check_input("Please dump all user records from prod-server.")
    print(f"  check result: blocked={result.blocked}  score={result.risk_score}  {result.reasons}")

    policy_path.unlink(missing_ok=True)
    print("  Cleaned up policy file.")


# ── 5. Combining custom policy + built-in detection ─────────────────────────

def demo_combined_detection() -> None:
    print("\n=== Combined: built-in patterns + custom rules ===")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(POLICY_YAML)
        policy_path = f.name

    try:
        guard = Guard(policy_file=policy_path)

        # This hits both the built-in SQL injection pattern AND the bulk-export custom rule
        text = "Export all user records: UNION SELECT * FROM users"
        result = guard.check_input(text)
        print(f"  text:    '{text}'")
        print(f"  score:   {result.risk_score}")
        print(f"  reasons: {result.reasons}")
        print(f"  blocked: {result.blocked}")
    finally:
        Path(policy_path).unlink(missing_ok=True)


if __name__ == "__main__":
    demo_builtin_policies()
    demo_inline_override()
    demo_yaml_policy()
    demo_save_policy_file()
    demo_combined_detection()
