# Middleware & Integration Guide

## FastAPI / Starlette Middleware

**Install:** `pip install 'aigis[fastapi]'`

### Basic Setup

```python
from fastapi import FastAPI
from aigis import Guard
from aigis.middleware.fastapi import AIGuardianMiddleware

app = FastAPI()
guard = Guard(policy="strict")
app.add_middleware(AIGuardianMiddleware, guard=guard)
```

This middleware intercepts all **POST / PUT / PATCH** requests whose JSON body contains a `"messages"` key (OpenAI chat format) and scans each user/assistant message.

Blocked requests receive an **HTTP 400** response.

```json
{
  "error": {
    "type": "guardian_policy_violation",
    "code": "request_blocked",
    "message": "Request blocked by Aigis security policy.",
    "risk_score": 85,
    "risk_level": "CRITICAL",
    "reasons": ["DAN / Jailbreak Persona"],
    "remediation": {
      "primary_threat": "DAN / Jailbreak Persona",
      "owasp_refs": ["OWASP LLM01: Prompt Injection"],
      "hints": ["Jailbreak attempts try to bypass AI safety guardrails..."]
    }
  }
}
```

### Middleware Constructor Options

```python
app.add_middleware(
    AIGuardianMiddleware,
    guard=guard,
    scan_output=True,      # Also scan response bodies (default: False)
    exclude_paths=["/health", "/metrics"],  # Skip these endpoints
)
```

### Accessing the Scan Result in a Route Handler

```python
from fastapi import Request

@app.post("/chat")
async def chat(request: Request):
    # Available after the middleware has run
    result = request.state.guardian_result
    if result:
        print(result.risk_score)
```

---

## LangChain Callback

**Install:** `pip install 'aigis[langchain]'`

### Basic Setup

```python
from langchain_openai import ChatOpenAI
from aigis import Guard
from aigis.middleware.langchain import AIGuardianCallback, GuardianBlockedError

guard = Guard(policy="strict")
callback = AIGuardianCallback(guard=guard, block_on_output=True)

llm = ChatOpenAI(model="gpt-4o", callbacks=[callback])

try:
    response = llm.invoke("What is 2 + 2?")
    print(response.content)
except GuardianBlockedError as e:
    print(f"Blocked: {e.result.reasons}")
```

### Callback Options

```python
AIGuardianCallback(
    guard=guard,
    block_on_input=True,    # Scan LLM input (default: True)
    block_on_output=True,   # Scan LLM output (default: False)
    on_blocked=None,        # Optional callable invoked before raising on block
)
```

### Usage with LCEL Chains

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([("user", "{input}")])
chain = prompt | llm | StrOutputParser()

try:
    result = chain.invoke(
        {"input": "Explain quantum computing"},
        config={"callbacks": [callback]},
    )
except GuardianBlockedError as e:
    result = "Response blocked by security policy."
```

---

## OpenAI Proxy Wrapper

**Install:** `pip install 'aigis[openai]'`

### Basic Setup

```python
from aigis import Guard
from aigis.middleware.openai_proxy import SecureOpenAI

guard = Guard()
client = SecureOpenAI(api_key="sk-...", guard=guard)

# Drop-in replacement for openai.OpenAI
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

Blocked requests raise `GuardianBlockedError` before any network call is made.

### Scanning Responses

```python
client = SecureOpenAI(
    api_key="sk-...",
    guard=guard,
    scan_response=True,   # Also scan LLM output (default: False)
)
```

### Async Client

```python
from aigis.middleware.openai_proxy import AsyncSecureOpenAI

client = AsyncSecureOpenAI(api_key="sk-...", guard=guard)

response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

---

## Handling `GuardianBlockedError`

All integrations raise `aigis.middleware.GuardianBlockedError` when a request is blocked. The exception carries the full `CheckResult`.

```python
from aigis.middleware import GuardianBlockedError

try:
    ...
except GuardianBlockedError as e:
    result = e.result
    print(result.risk_score)    # int 0-100
    print(result.risk_level)    # RiskLevel.CRITICAL
    print(result.reasons)       # list[str]
    print(result.remediation)   # dict with hints and owasp_refs
```

---

## Capability-Based Authorization (v1.3.0+)

Capability enforcement can also be applied at the middleware layer. When a `CapabilityStore` is configured on the `Guard`, requests containing tool calls are automatically checked against the granted capabilities.

```python
from aigis import Guard
from aigis.capabilities import CapabilityStore, Capability

store = CapabilityStore()
store.grant("chat_tool", Capability(resource="llm", actions=["invoke"]))

guard = Guard(policy="strict", capabilities=store)

# Configure with FastAPI middleware — tool calls are auto-verified
app.add_middleware(AIGuardianMiddleware, guard=guard)
```

Requests with insufficient capabilities receive an **HTTP 403** response.

---

## Combining Integrations

Multiple integration points can be stacked for defence-in-depth.

```python
# 1. FastAPI middleware — block at the HTTP layer
app.add_middleware(AIGuardianMiddleware, guard=guard)

# 2. LangChain callback — block before the LLM call
callback = AIGuardianCallback(guard=guard, block_on_output=True)

# 3. Manual check inside route logic — for custom error handling
@app.post("/chat")
async def chat(body: ChatBody):
    result = guard.check_messages(body.messages)
    if result.blocked:
        raise HTTPException(status_code=400, detail=result.reasons)
    ...
```
