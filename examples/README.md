# Examples

Runnable code samples for aigis v1.3.1.

## Setup

```bash
pip install aigis
# or for all examples:
pip install 'aigis[all]'
```

## Files

| File | Description | Extra deps |
|------|-------------|------------|
| [`basic_usage.py`](basic_usage.py) | Core `Guard` class — input/output scanning, policies, risk scoring | none |
| [`fastapi_integration.py`](fastapi_integration.py) | FastAPI middleware + manual check | `aigis[fastapi]`, `uvicorn` |
| [`langchain_integration.py`](langchain_integration.py) | LangChain callback for input + output scanning | `aigis[langchain]`, `langchain-openai` |
| [`langgraph_integration.py`](langgraph_integration.py) | LangGraph agent with tool authorization | `aigis[langchain]`, `langgraph` |
| [`openai_proxy.py`](openai_proxy.py) | Drop-in `SecureOpenAI` wrapper (sync + async) | `aigis[openai]` |
| [`custom_policy.py`](custom_policy.py) | YAML policy files, inline overrides, custom rules | `aigis[yaml]` |

## Running the examples

```bash
# Basic — no dependencies, no API key needed
python examples/basic_usage.py

# FastAPI server
pip install 'aigis[fastapi]' uvicorn
uvicorn examples.fastapi_integration:app --reload
# then: curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
#         -d '{"messages": [{"role": "user", "content": "Hello!"}]}'

# LangChain (live LLM calls optional)
pip install 'aigis[langchain]' langchain-openai
OPENAI_API_KEY=sk-... python examples/langchain_integration.py

# LangGraph agent with tool authorization (v1.3.1)
pip install 'aigis[langchain]' langgraph
python examples/langgraph_integration.py

# OpenAI proxy (live API calls optional — guard fires offline)
pip install 'aigis[openai]'
OPENAI_API_KEY=sk-... python examples/openai_proxy.py

# Custom policy
pip install 'aigis[yaml]'
python examples/custom_policy.py
```

## What each example demonstrates

### `basic_usage.py`

- Prompt injection detection (165+ patterns, 25+ threat categories)
- PII detection (credit card, SSN, API keys)
- SQL injection detection
- Policy comparison (`permissive` vs `default` vs `strict`)
- Output scanning
- Accessing the full `CheckResult` (score, reasons, remediation)

### `fastapi_integration.py`

- `AIGuardianMiddleware` setup
- Automatic scan of all POST request bodies
- Accessing `request.state.guardian_result` inside route handlers
- Manual `guard.check_messages()` as an alternative to middleware
- Custom error handler for blocked requests

### `langchain_integration.py`

- `AIGuardianCallback` with `block_on_input=True` / `block_on_output=True`
- Handling `GuardianBlockedError`
- LCEL chain integration
- Custom `on_blocked` handler (silent logging instead of raising)

### `langgraph_integration.py` (v1.3.1)

- `Guard.authorize_tool()` — Capability-Based Access Control (CaMeL-inspired)
- `CapabilityStore` with scoped grants and automatic expiry
- `TaintLabel` (TRUSTED / UNTRUSTED / SANITIZED) enforcement
- `AtomicPipeline` — Scan → Execute → Vaporize as indivisible operation
- `SafetyVerifier` with `ProofCertificate` for audit trails

### `openai_proxy.py`

- `SecureOpenAI` as a drop-in for `openai.OpenAI`
- `scan_response=True` for output scanning
- `AsyncSecureOpenAI` for async code
- One-line migration from `openai.OpenAI`

### `custom_policy.py`

- Built-in policy comparison
- Inline `auto_block_threshold` / `auto_allow_threshold` override
- YAML policy file with custom rules
- Combining built-in patterns with custom regex rules

## v1.3.1 New Features (Layers 4-6)

### Capability-Based Access Control (Layer 4)

```python
from aigis import Guard
from aigis.capabilities import CapabilityStore, TaintLabel

store = CapabilityStore()
guard = Guard(capabilities=store)

# Grant a scoped capability
store.grant("file:read", scope="*.py", ttl_seconds=3600)

# Authorize a tool call — blocks UNTRUSTED data from control-flow tools
result = guard.authorize_tool(
    tool_name="shell:exec",
    taint=TaintLabel.UNTRUSTED,
)
print(result.allowed)  # False — UNTRUSTED data cannot execute shell commands
```

### Atomic Execution Pipeline (Layer 5)

```python
from aigis.aep import AtomicPipeline

pipeline = AtomicPipeline(guard=guard)

# Scan → Execute → Vaporize (indivisible)
result = pipeline.run(
    command="python script.py",
    timeout=30,
    vaporize=True,  # destroy artifacts after execution
)
print(result.stdout)
print(result.sandbox_used)    # True
print(result.artifacts_clean) # True
```

### Safety Verifier (Layer 6)

```python
from aigis.safety import SafetyVerifier, DEFAULT_SAFETY_SPEC

verifier = SafetyVerifier(spec=DEFAULT_SAFETY_SPEC)
certificate = verifier.verify(
    action="file:write",
    target="output.txt",
    content="safe content",
)
print(certificate.passed)      # True
print(certificate.certificate_id)  # UUID4
print(certificate.timestamp)       # UTC timestamp
```
