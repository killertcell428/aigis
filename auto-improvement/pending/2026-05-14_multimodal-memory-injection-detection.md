# Pending: Multimodal Memory Injection Detection

**Title:** Multimodal Memory Injection Detection (Visual Memory Attack Coverage)

**Motivation:**
arxiv:2602.15927 ("Visual Memory Injection Attacks for Multi-Turn Conversations", February 2026) documents injection attacks that plant malicious instructions via images embedded in multi-turn conversation history. The injected image content is retrieved in a later turn and activates attack behavior. As LLM agents increasingly use multimodal context (images, documents, screenshots), memory poisoning attacks are extending beyond text to visual channels.

**Which research finding led to this:**
- arxiv:2602.15927 — visual injection via conversation history images
- General trend: multimodal agents (Claude, GPT-4o, Gemini) are increasingly used with persistent multimodal memory

**Proposed change:**
Add a multimodal memory scanning layer that:
1. Extracts text from images in memory entries (using OCR or model-based extraction in a pre-scan step)
2. Passes extracted text through existing memory poisoning patterns
3. Flags entries where embedded image text matches MEMORY_POISONING_PATTERNS

**Why it was held back:**
Requires new optional dependency (OCR library such as pytesseract or easyocr) or integration with a vision model. Both introduce a required or optional runtime dependency. This is incompatible with aigis's zero-runtime-dependency / rule-based philosophy unless the dependency is strictly opt-in and clearly gated.

**Which constraint blocked it:**
> aigis is a zero-runtime-dependency, rule-based Python firewall for AI agents. Do NOT add features that depend on calling an LLM at runtime.

**Suggested next step for human reviewer:**
Design an opt-in `[multimodal]` extras group with a lightweight OCR library as an optional dependency. The multimodal scanner should be clearly marked as requiring the extras and should degrade gracefully (skip image scanning with a warning) when the extras are not installed. This is a meaningful extension that preserves the zero-dependency default while unlocking multimodal coverage for operators who opt in.
