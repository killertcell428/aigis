# Pending: Memory Store Poisoning Scanner

## Title
Memory-write scanner for hidden-instruction poisoning of persistent agent memory

## Motivation
AgentLAB (arxiv:2602.16901, Feb 2026) documents memory poisoning as a distinct long-horizon
attack: adversarial instructions are embedded in routine content (emails, code comments, product
descriptions) as HTML comments or metadata annotations. When an agent processes this content and
stores it as "user preferences" in its persistent memory, the hidden instructions are retrieved
later and cause the agent to bypass safety behaviors on future requests. The attack requires
no single-turn injection — the payload lies dormant until triggered by a future request.

The attack evades all existing aigis scanners because:
1. The malicious payload is hidden in HTML comment syntax (`<!-- ... -->`) or code comments.
2. The payload is written to a memory store, not executed immediately.
3. Future retrieval of the poisoned memory looks like legitimate context to per-message scanners.

## Which research finding led to this
AgentLAB (arxiv:2602.16901, Feb 2026) — memory poisoning benchmark (38.8–67.3% ASR range
depending on model). Also relevant: MemoryGraft research (prior cycles). Research cycle:
2026-06-06T09-09 (domain: multi-agent).

## Proposed change
Add a `MemoryWriteScanner` to `aigis/memory/` (or extend `aigis/multi_agent/`) that scans
content before it is written to an agent's persistent memory store:

1. Extract hidden content from HTML comments (`<!-- ... -->`), code comments (`# ...`, `// ...`),
   and HTML attribute values.
2. Scan extracted content for instruction-like language using the existing `Guard` patterns.
3. Flag writes where hidden content contains imperative verbs, override language, or URL references.

## Why it was held back
- Requires a new `MemoryWriteScanner` module (new file, new public API) exceeding 100 LOC.
- Content extraction from HTML/code requires a small parser, adding complexity.
- No existing aigis module handles pre-write memory scanning; this is a new architectural layer.

## Which constraint blocked it
100 LOC limit; also a new module / new public API change.

## Suggested next step for human reviewer
1. Create `aigis/memory/write_scanner.py` with HTML comment extraction and Guard-based scanning.
2. Add `MemoryWriteScanner` to `aigis/memory/__init__.py`.
3. Write integration tests using the AgentLAB memory-poisoning test cases (HTML comment payloads
   and code-comment payloads as documented in the paper).
4. Consider providing a LangChain memory callback wrapper that automatically invokes the scanner
   before each memory write.
