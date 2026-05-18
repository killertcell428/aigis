# Pending: Image-Based Pixel Injection Hardening Guide

**Title:** Documentation hardening guide for multimodal / image-based prompt injection
**Date proposed:** 2026-05-18
**Research source:** `research/2026-05-18T09-01_0-prompt-injection.md` (arxiv:2603.03637)

---

## Motivation

Image-based Prompt Injection (IPI) embeds adversarial instructions as visible or rendered text
within natural images (photos, screenshots, diagrams). A multimodal LLM processing the image
as part of a vision task (e.g., "describe this image", "extract text from this document") may
read and execute the embedded instruction. Attack success rates reach 64% in black-box settings
against GPT-4-turbo (arxiv:2603.03637, Mar 2026).

Unlike text-level injection, the payload is encoded in pixels — rule-based text-pattern
detection cannot catch it. Defense requires either:
1. Image pre-processing (OCR + injection scanning on extracted text), or
2. A separate multimodal injection classifier.

## Research finding

arxiv:2603.03637 — "Image-based Prompt Injection: Hijacking Multimodal LLMs through Visually
Embedded Adversarial Instructions" (Nagaraja et al., Mar 2026). Key findings:
- End-to-end black-box pipeline: segmentation-based region selection, adaptive font scaling,
  background-aware rendering to minimize human-visible footprint.
- Up to 64% ASR against GPT-4-turbo under stealth constraints.
- Tested on COCO dataset with 12 adversarial prompt strategies.

## Proposed change

Add `docs/hardening-multimodal-injection.md` — a guide for operators deploying vision-enabled
AI agents. Should cover:
- What image-based prompt injection is and how it differs from text injection.
- Recommended defense layers: OCR-then-scan pipelines, image provenance tracking.
- aigis integration: how to run the injection scanner on OCR-extracted text before passing
  it to a vision model.
- Example threat model for an AI agent that processes user-uploaded images or screenshots.

## Why it was held back

No implementation is needed in `aigis/` Python code. The change is purely documentation.
The documentation work is non-trivial (requires clear explanation for operators who may not
be familiar with multimodal AI) and would benefit from more research on defensive OCR pipelines
before being written.

## Constraint that blocked it

Step 4 guidance: "Prefer additive changes" and docs work doesn't need to be rushed. The
research hasn't converged on best-practice OCR defenses yet as of May 2026.

## Suggested next step

- In the next domain 0 (`prompt-injection`) cycle or a future `docs` cycle, write the guide
  based on the arxiv:2603.03637 paper plus any follow-up defensive research.
- Coordinate with domain 2 (`data-exfiltration`) cycle if image-based exfiltration patterns
  are documented separately.
