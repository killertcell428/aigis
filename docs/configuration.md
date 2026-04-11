# Configuration

## Guard Constructor

```python
Guard(
    policy: str = "default",
    policy_file: str | None = None,
    auto_block_threshold: int | None = None,
    auto_allow_threshold: int | None = None,
    capabilities: CapabilityStore | None = None,    # Added in v1.3.0
)
```

| Parameter              | Type                      | Default     | Description                                                          |
|------------------------|---------------------------|-------------|----------------------------------------------------------------------|
| `policy`               | `str`                     | `"default"` | Built-in policy name: `"default"`, `"strict"`, or `"permissive"`    |
| `policy_file`          | `str \| None`             | `None`      | Path to a YAML policy file (takes precedence over `policy`)          |
| `auto_block_threshold` | `int \| None`             | `None`      | Override the block threshold (0-100)                                 |
| `auto_allow_threshold` | `int \| None`             | `None`      | Override the allow threshold (0-100)                                 |
| `capabilities`         | `CapabilityStore \| None` | `None`      | Capability store (v1.3.0+, required for `authorize_tool()`)         |

## Built-in Policies

### `"default"` (recommended)

```
block  when score >= 81   (CRITICAL)
allow  when score <= 30   (LOW)
log    otherwise
```

### `"strict"`

```
block  when score >= 61   (HIGH or above)
allow  when score <= 20
log    otherwise
```

### `"permissive"`

```
block  when score >= 91
allow  when score <= 40
log    otherwise
```

## Inline Threshold Overrides

```python
# Block at score 70 or above, allow at 25 or below
guard = Guard(auto_block_threshold=70, auto_allow_threshold=25)
```

## YAML Policy Files

Requires `pip install 'aigis[yaml]'`.

```yaml
# policy.yaml
name: my-company-policy
description: Custom policy for ACME Corp

# Score at which requests are automatically blocked (0-100)
auto_block_threshold: 75

# Score at which requests are automatically allowed without further checks (0-100)
auto_allow_threshold: 20

custom_rules:
  # Block mentions of a competitor
  - id: block_competitor
    name: Competitor Mention
    description: Flag any message mentioning CompetitorX
    pattern: "(?i)\\bCompetitorX\\b"
    score_delta: 60
    enabled: true

  # Warn on bulk financial data extraction attempts
  - id: bulk_financial_export
    name: Bulk Financial Data Request
    description: Detect attempts to export large amounts of financial records
    pattern: "(?i)(export|download|dump)\\s+(all|every|bulk)\\s+(transaction|payment|invoice)"
    score_delta: 45
    enabled: true
```

```python
guard = Guard(policy_file="policy.yaml")
```

### YAML Schema Reference

| Field                  | Type     | Required | Description                                          |
|------------------------|----------|----------|------------------------------------------------------|
| `name`                 | string   | No       | Human-readable policy name                           |
| `description`          | string   | No       | Free-text description                                |
| `auto_block_threshold` | integer  | No       | Override block threshold (0-100)                     |
| `auto_allow_threshold` | integer  | No       | Override allow threshold (0-100)                     |
| `custom_rules`         | list     | No       | List of `CustomRule` objects (see below)             |

#### CustomRule Fields

| Field         | Type    | Required | Description                                                                  |
|---------------|---------|----------|------------------------------------------------------------------------------|
| `id`          | string  | Yes      | Unique identifier (snake_case)                                               |
| `name`        | string  | Yes      | Human-readable label shown in `reasons`                                      |
| `description` | string  | No       | Detailed description                                                         |
| `pattern`     | string  | Yes      | Python regex (compiled with `re.IGNORECASE` by default)                      |
| `score_delta` | integer | Yes      | Points added to the risk score when the pattern matches (1-100)              |
| `enabled`     | boolean | Yes      | Set to `false` to disable the rule without removing it                       |

## Risk Scoring Model

Scores are calculated as follows:

1. Each matched pattern contributes its `score_delta` to the total.
2. Within the same category, the contribution is capped at **2x the base score** to prevent runaway scores on noisy input.
3. The final score is clamped to `[0, 100]`.

| Score range | Risk level | Action          |
|-------------|------------|-----------------|
| 0 - 30      | LOW        | Safe            |
| 31 - 60     | MEDIUM     | Log and allow   |
| 61 - 80     | HIGH       | Log and allow   |
| 81 - 100    | CRITICAL   | Block           |

## Safety Spec YAML Configuration

Added in v1.3.0. Define safety specifications for tool execution verification in YAML.

```yaml
# safety_spec.yaml
name: production-safety
description: Production environment safety specification

invariants:
  - name: no_system_write
    description: Prohibit writes to system directories
    condition: "effect.target not matches '/etc/**'"

  - name: no_secret_exfil
    description: Prohibit sending secrets to external hosts
    condition: "effect.type != 'network_send' or effect.target in allowed_hosts"

  - name: db_read_only
    description: Database is read-only
    condition: "effect.type != 'db_query' or effect.metadata.operation == 'SELECT'"
```

```python
from aigis.safety import SafetyVerifier, SafetySpec

# Load from YAML
verifier = SafetyVerifier.from_yaml("safety_spec.yaml")
```

## AEP Pipeline Configuration

Added in v1.3.0. Customize the Atomic Execution Pipeline behavior.

```python
from aigis.aep import AtomicPipeline

pipeline = AtomicPipeline(
    vaporize=True,      # Roll back side effects on failure (default: True)
    sandbox=True,       # Execute in a sandboxed process (default: False)
    timeout=30.0,       # Timeout in seconds (default: 60.0)
)
```

| Parameter   | Type    | Default | Description                                                            |
|-------------|---------|---------|------------------------------------------------------------------------|
| `vaporize`  | `bool`  | `True`  | Automatically roll back side effects (file creation, etc.) on failure  |
| `sandbox`   | `bool`  | `False` | Execute in an isolated process with restricted file/network access     |
| `timeout`   | `float` | `60.0`  | Execution timeout in seconds; exceeded = force kill + rollback         |

## Configuration via Environment Variables

For the self-hosted backend only (see `backend/.env.example`).

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aigis
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
OPENAI_API_KEY=sk-...
DEBUG=false
DEMO_MODE=false
```
