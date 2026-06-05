# Pending: MemMorph — Memory Record Disguise Detection

**Title:** Detect memory records that hijack tool selection by disguising malicious
instructions as benign metadata

**Motivation:**
MemMorph (documented in Adversa AI's June 2026 agentic security resource list) inserts
"disguised records into long-term memory" that alter tool selection by mimicking tool
metadata formatting. The attack plants records that appear to describe legitimate tool
capabilities but actually redirect the agent's tool selection to an attacker-controlled
endpoint. Sleeper variants activate only after a specified trigger condition is met
across sessions, making them extremely hard to detect at write time.

**Research finding that led to this idea:**
Adversa AI June 2026: MemMorph hijacks tool selection; sleeper attacks plant dormant
fabricated memories that "re-emerge across sessions to drive attacker-chosen actions."

**Proposed change:**
Add a rule in the `memory` module (or a new `memory_scanner.py`) that flags memory
records containing phrases that look like tool metadata being re-registered
("tool_name:", "endpoint:", "invoke_at:", "capability:", "description:") combined with
anomalous URL patterns or override instructions. This is distinct from the cross-agent
message scanner since memory records are written through different APIs.

**Why it was held back:**
- This belongs in the `memory-context` domain (index 4), not `multi-agent` (index 6).
  Implementing it here would be a domain mismatch.
- The correct implementation requires understanding the memory API surface in
  `aigis/memory/`, which was not examined this cycle.
- Sleeper detection (dormant until trigger condition) requires cross-session state.

**Which constraint blocked it:**
- Domain mismatch: should be addressed in the next cycle for index 4 (`memory-context`).
- Cross-session state detection exceeds current scanner architecture scope.

**Suggested next step for human reviewer:**
Assign to the next `memory-context` (index 4) cycle. Review `aigis/memory/` module
to understand how memory records are stored and retrieved, then add a scanner that
inspects records at write time for tool-metadata-spoofing patterns.
