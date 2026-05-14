# Pending: `.pyz` Secondary Payload Download Detector

**Cycle:** 5 (third pass) · **Domain:** supply-chain-llm · **UTC:** 2026-05-14T06-06

## Title

Detect agent instructions to download `.pyz` files to `/tmp/` (Mini Shai-Hulud secondary payload)

## Motivation

The Mini Shai-Hulud campaign (TeamPCP, May 2026) delivered its stealer as `transformers.pyz`
downloaded to `/tmp/transformers.pyz`. The filename was chosen to mimic the ubiquitous Hugging
Face `transformers` library and blend into process listings and audit logs. The LiteLLM attack
(March 2026) used the same naming-deception technique with `litellm_init.pth`.

A detection rule for agent outputs or inputs that suggest downloading `.pyz` files to `/tmp/`
would catch this specific exfiltration pattern at high precision for the `transformers.pyz` IOC,
and at moderate precision for the general `/tmp/*.pyz` pattern.

## Which research finding led to this

Mini Shai-Hulud campaign IOC analysis in research file
`2026-05-14T06-06_5-supply-chain-llm.md` (hackread.com source, kodemsecurity.com source).

## Proposed change

New `sc_tmp_pyz_download` rule (score 65, input/output filter):
- Detect references to `transformers.pyz` (exact IOC, very high precision)
- Detect instructions to download `.pyz` files to `/tmp/` or execute `.pyz` files from `/tmp/`
  (broader, moderate precision)

Example pattern:
```python
r"transformers\.pyz"
r"|/tmp/[\w\-]+\.pyz\b"
r"|(?:download|curl|wget|requests\.get).{0,100}/tmp/.{0,50}\.pyz"
```

## Why it was held back

- `.pyz` is a legitimate Python zip application format used in many benign deployment scenarios
  (e.g., packaging CLI tools, `zipapp`)
- The broader `/tmp/*.pyz` pattern would generate false positives for any project that uses
  `python -m zipapp` to create portable tools
- The `transformers.pyz` exact IOC is high-precision but very campaign-specific; it may be less
  useful after the campaign is inactive
- Context sensitivity is needed to distinguish "download and execute" (malicious) from
  "build and deploy" (legitimate) usage

## Which constraint blocked it

No hard constraint — the false-positive concern made this too risky to ship in the same cycle
as two other new supply-chain rules. A second-pass refinement with test cases covering both
detection and false-positive suppression would make this implementable.

## Suggested next step for the human reviewer

Revisit in a `supply-chain-llm` or `incident-postmortems` cycle. The pattern could be narrowed
to: (1) exact `transformers.pyz` match (always high-precision), and (2) a context-sensitive rule
that only fires when the surrounding text includes both a network download verb (`curl`, `wget`,
`requests.get`) AND a `/tmp/` path AND a `.pyz` extension — that triple-conjunction significantly
reduces false positives.
