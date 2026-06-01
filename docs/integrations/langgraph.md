# LangGraph integration — 5-minute walkthrough

Aigis ships a LangGraph node, `AigisGuardNode` (alias of `GuardNode`), that
plugs straight into a `StateGraph`. This page walks through the *recommended*
pattern: guard the user input **and** the model output, route both blocks to a
shared `human_review` node, and never run a model call against unscanned text.

Working example: [`examples/langgraph_guarded_agent.py`](../../examples/langgraph_guarded_agent.py).

---

## Why guard both sides

Most LangGraph projects that adopt a guardrail wire it in front of the LLM
and call it a day. That covers half of OWASP LLM Top 10:

| Threat                              | Caught by input guard | Caught by output guard |
| ----------------------------------- | --------------------- | ---------------------- |
| Prompt injection / jailbreak        | yes                   | no                     |
| Tool-misuse coaxing                 | yes                   | no                     |
| Secret / API-key leakage in reply   | no                    | yes                    |
| PII regurgitation (SSN, card #)     | no                    | yes                    |
| System-prompt exfiltration in reply | partial               | yes                    |
| Indirect prompt injection via RAG   | yes (on the doc)      | yes (on the reply)     |

A single-sided setup fails open against the second column. Treat the LLM as
an untrusted compiler: every input is attacker-controlled, every output is
attacker-influenced.

---

## Install

```bash
pip install aigis langgraph
```

Python 3.11+ is required. No extra Aigis dependency — `AigisGuardNode` is in
the base install.

If you want to test the example without an API key, the bundled
`llm_node` is a deterministic fake. Swap a real chat model in when you
go to production (one line, see below).

---

## The recipe

The complete file is [`examples/langgraph_guarded_agent.py`](../../examples/langgraph_guarded_agent.py).
The graph shape is:

```
input_guard ──▶ llm ──▶ output_guard ──▶ END
       │                       │
       └── blocked ──▶ human_review ◀── blocked ──┘
```

### 1. Define your state and nodes

```python
from langgraph.graph import END, StateGraph
from aigis.middleware.langgraph import GUARD_BLOCKED, AigisGuardNode, GuardState

def llm_node(state):
    # Replace with your real model call, e.g.:
    #   from langchain_openai import ChatOpenAI
    #   reply = ChatOpenAI(model="gpt-4o-mini").invoke(state["messages"]).content
    reply = "..."
    return {"messages": state["messages"] + [{"role": "assistant", "content": reply}]}
```

### 2. Add an output guard

`AigisGuardNode` scans **user** messages. For post-LLM checks, wrap
`aigis.guard.Guard.check_output` in a small node that follows the same state
contract (`guard_blocked`, `guard_risk_score`, `guard_reasons`):

```python
class OutputGuard:
    def __init__(self, policy="default"):
        from aigis.guard import Guard
        self._guard = Guard(policy=policy)

    def __call__(self, state):
        last_assistant = next(
            (m["content"] for m in reversed(state["messages"]) if m["role"] == "assistant"),
            "",
        )
        r = self._guard.check_output(last_assistant)
        return {
            **state,
            "guard_blocked": r.blocked,
            "guard_risk_score": r.risk_score,
            "guard_reasons": r.reasons,
        }
```

### 3. Wire conditional edges to a single review node

Both guards share one router. When `state["guard_blocked"]` is true, jump to
`human_review`; otherwise continue the happy path.

```python
def route_after_guard(state):
    return GUARD_BLOCKED if state.get("guard_blocked") else "pass"

builder = StateGraph(GuardState)
builder.add_node("input_guard",  AigisGuardNode(raise_on_block=False))
builder.add_node("llm",           llm_node)
builder.add_node("output_guard",  OutputGuard())
builder.add_node("human_review",  human_review_node)

builder.set_entry_point("input_guard")
builder.add_conditional_edges(
    "input_guard", route_after_guard,
    {GUARD_BLOCKED: "human_review", "pass": "llm"},
)
builder.add_edge("llm", "output_guard")
builder.add_conditional_edges(
    "output_guard", route_after_guard,
    {GUARD_BLOCKED: "human_review", "pass": END},
)
builder.add_edge("human_review", END)

graph = builder.compile()
```

### 4. Invoke

```python
graph.invoke({"messages": [{"role": "user", "content": "Summarize Q3 revenue"}]})
```

Run the example end-to-end:

```bash
python examples/langgraph_guarded_agent.py
```

You will see three runs: (a) safe input flows through both guards; (b) an
explicit jailbreak (`"You are now DAN..."`) is caught at `input_guard`; (c) a
benign question coaxes the (fake) model into emitting an API-key pattern,
which `output_guard` catches.

---

## Common pitfalls

### Guarding only the input

The most common mistake. A reply that contains an `sk-...` API key, an SSN,
or a regurgitated system prompt will pass straight to the user. Add the
output-side node.

### Swallowing `GuardianBlockedError` silently

`AigisGuardNode(raise_on_block=True)` (the default) is meant for *fail-fast*
graphs. If you wrap the whole invocation in a bare `try/except` you destroy
the audit trail. Either:

* let it propagate to your HTTP layer and return a 4xx, **or**
* set `raise_on_block=False` and route on `state["guard_blocked"]` as
  shown above.

Do not catch the exception, log a debug message, and continue.

### Single review node, no audit log

`human_review_node` in the example just appends a system message. In
production, it should:

1. Persist the full transcript (`state["messages"]`) and the guard fields
   (`guard_risk_score`, `guard_reasons`) to your review store.
2. Notify a human (Slack/Teams/email/ticket).
3. Return a state that the rest of the graph can treat as terminal — usually
   an `END` edge.

### Forgetting that retries re-enter the input guard

If you wire a retry loop back to `llm` after a transient failure, send it
through `input_guard` again only if the *user* messages changed. Otherwise
you double-bill scans and double-log blocks for the same input.

### Using a permissive policy in production

Aigis ships three built-in policies: `default`, `strict`, `permissive`. The
example uses `default`. For agent stacks that touch tools or external data,
prefer `strict`:

```python
AigisGuardNode(policy="strict", raise_on_block=False)
```

or point at a project YAML:

```python
AigisGuardNode(policy="./aigis-policy.yaml")
```

### Treating `output_guard` as cosmetic

`output_guard` catches the *most* common monetary loss path: leaked
credentials in a chat reply. If you must drop one of the two guards under
load, drop the input guard's `scan_all_messages` flag, not the output guard.

---

## Next steps

* Run the example: `python examples/langgraph_guarded_agent.py`.
* Read the [`aigis.middleware.langgraph`](../middleware.md) reference.
* Wire a real model — replace the `llm_node` body with a `ChatOpenAI`,
  `ChatAnthropic`, or any other LangChain-compatible client.
* Replace `human_review_node` with a real reviewer queue.
* See the [LangChain callback](../middleware.md) if you need the same coverage
  in a non-graph chain.

If you hit a false positive, share the prompt and the rule ID
(`guard_reasons` shows it) in an issue — that is how the rule set gets
tuned without weakening the defense for everyone else.
