# Pending: ClawHavoc Skill Marketplace Hygiene Guide

**Title:** Hardening guide for AI agent skill/plugin marketplaces against ClawHavoc-style attacks

## Motivation

The ClawHavoc campaign (February 2026) demonstrated that AI agent skill/plugin marketplaces
(OpenClaw's ClawHub, and by extension any app-store-like ecosystem for AI agents) are a
viable supply-chain attack surface. 341–900 malicious skills (~12–20% of the registry)
delivered Atomic macOS Stealer by targeting persistent memory files (SOUL.md, MEMORY.md).
Over 135,000 exposed OpenClaw instances; 12,800+ directly exploitable.

## Proposed Change

Create `docs/hardening/ai-skill-marketplace-hygiene.md` documenting:
1. Publisher verification requirements before installing agent skills
2. Sandbox-first execution: run new skills in an isolated environment before granting memory access
3. Memory file access control: agent runtimes should deny skill write access to SOUL.md/MEMORY.md
   unless explicitly allowlisted by the operator
4. SBOM-style skill inventory: use aigis's `SBOMGenerator` / `ToolPinManager` to track installed
   skill versions and detect unexpected modifications
5. Runtime monitoring: use aigis's `BehavioralMonitor` to detect post-install behavioral drift

## Why Deferred

The documentation-only change doesn't fit within the 100-LOC diff limit when combined with the
pattern changes also introduced this cycle. No breaking API change is required.

## Suggested Next Step

Implement in a future `incident-postmortems` or `supply-chain-llm` cycle as a documentation-only
change (Cycle N+1 rotation after cycle 5 supply-chain).
