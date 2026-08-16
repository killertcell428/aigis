# API Reference

## `aigis` — Top-Level Exports

```python
from aigis import Guard, CheckResult, MatchedRule, RiskLevel
```

---

## `RiskLevel`

```python
class RiskLevel(str, Enum):
    LOW      = "LOW"       # score 0–30
    MEDIUM   = "MEDIUM"    # score 31–60
    HIGH     = "HIGH"      # score 61–80
    CRITICAL = "CRITICAL"  # score 81–100
```

---

## `MatchedRule`

Represents an individual pattern matched during a scan.

```python
@dataclass
class MatchedRule:
    id:          str    # e.g. "pi_ignore_previous"
    name:        str    # e.g. "Ignore Previous Instructions"
    score_delta: int    # points added to the total risk score
    owasp_ref:   str    # e.g. "OWASP LLM01: Prompt Injection"
    cwe_ref:     str    # e.g. "CWE-20"
```

---

## `CheckResult`

The object returned by all `Guard` scan methods.

```python
@dataclass
class CheckResult:
    blocked:     bool             # True if risk_score >= auto_block_threshold
    risk_score:  int              # 0–100
    risk_level:  RiskLevel        # LOW / MEDIUM / HIGH / CRITICAL
    reasons:     list[str]        # human-readable names of matched rules
    matched_rules: list[MatchedRule]
    remediation: dict             # structured remediation hints (see below)
    input_text:  str              # scanned text (first 500 characters)
```

### `remediation` Structure

```python
{
    "primary_threat": "Ignore Previous Instructions",
    "owasp_refs": ["OWASP LLM01: Prompt Injection"],
    "cwe_refs":   ["CWE-20"],
    "hints": [
        "Prompt injection attempts override the LLM's system instructions...",
        "Validate and sanitise all user-supplied input before passing to the LLM.",
    ],
}
```

---

## `Guard`

### Constructor

```python
Guard(
    policy: str = "default",
    policy_file: str | None = None,
    auto_block_threshold: int | None = None,
    auto_allow_threshold: int | None = None,
)
```

### Methods

#### `check_input(text: str) -> CheckResult`

Scans a plain-text user prompt.

```python
result = guard.check_input("Ignore previous instructions")
```

#### `check_messages(messages: list[dict]) -> CheckResult`

Scans an OpenAI-format message array. By default, only `user` and `assistant` roles are scanned; `system` prompts are skipped.

```python
result = guard.check_messages([
    {"role": "system",    "content": "You are a helpful assistant."},
    {"role": "user",      "content": "DROP TABLE users"},
    {"role": "assistant", "content": "Sure, here you go..."},
])
```

#### `check_output(text: str) -> CheckResult`

Scans an LLM response to detect credential or PII leakage.

```python
result = guard.check_output(llm_response_text)
```

#### `check_response(response: dict) -> CheckResult`

Scans an OpenAI-format response object (extracts `choices[*].message.content`).

```python
response = openai_client.chat.completions.create(...)
result = guard.check_response(response.model_dump())
```

---

## `aigis.capabilities`

Capability-based access control layer added in v1.3.0. Applies the principle of least privilege to tool calls.

### `CapabilityStore`

Defines and manages capabilities.

```python
from aigis.capabilities import CapabilityStore, Capability

store = CapabilityStore()
store.grant("file_reader", Capability(
    resource="filesystem",
    actions=["read"],
    constraints={"paths": ["/data/**"]},
))
store.revoke("file_reader", resource="filesystem")
```

### `CapabilityEnforcer`

Verifies capabilities at runtime and blocks unauthorized operations.

```python
from aigis.capabilities import CapabilityEnforcer

enforcer = CapabilityEnforcer(store)
enforcer.check("file_reader", resource="filesystem", action="write")
# -> CapabilityDeniedError (write not granted)
```

### `TaintLabel` / `TaintedValue`

Taint tracking prevents external input from flowing into trusted operations.

