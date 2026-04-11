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

## `aigis.aep`

Atomic Execution Pipeline (AEP) added in v1.3.0. Executes tools atomically inside a sandbox and controls side effects.

### `AtomicPipeline`

Wraps tool execution as an atomic transaction.

```python
from aigis.aep import AtomicPipeline, Vaporizer

pipeline = AtomicPipeline(
    vaporize=True,      # Erase side effects on failure
    sandbox=True,       # Execute in a sandbox
    timeout=30.0,       # Timeout in seconds
)

result = await pipeline.execute(tool_fn, args={"path": "/data/report.csv"})
print(result.success)       # True
print(result.return_value)  # return value of tool_fn
print(result.side_effects)  # list of detected side effects
```

### `ProcessSandbox`

Runs tool execution in an isolated process.

```python
from aigis.aep import ProcessSandbox

sandbox = ProcessSandbox(
    allowed_paths=["/data/**"],
    network=False,        # network access disabled
    max_memory_mb=256,
)
result = await sandbox.run(tool_fn, args)
```

### `Vaporizer`

Rolls back side effects (file creation, network sends, etc.) on execution failure.

```python
from aigis.aep import Vaporizer

vaporizer = Vaporizer()
async with vaporizer.track():
    # Side effects within this block are auto-erased on failure
    write_file("/tmp/output.txt", data)
    # If an exception occurs -> /tmp/output.txt is automatically deleted
```

### `AEPResult`

Represents the result of a pipeline execution.

```python
@dataclass
class AEPResult:
    success: bool                    # whether execution succeeded
    return_value: Any                # return value of the tool
    side_effects: list[str]          # detected side effects
    duration_ms: float               # execution time in milliseconds
    sandbox_violations: list[str]    # sandbox violations (if any)
```

---

## `aigis.safety`

Formal safety verification layer added in v1.3.0. Verifies that tool side effects comply with a safety specification.

### `SafetyVerifier`

Verifies tool execution safety based on a safety specification.

```python
from aigis.safety import SafetyVerifier, DEFAULT_SAFETY_SPEC

verifier = SafetyVerifier(spec=DEFAULT_SAFETY_SPEC)
cert = verifier.verify(tool_name="file_writer", effects=[
    EffectSpec(type="file_write", target="/data/output.csv"),
])
print(cert.verified)     # True
print(cert.proof_hash)   # verification proof hash
```

### `SafetySpec`

Defines a safety specification.

```python
from aigis.safety import SafetySpec, Invariant

spec = SafetySpec(
    name="production-safety",
    invariants=[
        Invariant(
            name="no_system_write",
            description="Prohibit writes to system directories",
            condition="effect.target not matches '/etc/**'",
        ),
        Invariant(
            name="no_network_exfil",
            description="Prohibit sending data to external networks",
            condition="effect.type != 'network_send' or effect.target in allowed_hosts",
        ),
    ],
)
```

### `EffectSpec` / `Invariant` / `ProofCertificate`

```python
@dataclass
class EffectSpec:
    type: str          # "file_write", "network_send", "db_query", etc.
    target: str        # target resource
    metadata: dict     # additional metadata

@dataclass
class Invariant:
    name: str          # invariant name
    description: str   # human-readable description
    condition: str     # verification condition expression

@dataclass
class ProofCertificate:
    verified: bool             # whether all invariants were satisfied
    proof_hash: str            # SHA-256 hash of the verification proof
    checked_invariants: int    # number of invariants checked
    violations: list[str]      # violated invariants (if any)
    timestamp: datetime        # verification timestamp
```

### Pre-defined Safety Specifications

```python
from aigis.safety import DEFAULT_SAFETY_SPEC, STRICT_SAFETY_SPEC

# DEFAULT_SAFETY_SPEC — for general-purpose applications
# STRICT_SAFETY_SPEC — for finance/healthcare (stricter constraints)
verifier = SafetyVerifier(spec=STRICT_SAFETY_SPEC)
```

---

## `Guard.authorize_tool()`

Added in v1.3.0. A single entry point integrating capability verification + safety verification + AEP.

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

# Authorize a tool call (capability + safety spec verified in one step)
auth = guard.authorize_tool(
    tool_name="data_tool",
    action="read",
    resource="filesystem",
    target="/data/report.csv",
)
print(auth.authorized)    # True
print(auth.certificate)   # ProofCertificate
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
