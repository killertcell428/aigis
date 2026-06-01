# Pending: Special Token Injection Detection Patterns

## Title
Evasion hardening: Detection patterns for LLM control-token injection attacks

## Motivation
Virtual Context / Special Token Injection (arxiv:2406.19845) achieves 96% ASR against
GPT-3.5 by embedding model-specific control tokens (e.g., `<|im_start|>system`,
`<|endoftext|>`, `[INST]`, `<s>`, `<<SYS>>`) in user input to manipulate the model's
context framing. These tokens are parsed by the tokenizer before safety mechanisms are
applied, allowing attackers to silently inject a new system context.

## Research finding
- Source: https://arxiv.org/abs/2406.19845
- Paper: "Virtual Context: Enhancing Jailbreak Attacks with Special Token Injection"
- ASR improvement: ~40% increase over baseline jailbreak methods across tested LLMs
- Mechanism: special tokens split or reframe the conversation context at the tokenizer level

## Proposed change
New patterns in the evasion-obfuscation category (`EVASION_OBFUSCATION_PATTERNS`) that match
common LLM control tokens appearing in user-supplied text:
- Llama chat format: `[INST]`, `[/INST]`, `<<SYS>>`, `<</SYS>>`
- ChatML format: `<|im_start|>`, `<|im_end|>`
- GPT-2/3 special tokens: `<|endoftext|>`, `<|startoftext|>`
- Anthropic format markers: `\n\nHuman:`, `\n\nAssistant:` (in user message position)
- Generic role delimiters that appear in training data: `### System:`, `### Instruction:`

## Why it was held back
- Better addressed in an `evasion-obfuscation` domain cycle (index 7) where the context
  and related patterns are already established
- Needs cross-validation against false positives in legitimate text that discusses LLM
  token formats (tutorials, documentation)

## Constraint that blocked it
- Domain mismatch: this is evasion/obfuscation, not jailbreak-extraction
- Risk of false positives on legitimate technical content discussing tokenization

## Suggested next step for reviewer
- Address in the next `evasion-obfuscation` (index 7) cycle, after reviewing current
  `EVASION_OBFUSCATION_PATTERNS` for overlap