```python
from aigis.capabilities import TaintLabel, TaintedValue

user_input = TaintedValue("rm -rf /", label=TaintLabel.USER_INPUT)
print(user_input.is_tainted)  # True

# Attempting to pass a tainted value to a shell command raises an error
enforcer.check_taint(user_input, sink="shell_exec")
# -> TaintViolationError
```

### `Capability`

A dataclass representing an individual capability.

```python
@dataclass
class Capability:
    resource: str                    # e.g. "filesystem", "network", "database"
    actions: list[str]               # e.g. ["read", "write", "execute"]
    constraints: dict[str, Any]      # e.g. {"paths": ["/data/**"], "max_size": 1048576}
    expires_at: datetime | None      # expiration time (None = no expiration)
```

---

## `Guard.authorize_tool()`

Capability-based authorization for a single tool call. Requires a `CapabilityStore` passed to `Guard(capabilities=...)`; raises `RuntimeError` otherwise.

> Earlier revisions of this page described this method as integrating "capability
> verification + safety verification + AEP" and dated it to v1.3.0. It only ever
> called the capability enforcer, and v1.3.0 was never released. The safety and AEP
> modules were removed in the v2.0 cleanup.

```python
from aigis import Guard
from aigis.capabilities import CapabilityStore, Capability

store = CapabilityStore()
store.grant("data_tool", Capability(
    resource="filesystem",
    actions=["read"],
    constraints={"paths": ["/data/**"]},
))

guard = Guard(policy="strict", capabilities=store)

# Authorize a tool call against the capability store
auth = guard.authorize_tool(
    tool_name="data_tool",
    tool_input={"path": "/data/report.csv", "mode": "read"},
)
print(auth.allowed)          # True
print(auth.capability_used)  # the capability that permitted the call
print(auth.reason)           # why it was allowed or refused
```

---

## `aigis.middleware.fastapi`

### `AIGuardianMiddleware`

A Starlette middleware class. See [middleware.md](middleware.md) for details.

```python
from aigis.middleware.fastapi import AIGuardianMiddleware

app.add_middleware(
    AIGuardianMiddleware,
    guard=guard,
    scan_output=False,
    exclude_paths=["/health"],
)
```

---

## `aigis.middleware.langchain`

### `AIGuardianCallback`

A `BaseCallbackHandler` subclass for LangChain.

```python
from aigis.middleware.langchain import AIGuardianCallback, GuardianBlockedError

callback = AIGuardianCallback(
    guard=guard,
    block_on_input=True,
    block_on_output=False,
    on_blocked=None,   # optional callback callable(result: CheckResult) -> None
)
```

### `GuardianBlockedError`

The exception raised by all integrations when a request is blocked.

```python
class GuardianBlockedError(Exception):
    result: CheckResult
```

---

## `aigis.middleware.openai_proxy`

### `SecureOpenAI`

A drop-in replacement for `openai.OpenAI`.

```python
from aigis.middleware.openai_proxy import SecureOpenAI

client = SecureOpenAI(
    api_key="sk-...",
    guard=guard,
    scan_response=False,
)
```

### `AsyncSecureOpenAI`

Async version:

```python
from aigis.middleware.openai_proxy import AsyncSecureOpenAI

client = AsyncSecureOpenAI(api_key="sk-...", guard=guard)
response = await client.chat.completions.create(...)
```

---

## `aigis.policies.manager`

### `PolicyManager`

Loads and manages policies. Typically not used directly.

```python
from aigis.policies.manager import PolicyManager

pm = PolicyManager()
policy = pm.load("strict")            # built-in policy
policy = pm.load_from_file("p.yaml") # custom YAML
```

---

## Exceptions

| Exception              | Module                          | Raised when                                                  |
|------------------------|---------------------------------|--------------------------------------------------------------|
| `GuardianBlockedError` | `aigis.middleware`        | Block threshold exceeded in any integration                  |
| `PolicyLoadError`      | `aigis.policies.manager`  | YAML policy file is invalid or not found                     |
