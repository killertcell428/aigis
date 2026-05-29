#!/usr/bin/env python3
"""Daily paper-review loop for the Awesome-LLM4Cybersecurity list.

Reads N (default 10) unseen entries from the upstream LITERATURES.md, asks
Claude Haiku whether each one suggests a concrete Aigis hardening, and:

  - writes a pending/ stub for each adopted candidate (human reviews & merges),
  - writes a research/ roll-up for the batch (always, even with 0 candidates),
  - opens one GitHub issue summarising the batch (one click per candidate to
    promote into a real PR),
  - records every seen URL/title into paper_review_state.json so the next run
    moves forward.

The script is intentionally additive: it only writes drafts. No detector code
is touched. Human reviewers promote pending/ entries via a follow-up PR.

Usage:
    python auto-improvement/scripts/paper_review.py             # full run
    python auto-improvement/scripts/paper_review.py --dry-run   # parse only
    python auto-improvement/scripts/paper_review.py --no-issue  # skip gh

Required env (non-dry-run): ANTHROPIC_API_KEY.
Optional env: GITHUB_REPOSITORY (for issue URL composition under Actions).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_DIR = REPO_ROOT / "auto-improvement"
PENDING_DIR = AI_DIR / "pending"
RESEARCH_DIR = AI_DIR / "research"
STATE_PATH = AI_DIR / "paper_review_state.json"

DEFAULT_SOURCE = (
    "https://raw.githubusercontent.com/tmylla/Awesome-LLM4Cybersecurity/main/LITERATURES.md"
)

# Numbered list line: "12. Title | *Venue* | 2026.01.31 | [Paper Link](url)"
# URL portion is optional; title may contain colons / pipes inside backticks.
ENTRY_RE = re.compile(
    r"^\s*\d+\.\s+(?P<title>.+?)\s*\|\s*\*(?P<venue>.+?)\*\s*\|\s*(?P<date>[\d.]+)"
    r"(?:\s*\|\s*\[[^\]]*\]\((?P<url>[^)\s]+)\))?\s*$"
)
SECTION_RE = re.compile(r"^#{1,4}\s+(.+?)\s*$")

# Aigis context used to bias the LLM toward concrete pattern proposals.
AIGIS_CONTEXT = """\
Aigis is a zero-dependency Python firewall for LLM agents.

Detection model:
- Each rule is a DetectionPattern (regex + score + input/output filter scope).
- Rules live in modules like aigis/policies/, aigis/patterns.py, aigis/safety/,
  aigis/supply_chain/, etc. Each rule has a stable rule_id (e.g. `sc_langflow_build_exec`,
  `afe_python_mro_escape`, `pi_unicode_tag_block`).
- The loop has a hard budget: one paper translates to at most ~10 LOC of pattern
  code + a few regex tests. Proposals that need new dependencies, ML models,
  trained classifiers, or rewriting >100 LOC are NOT relevant.

What IS relevant:
- A new attack technique with a string signature catchable by regex / substring /
  small AST inspection (e.g. a specific API path, a specific f-string template,
  a specific Unicode block, a specific obfuscation prefix).
- A measurable improvement to an existing rule (e.g. extending a regex to catch
  a documented bypass).
- A new compliance template (NIST / EU AI Act / ISO) that maps cleanly onto an
  existing policy_templates/ file.
- A hardening guide (docs-only) that codifies operational guidance from the paper.

What is NOT relevant:
- ML-based detection, embeddings, training pipelines.
- Pure benchmarks/datasets with no extractable detection rule.
- Surveys that summarise prior work without introducing new attack signatures.
- Agentic frameworks for offensive use that don't translate into a defensive signature.
"""

JUDGE_PROMPT = """\
You are triaging one paper for the Aigis auto-improvement loop.

{aigis_context}

Paper:
- Title: {title}
- Venue: {venue}
- Date: {date}
- URL: {url}
- List section: {section}

Decide whether this paper plausibly yields a concrete, regex/substring-scoped
detection rule or a small docs/template addition for Aigis. Be strict: when in
doubt, say no. Most papers will be irrelevant; that is fine.

