"""Validate every internal anchor link in docs/ against the generated HTML.

Markdown headings become HTML ids via python-markdown's slugifier, and the two
do not always agree with what a human would guess -- an em dash in a heading
collapses to a single hyphen, so `## Foo -- Bar` becomes `#foo-bar`, not
`#foo--bar`. Hand-written links get this wrong silently: the markdown renders
fine on GitHub and the published page 404s on the fragment.

Run after scripts/generate_html.py; exits non-zero if any link is broken.

Usage:
    python scripts/generate_html.py && python scripts/check_anchors.py
"""

import glob
import io
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parent.parent
HTML_DIR = PROJECT_DIR / "docs" / "html"

# Source stems whose output file is renamed (see generate_html.OUT_STEM_MAP).
OUT_STEM_MAP = {"INDEX.html": "task-index.html"}

LINK_RE = re.compile(r"\]\((?:docs/)?([0-9A-Za-z\-\./]*\.md)?#([a-z0-9\-]+)\)")


def collect_anchors() -> dict[str, set[str]]:
    """Map each generated HTML file (relative to html/) to the ids it defines."""
    anchors: dict[str, set[str]] = {}
    for path in glob.glob(str(HTML_DIR / "*.html")) + glob.glob(
        str(HTML_DIR / "recipes" / "*.html")
    ):
        text = io.open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, HTML_DIR).replace(os.sep, "/")
        anchors[rel] = set(re.findall(r'id="([^"]+)"', text))
    return anchors


def source_files() -> list[str]:
    """Markdown files whose internal links should resolve."""
    os.chdir(PROJECT_DIR)
    return (
        glob.glob("docs/*.md")
        + glob.glob("docs/recipes/*.md")
        + ["CLAUDE.md"]
    )


def main() -> int:
    """Check every anchor link; report and return 1 on any failure."""
    if not HTML_DIR.is_dir():
        print("docs/html/ not found -- run scripts/generate_html.py first")
        return 1

    anchors = collect_anchors()
    broken: list[tuple[str, str, str]] = []

    for md in source_files():
        text = io.open(md, encoding="utf-8").read()
        # CLAUDE.md links are docs/-prefixed; docs pages are relative to themselves.
        base = "docs" if md == "CLAUDE.md" else os.path.dirname(md).replace(os.sep, "/")
        for match in LINK_RE.finditer(text):
            target, frag = match.group(1), match.group(2)
            if md == "CLAUDE.md" and not target:
                continue  # CLAUDE.md has no generated page of its own
            target = target or os.path.basename(md)
            html = (
                os.path.normpath(os.path.join(base, target))
                .replace(os.sep, "/")
                .replace(".md", ".html")
                .replace("docs/", "")
            )
            html = OUT_STEM_MAP.get(html, html)
            if html not in anchors:
                broken.append((md, f"{target}#{frag}", "no such page"))
            elif frag not in anchors[html]:
                broken.append((md, f"{target}#{frag}", "no such anchor"))

    if broken:
        print(f"BROKEN ANCHOR LINKS: {len(broken)}\n")
        for md, link, why in broken:
            print(f"  {md}\n    -> {link}  ({why})")
        print("\nTip: an em dash in a heading collapses to ONE hyphen in the id.")
        return 1

    total = sum(len(v) for v in anchors.values())
    print(f"OK -- every internal anchor resolves ({total} ids across {len(anchors)} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
