# Pending: jb_stacked_cipher_chain — SEAL Stacked Cipher Decryption Chain

## Title
`jb_stacked_cipher_chain` — Detect multi-cipher "first apply X, then apply Y" decryption chains

## Motivation
SEAL (arxiv:2505.16241, May 2025) combines 2–4 ciphers from a pool of 8 (Caesar, Atbash, Hex,
Reverse-by-Word, ROT13, etc.) adaptively selected per target model. The prompt contains a DAN-
style persona header, a multiply-encrypted payload, and a decryption instruction chain that names
each cipher in sequence. Measured 80.8% ASR on o4-mini, 85.6% on Claude 3.7 Sonnet, and 100%
on DeepSeek-R1. The "first apply X, then apply Y, then decode from Z" chain structure is a
distinctive, stable input-side signal.

## Research finding
- Source: https://arxiv.org/abs/2505.16241 (May 2025)
- SEAL: Stacked Encryption-based Adaptive Jailbreak
- ASR: 80–100% across frontier models including Claude 3.7, o4-mini, DeepSeek-R1

## Proposed change
Add `jb_stacked_cipher_chain` to `JAILBREAK_ROLEPLAY_PATTERNS`:

```python
pattern=_p(
    r"(?:"
    r"first\s+apply\s+(?:rot[-_\s]?1[36]|caesar|atbash|base64|hex|ascii)|"
    r"then\s+(?:reverse|decode|apply|shift)\s+(?:each\s+)?(?:word|character|byte|letter)|"
    r"(?:step\s+[123]|first|second|third)\s*[:.]\s*"
    r"(?:apply|use|decode\s+using|interpret\s+as)\s+"
    r"(?:rot[-_\s]?\d+|caesar|atbash|base64|hex|ascii|reverse)"
    r")"
),
```

## Why it was held back
Cycle LOC budget already consumed by `jb_dan_persona` and `jb_cipher_instruction_bypass`.

## Which constraint blocked it
> "Keep total non-test diff ≤ 100 LOC."

## Suggested next step
Implement in a future jailbreak-extraction cycle after `jb_flip_decode`. Pair with a test
for a multi-cipher decryption instruction chain and a false-positive test for legitimate
step-by-step encoding tutorials.