Reply with one JSON object, no prose, no code fences:
{{
  "relevant": true | false,
  "rule_id": "<short snake_case id if relevant, else null>",
  "rule_category": "input | output | supply_chain | mcp | memory | compliance | docs | null",
  "one_line": "<= 25 words explaining what the rule catches, or why irrelevant>",
  "blocked_example": "<a literal example string the rule would flag, or null>",
  "source_evidence": "<one sentence quoting or paraphrasing the paper's key finding>"
}}
"""


@dataclass
class Entry:
    section: str
    title: str
    venue: str
    date: str
    url: str | None

    @property
    def key(self) -> str:
        """Stable dedup key: URL when present, else title hash."""
        if self.url:
            return f"url:{self.url}"
        return "title:" + hashlib.sha1(self.title.encode("utf-8")).hexdigest()[:16]

    @property
    def slug(self) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        return base[:60] or "paper"


@dataclass
class Verdict:
    relevant: bool
    rule_id: str | None
    rule_category: str | None
    one_line: str
    blocked_example: str | None
    source_evidence: str


def fetch_source(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "aigis-paper-review/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_entries(text: str) -> list[Entry]:
    entries: list[Entry] = []
    section = "(unsectioned)"
    for line in text.splitlines():
        m = SECTION_RE.match(line)
        if m:
            section = m.group(1).strip()
            continue
        m = ENTRY_RE.match(line)
        if not m:
            continue
        entries.append(
            Entry(
                section=section,
                title=m.group("title").strip().strip("`"),
                venue=m.group("venue").strip(),
                date=m.group("date").strip(),
                url=(m.group("url") or "").strip() or None,
            )
        )
    return entries


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"seen": {}, "runs": []}
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    data.setdefault("seen", {})
    data.setdefault("runs", [])
    return data


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def pick_unseen(entries: list[Entry], seen: dict, limit: int) -> list[Entry]:
    fresh = [e for e in entries if e.key not in seen]
    # Prefer newest first (date string sorts because format is YYYY.MM.DD).
    fresh.sort(key=lambda e: (e.date or ""), reverse=True)
    return fresh[:limit]


class JudgeAuthError(RuntimeError):
    """Raised when the Anthropic SDK cannot authenticate (missing/invalid key).

    Surfaced separately from per-paper errors so the loop can abort the entire
    run cleanly instead of marking every paper as "judge error: ..." and
    advancing state past unjudged entries (see issues #93 / #95 / #96).
    """


def _is_auth_error(exc: Exception) -> bool:
    """Heuristic: does this exception look like a missing/invalid API key?

    Anthropic SDK raises ``anthropic.AuthenticationError`` / ``PermissionDeniedError``
    on a bad key, but the most common production failure mode is the SDK's
    "Could not resolve authentication method" RuntimeError when no key is
    available at all. Match all three by class name + message keywords so we
    don't have to import the SDK just for `isinstance` checks.
    """
    name = type(exc).__name__
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return True
    text = str(exc).lower()
    return (
        "could not resolve authentication method" in text
        or "expected one of api_key" in text
        or "x-api-key" in text and "authorization" in text
    )


def judge_with_anthropic(entry: Entry) -> Verdict:
    import anthropic  # noqa: PLC0415 — optional dep, only needed in non-dry-run

    client = anthropic.Anthropic()
    prompt = JUDGE_PROMPT.format(
        aigis_context=AIGIS_CONTEXT,
        title=entry.title,
        venue=entry.venue,
        date=entry.date,
        url=entry.url or "(no URL)",
        section=entry.section,
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(block.text for block in msg.content if getattr(block, "text", None))
    return parse_verdict(raw)


def parse_verdict(raw: str) -> Verdict:
    # Defensive parse: strip code fences if the model added any.
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|```$", "", text).strip()
    obj = json.loads(text)
    return Verdict(
        relevant=bool(obj.get("relevant")),
        rule_id=obj.get("rule_id") or None,
        rule_category=obj.get("rule_category") or None,
        one_line=str(obj.get("one_line", ""))[:400],
        blocked_example=obj.get("blocked_example") or None,
        source_evidence=str(obj.get("source_evidence", ""))[:400],
    )


def write_pending(entry: Entry, verdict: Verdict, today: str) -> Path:
    fname = f"{today}_paper_{entry.slug}.md"
    path = PENDING_DIR / fname
    body = f"""# Pending: {verdict.rule_id or entry.slug}

## Title

{verdict.one_line}

## Source paper

- **{entry.title}**
- Venue: {entry.venue} ({entry.date})
- URL: {entry.url or "(no URL provided in source list)"}
- Discovered via: Awesome-LLM4Cybersecurity / `{entry.section}`

## Why it might matter for Aigis

{verdict.source_evidence}

## Proposed rule (draft)

- **rule_id (proposed):** `{verdict.rule_id or "TBD"}`
- **category:** {verdict.rule_category or "TBD"}
- **what it catches:** {verdict.one_line}

### Example the rule should flag

```
{verdict.blocked_example or "(LLM did not surface a concrete example — verify against the paper before implementing.)"}
```

## Why this is in pending/ not implemented

This entry was drafted by `auto-improvement/scripts/paper_review.py` from the
Awesome-LLM4Cybersecurity reading list. A human reviewer must:

1. Read the actual paper to confirm the technique is real and current.
2. Decide if the regex/string signature above survives realistic adversarial
   variations (or if a stricter pattern is needed).
3. Promote the rule into the appropriate `aigis/` module via a normal PR, with
   tests covering both the example above and at least one near-miss benign case.
4. Or close this file with a note on why it was rejected.
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_research(
    today_path: str, batch: list[tuple[Entry, Verdict | None]], source_url: str
) -> Path:
    path = RESEARCH_DIR / f"{today_path}_paper-batch.md"
    lines: list[str] = [
        f"# Research: paper-batch — {today_path}",
        "",
        f"Source: {source_url}",
        f"Papers reviewed this run: {len(batch)}",
        f"Candidates surfaced (relevant=true): "
        + str(sum(1 for _, v in batch if v and v.relevant)),
        "",
        "---",
        "",
    ]
    for entry, verdict in batch:
        lines.append(f"## {entry.title}")
        lines.append("")
        lines.append(f"- Venue: {entry.venue} ({entry.date})")
        lines.append(f"- URL: {entry.url or '(none)'}")
        lines.append(f"- Section: {entry.section}")
        if verdict is None:
            lines.append("- Verdict: SKIPPED (no API call this run)")
        else:
            lines.append(
                f"- Verdict: {'RELEVANT' if verdict.relevant else 'not relevant'} "
                f"— {verdict.one_line}"
            )
            if verdict.relevant:
                lines.append(f"- Proposed rule_id: `{verdict.rule_id}` ({verdict.rule_category})")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def open_issue(
    today: str,
    batch: list[tuple[Entry, Verdict]],
    research_path: Path,
    pending_paths: list[Path],
) -> None:
    relevant = [(e, v) for e, v in batch if v.relevant]
    title = (
        f"Paper review {today}: {len(batch)} papers reviewed, "
        f"{len(relevant)} candidate rule(s)"
    )
    body_lines = [
        f"Automated batch from `auto-improvement/scripts/paper_review.py`.",
        "",
        f"- Research roll-up: `{research_path.relative_to(REPO_ROOT).as_posix()}`",
        f"- Candidates drafted under `auto-improvement/pending/`: {len(pending_paths)}",
        "",
        "## Candidates",
        "",
    ]
    if not relevant:
        body_lines.append("_No candidate surfaced relevant detector ideas this batch._")
    for entry, verdict in relevant:
        body_lines.extend(
            [
                f"### `{verdict.rule_id}` — {entry.title}",
                "",
                f"- Category: {verdict.rule_category}",
                f"- Source: {entry.venue} ({entry.date}) — {entry.url or '(no URL)'}",
                f"- Catches: {verdict.one_line}",
                f"- Pending file: `auto-improvement/pending/{today}_paper_{entry.slug}.md`",
                "",
            ]
        )
    body_lines.extend(
        [
            "## All papers reviewed",
            "",
            *[
                f"- {('✅' if v.relevant else '⏭️')} {e.title} ({e.venue}, {e.date})"
                for e, v in batch
            ],
            "",
            "---",
            "",
            "Reviewer checklist:",
            "- [ ] Confirm each ✅ entry against the actual paper",
            "- [ ] Promote accepted ones into the appropriate `aigis/` module via PR",
            "- [ ] Close + delete pending files for rejected proposals",
        ]
    )
    subprocess.run(
        ["gh", "issue", "create", "--title", title, "--body", "\n".join(body_lines)],
        check=True,
        cwd=REPO_ROOT,
    )


def run(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-papers", type=int, default=10)
    parser.add_argument("--source-url", default=DEFAULT_SOURCE)
    parser.add_argument("--dry-run", action="store_true", help="Parse + pick only, no API/IO writes")
    parser.add_argument("--no-issue", action="store_true", help="Skip the gh issue step")
    args = parser.parse_args(list(argv) if argv is not None else None)

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    text = fetch_source(args.source_url)
    entries = parse_entries(text)
    if not entries:
        print("ERROR: parsed 0 entries from source. Format may have changed.", file=sys.stderr)
        return 2

    state = load_state()
    picked = pick_unseen(entries, state["seen"], args.max_papers)
    print(f"Source entries: {len(entries)} | already seen: {len(state['seen'])} | picked: {len(picked)}")
    for e in picked:
        print(f"  - {e.date} | {e.title[:80]}")

    if args.dry_run:
        return 0

    if not picked:
        print("Nothing new to review.")
        return 0

    now = dt.datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    today_path = now.strftime("%Y-%m-%dT%H-%M")

    batch: list[tuple[Entry, Verdict]] = []
    pending_paths: list[Path] = []
    judge_errors: list[tuple[Entry, Exception]] = []
    for entry in picked:
        try:
            verdict = judge_with_anthropic(entry)
        except Exception as exc:  # pragma: no cover — surfaced in run summary
            # Abort the entire run on the first auth failure: every subsequent
            # call would fail the same way, and marking unjudged papers as
            # `seen` would permanently skip them once the credential is fixed
            # (which is exactly what produced issues #93 / #95 / #96).
            if _is_auth_error(exc):
                print(
                    "FATAL: anthropic auth failed — aborting run without writing state "
                    f"or opening an issue. Fix ANTHROPIC_API_KEY and retry. "
                    f"({type(exc).__name__}: {exc})",
                    file=sys.stderr,
                )
                raise JudgeAuthError(str(exc)) from exc
            print(f"WARN: judge failed for {entry.title!r}: {exc}", file=sys.stderr)
            judge_errors.append((entry, exc))
            # Skip this entry entirely: don't add to batch, don't mark seen.
            # Tomorrow's run will pick it up again so we don't silently lose it.
            continue
        batch.append((entry, verdict))
        if verdict.relevant:
            pending_paths.append(write_pending(entry, verdict, today))
        # Mark seen only after a successful judge call so we don't permanently
        # skip a paper that failed transiently.
        state["seen"][entry.key] = {
            "title": entry.title,
            "date": entry.date,
            "venue": entry.venue,
            "url": entry.url,
            "first_seen_utc": now.isoformat(timespec="seconds") + "Z",
            "relevant": verdict.relevant,
        }

    if not batch:
        # Every paper errored individually (rate limits, parse errors, etc).
        # Don't open a misleading "0 candidates" issue — exit non-zero so the
        # workflow shows red and the maintainer notices.
        err_lines = "\n".join(f"  - {e.title!r}: {exc}" for e, exc in judge_errors)
        print(
            f"FATAL: all {len(picked)} papers failed to be judged this run:\n{err_lines}",
            file=sys.stderr,
        )
        return 3

    research_path = write_research(today_path, [(e, v) for e, v in batch], args.source_url)

    state["runs"].append(
        {
            "run_utc": now.isoformat(timespec="seconds") + "Z",
            "picked": len(picked),
            "relevant": sum(1 for _, v in batch if v.relevant),
            "research": research_path.relative_to(REPO_ROOT).as_posix(),
        }
    )
    save_state(state)

    if not args.no_issue:
        try:
            open_issue(today, batch, research_path, pending_paths)
        except subprocess.CalledProcessError as exc:
            print(f"WARN: gh issue create failed: {exc}", file=sys.stderr)

    print(
        f"Done. Reviewed {len(batch)} | relevant {len(pending_paths)} | "
        f"research: {research_path.relative_to(REPO_ROOT)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except JudgeAuthError:
        # Already logged a clear FATAL above. Exit 4 so the workflow step
        # fails red without dumping a noisy Python traceback.
        raise SystemExit(4)
