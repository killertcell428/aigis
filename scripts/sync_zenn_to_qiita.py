#!/usr/bin/env python3
"""Sync published Zenn articles to Qiita format.

Converts articles/*.md (Zenn) → public/*.md (Qiita) for auto-publishing.
Only syncs articles with `published: true` in Zenn frontmatter.

Usage:
    python scripts/sync_zenn_to_qiita.py          # dry-run
    python scripts/sync_zenn_to_qiita.py --apply   # actually write files

Frontmatter conversion:
    Zenn                          → Qiita
    title: "..."                  → title: "..."
    topics: ["A", "B"]           → tags: [A, B]
    published: true              → ignorePublish: false
    emoji: "..."                 → (removed)
    type: "tech"                 → (removed)
"""

import re
import sys
from pathlib import Path

ARTICLES_DIR = Path("articles")
PUBLIC_DIR = Path("public")

# Zenn-specific syntax to strip (Qiita doesn't support these)
ZENN_ONLY_PATTERNS = [
    (re.compile(r"^:::message\s*$", re.MULTILINE), ""),
    (re.compile(r"^:::$", re.MULTILINE), ""),
    (re.compile(r"^:::details .+$", re.MULTILINE), ""),
]


def parse_zenn_frontmatter(content: str) -> tuple[dict, str]:
    """Parse Zenn frontmatter and return (metadata, body)."""
    if not content.startswith("---"):
        return {}, content

    end = content.index("---", 3)
    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()

    meta = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == "topics":
                # Parse YAML list: ["A", "B", "C"]
                value = [t.strip().strip('"').strip("'")
                         for t in value.strip("[]").split(",")]
            elif key == "published":
                value = value.lower() == "true"
            meta[key] = value

    return meta, body


def to_qiita_frontmatter(meta: dict) -> str:
    """Convert Zenn metadata to Qiita frontmatter."""
    title = meta.get("title", "Untitled")
    topics = meta.get("topics", [])

    lines = [
        "---",
        f"title: {title}",
        "tags:",
    ]
    for topic in topics[:5]:  # Qiita max 5 tags
        lines.append(f"  - {topic}")
    lines += [
        "private: false",
        "updated_at: ''",
        "id: null",
        "organization_url_name: null",
        "slide: false",
        "ignorePublish: false",
        "---",
    ]
    return "\n".join(lines)


def strip_zenn_syntax(body: str) -> str:
    """Remove Zenn-specific markdown syntax."""
    for pattern, replacement in ZENN_ONLY_PATTERNS:
        body = pattern.sub(replacement, body)
    return body


def sync_article(zenn_path: Path, apply: bool = False) -> str | None:
    """Sync a single Zenn article to Qiita format. Returns Qiita path or None."""
    content = zenn_path.read_text(encoding="utf-8")
    meta, body = parse_zenn_frontmatter(content)

    # Only sync published articles
    if not meta.get("published", False):
        return None

    # Generate Qiita filename (same slug as Zenn)
    qiita_path = PUBLIC_DIR / zenn_path.name

    # Check if already exists with content
    if qiita_path.exists():
        existing = qiita_path.read_text(encoding="utf-8")
        # Check if body content has changed (ignore frontmatter)
        _, existing_body = parse_zenn_frontmatter(existing)
        if existing_body.strip() == strip_zenn_syntax(body).strip():
            return None  # No changes

    # Convert
    qiita_fm = to_qiita_frontmatter(meta)
    qiita_body = strip_zenn_syntax(body)
    qiita_content = f"{qiita_fm}\n\n{qiita_body}\n"

    if apply:
        PUBLIC_DIR.mkdir(exist_ok=True)
        qiita_path.write_text(qiita_content, encoding="utf-8")

    return str(qiita_path)


def main():
    apply = "--apply" in sys.argv

    if not ARTICLES_DIR.exists():
        print("No articles/ directory found.")
        return

    synced = []
    skipped = []

    for zenn_path in sorted(ARTICLES_DIR.glob("*.md")):
        result = sync_article(zenn_path, apply=apply)
        if result:
            synced.append(result)
            print(f"  {'SYNC' if apply else 'WOULD SYNC'}: {zenn_path.name} → {result}")
        else:
            skipped.append(zenn_path.name)

    print(f"\nSynced: {len(synced)}, Skipped: {len(skipped)}")
    if not apply and synced:
        print("Run with --apply to write files.")


if __name__ == "__main__":
    main()
