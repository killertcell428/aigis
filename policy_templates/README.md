# Aigis — Policy Template Hub

Industry-specific YAML policy templates for common deployment scenarios.

## Usage

```bash
# Use any template directly
pip install 'aigis[yaml]'
```

```python
from aigis import Guard

# Use a template from this directory
guard = Guard(policy_file="policy_templates/finance.yaml")

# Or point to your own copy
guard = Guard(policy_file="my_policy.yaml")
```

## Available Templates

| Template | Use Case | Block Threshold |
|----------|----------|-----------------|
| [`finance.yaml`](finance.yaml) | Banking, trading, payment apps | 61 (strict) |
| [`healthcare.yaml`](healthcare.yaml) | Medical records, telehealth | 61 (strict) |
| [`ecommerce.yaml`](ecommerce.yaml) | Online stores, product QA bots | 76 (moderate-strict) |
| [`internal_tools.yaml`](internal_tools.yaml) | Internal company chatbots | 81 (default) |
| [`education.yaml`](education.yaml) | EdTech, student-facing AI | 71 (moderate) |
| [`customer_support.yaml`](customer_support.yaml) | Support bots, helpdesks | 76 (moderate-strict) |
| [`developer_tools.yaml`](developer_tools.yaml) | Code assistants, CI helpers | 86 (permissive) |
| [`eu_ai_act_high_risk.yaml`](eu_ai_act_high_risk.yaml) | EU AI Act Annex III systems (effective 2026-08-02) | 55 (strict) |

## Customization

All templates follow this schema:

```yaml
name: my-policy
auto_block_threshold: 75   # Score >= this → blocked
auto_allow_threshold: 25   # Score <= this → always allowed
custom_rules:
  - id: unique_rule_id
    name: Human-readable name
    pattern: "(regex|pattern)"
    score_delta: 50          # Added to base risk score
    enabled: true
```

## Contributing a Template

PRs welcome! To add a new industry template:

1. Copy `internal_tools.yaml` as a starting point
2. Adjust thresholds and add industry-specific `custom_rules`
3. Add a row to the table above
4. Submit a PR with a description of the target use case
