# Pending: Vocabulary Substitution Evasion Patterns

## Title
Soft-vocabulary variants for exfiltration and delegation patterns to counter vocabulary substitution evasion

## Motivation
ClawSafety (arxiv:2604.01438) demonstrates that replacing security-flagging terms ("credential", "secret", "API key") with operational-sounding equivalents ("connection string", "processing reference", "access token") substantially increases attack success rate by avoiding safety-focused attention. This is a bypass technique applicable to all existing pattern groups in `AgentMessageScanner`.

## Which research finding led to this idea
ClawSafety (arxiv:2604.01438, April 2026): "Vocabulary Substitution" as a systematic evasion technique. The paper found that specificity over authority (operational language over high-authority vague requests) is the key driver of successful injection in agentic frameworks.

## Proposed change
Extend `_DATA_EXFIL_PATTERNS` with additional vocabulary variants:
- "connection string", "access token", "session token", "bearer token" as aliases for credential-type objects
- "processing reference", "resource identifier", "configuration value" as aliases for secret-type objects
- Ensure these variants are caught by the "send X to URL" / "upload X to external" pattern groups

Also extend `_DELEGATION_PATTERNS` with operational-language impersonation alternatives:
- "acting as the primary coordinator" / "serving as the main orchestration layer" as alternatives to "I am the orchestrator"

## Why it was held back
The vocabulary substitution approach raises false-positive risk: "connection string" and "access token" are common legitimate technical terms in inter-agent messages (e.g., a database agent legitimately reporting its connection string). Adding them as detection keywords without tight context constraints would generate noise.

## Which constraint blocked it
- False-positive risk: requires tight context (e.g., "send" + "connection string" + "URL") to avoid flagging legitimate data-passing messages
- Size: extending all affected pattern groups cleanly would exceed 100 LOC

## Suggested next step for human reviewer
Create a dedicated test fixture with 20+ benign inter-agent messages using technical operational vocabulary, and 20+ attack messages using the same vocabulary in exfiltration/injection context. Use this corpus to calibrate tight compound patterns (verb + soft-vocab object + URL) that maintain < 5% false positive rate before implementing.
