"""
Generate HTML documentation with sidebar navigation.

This script converts all markdown files in the docs/ folder
to HTML files with:
1. Left sidebar with page index and on-page table of contents
2. Sticky navigation that scrolls with the user
3. Cross-page links (.md -> .html) with anchor support
4. Print-friendly styling

Usage:
    python scripts/generate_html.py           # Convert all docs
    python scripts/generate_html.py <file>    # Convert specific file

Output:
    docs/html/<filename>.html
"""

import re
import sys
import markdown
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DOCS_DIR = PROJECT_DIR / "docs"
HTML_DIR = DOCS_DIR / "html"

# Page index: (filename_stem, display_title)
# Generated dynamically from markdown files
PAGE_INDEX: list[tuple[str, str]] = []


def extract_title(md_file: Path) -> str:
    """Extract the first H1 title from a markdown file."""
    content = md_file.read_text(encoding="utf-8")
    for line in content.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return md_file.stem.replace("-", " ").replace("_", " ")


def build_page_index() -> list[tuple[str, str]]:
    """Build sorted list of (stem, title) for all doc pages."""
    pages = []
    for md_file in sorted(DOCS_DIR.glob("*.md")):
        title = extract_title(md_file)
        pages.append((md_file.stem, title))
    return pages


def build_sidebar_html(current_stem: str, toc_html: str) -> str:
    """Build the sidebar HTML with page index and on-page ToC."""
    nav_items = []
    for stem, title in PAGE_INDEX:
        active = ' class="active"' if stem == current_stem else ""
        nav_items.append(f'        <li{active}><a href="{stem}.html">{title}</a></li>')
    nav_list = "\n".join(nav_items)

    return f"""    <nav class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <strong>P21 API Docs</strong>
        </div>
        <div class="sidebar-section">
            <div class="sidebar-section-title">Pages</div>
            <ul class="nav-pages">
{nav_list}
            </ul>
        </div>
        <div class="sidebar-section page-toc-section">
            <div class="sidebar-section-title">On This Page</div>
            <div class="page-toc" id="page-toc">
                {toc_html}
            </div>
        </div>
    </nav>"""


def get_html_template(title: str, sidebar_html: str, content: str) -> str:
    """Return the full HTML page with sidebar layout."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - P21 API Documentation</title>
    <style>
        /* ===== Reset & Base ===== */
        * {{ box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            color: #333;
            background: #f5f6fa;
            display: flex;
        }}

        /* ===== Sidebar ===== */
        .sidebar {{
            width: 280px;
            min-width: 280px;
            height: 100vh;
            position: sticky;
            top: 0;
            background: #1a2332;
            color: #c8d6e5;
            overflow-y: auto;
            padding: 0;
            font-size: 0.875rem;
            flex-shrink: 0;
        }}

        .sidebar-header {{
            padding: 20px 16px 16px;
            font-size: 1.05rem;
            color: #fff;
            border-bottom: 1px solid #2c3e50;
        }}

        .sidebar-section {{
            padding: 12px 0 4px;
        }}

        .sidebar-section-title {{
            padding: 0 16px 6px;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #6b7f95;
            font-weight: 600;
        }}

        .nav-pages {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}

        .nav-pages li a {{
            display: block;
            padding: 5px 16px;
            color: #a0b4c8;
            text-decoration: none;
            border-left: 3px solid transparent;
            transition: background 0.15s, color 0.15s;
        }}

        .nav-pages li a:hover {{
            background: #232f3e;
            color: #e8eef4;
        }}

        .nav-pages li.active a {{
            color: #fff;
            background: #232f3e;
            border-left-color: #3498db;
            font-weight: 600;
        }}

        /* Page ToC in sidebar */
        .page-toc {{
            padding: 0 8px;
        }}

        .page-toc ul {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}

        .page-toc li {{
            margin: 0;
        }}

        .page-toc a {{
            display: block;
            padding: 3px 8px;
            color: #8a9bb5;
            text-decoration: none;
            font-size: 0.82rem;
            border-left: 2px solid transparent;
            transition: color 0.15s;
        }}

        .page-toc a:hover {{
            color: #e8eef4;
        }}

        .page-toc a.active {{
            color: #3498db;
            border-left-color: #3498db;
        }}

        /* Indent h3 items */
        .page-toc .toc-h3 {{
            padding-left: 20px;
            font-size: 0.78rem;
        }}

        .page-toc-section {{
            border-top: 1px solid #2c3e50;
        }}

        /* ===== Main Content ===== */
        .content {{
            flex: 1;
            max-width: 920px;
            margin: 0 auto;
            padding: 40px 48px;
            background: #fff;
            min-height: 100vh;
        }}

        h1 {{
            color: #1a5276;
            border-bottom: 3px solid #1a5276;
            padding-bottom: 15px;
            margin-bottom: 30px;
            margin-top: 0;
        }}

        h2 {{
            color: #2874a6;
            border-bottom: 2px solid #aed6f1;
            padding-bottom: 10px;
            margin-top: 40px;
        }}

        h3 {{
            color: #2e86c1;
            margin-top: 25px;
        }}

        h4 {{
            color: #34495e;
            margin-top: 20px;
        }}

        code {{
            background: #f4f6f7;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }}

        pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85em;
            line-height: 1.4;
        }}

        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95em;
        }}

        th {{
            background: #2874a6;
            color: white;
            padding: 12px;
            text-align: left;
        }}

        td {{
            border: 1px solid #ddd;
            padding: 10px;
        }}

        tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        blockquote {{
            border-left: 4px solid #2874a6;
            margin: 20px 0;
            padding: 15px 20px;
            background: #eaf2f8;
            font-style: italic;
        }}

        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 30px 0;
        }}

        a {{
            color: #2874a6;
        }}

        /* ===== Print ===== */
        @media print {{
            body {{
                display: block;
                background: #fff;
            }}
            .sidebar {{
                display: none;
            }}
            .content {{
                max-width: 100%;
                padding: 0;
                margin: 0;
            }}
            .print-btn {{
                display: none;
            }}
            h1 {{ page-break-after: avoid; margin-top: 0; }}
            h2 {{ page-break-after: avoid; margin-top: 20pt; }}
            h3 {{ page-break-after: avoid; margin-top: 15pt; }}
            pre, table, blockquote {{ page-break-inside: avoid; }}
            p {{ orphans: 3; widows: 3; }}
        }}

        /* ===== Mobile ===== */
        @media (max-width: 900px) {{
            body {{
                display: block;
            }}
            .sidebar {{
                width: 100%;
                min-width: unset;
                height: auto;
                position: relative;
            }}
            .content {{
                padding: 20px;
            }}
        }}

        /* Print button */
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2874a6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 13px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 100;
        }}

        .print-btn:hover {{
            background: #1a5276;
        }}
    </style>
</head>
<body>
{sidebar_html}

    <main class="content">
        <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
{content}
    </main>

    <script>
        // Add IDs to headers for linking
        document.querySelectorAll('h2, h3, h4').forEach(function(header) {{
            if (!header.id) {{
                header.id = header.textContent.toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/(^-|-$)/g, '');
            }}
        }});

        // Highlight current ToC item on scroll
        (function() {{
            var tocLinks = document.querySelectorAll('.page-toc a');
            if (!tocLinks.length) return;

            var headers = [];
            tocLinks.forEach(function(link) {{
                var id = link.getAttribute('href');
                if (id && id.startsWith('#')) {{
                    var el = document.getElementById(id.slice(1));
                    if (el) headers.push({{ el: el, link: link }});
                }}
            }});

            function updateActive() {{
                var scrollY = window.scrollY + 80;
                var active = null;
                for (var i = 0; i < headers.length; i++) {{
                    if (headers[i].el.offsetTop <= scrollY) {{
                        active = headers[i];
                    }}
                }}
                tocLinks.forEach(function(l) {{ l.classList.remove('active'); }});
                if (active) active.link.classList.add('active');
            }}

            window.addEventListener('scroll', updateActive, {{ passive: true }});
            updateActive();
        }})();
    </script>
</body>
</html>"""


def convert_md_to_html(md_file: Path) -> Path:
    """Convert a markdown file to HTML with sidebar navigation."""
    print(f"Converting: {md_file.name}")

    # Read markdown content
    md_content = md_file.read_text(encoding="utf-8")

    # Convert internal .md links to .html links (handles #anchors)
    md_content = re.sub(
        r"\]\((\d{2}-[^)#]+)\.md(#[^)]+)?\)",
        r"](\1.html\2)",
        md_content,
    )

    # Extract title from first heading or filename
    title = md_file.stem.replace("-", " ").replace("_", " ")
    for line in md_content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Configure markdown extensions
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "toc", "meta"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False},
            "toc": {"toc_depth": "2-3"},
        },
    )

    # Convert to HTML
    html_content = md.convert(md_content)

    # Get the generated ToC and add CSS classes for h3 indentation
    toc_html = getattr(md, "toc", "")
    # Add toc-h3 class to nested list items (h3 level)
    # The toc extension nests h3 inside a <ul> under h2 <li>
    # We add a class to the inner <a> tags for styling
    toc_html = re.sub(
        r"(<li><ul>\s*<li>)(.*?)(</li>)",
        lambda m: m.group(0).replace("<a ", '<a class="toc-h3" '),
        toc_html,
        flags=re.DOTALL,
    )

    # Build sidebar
    sidebar_html = build_sidebar_html(md_file.stem, toc_html)

    # Wrap in template
    full_html = get_html_template(title, sidebar_html, html_content)

    # Write output
    HTML_DIR.mkdir(exist_ok=True)
    html_file = HTML_DIR / f"{md_file.stem}.html"
    html_file.write_text(full_html, encoding="utf-8")

    return html_file


def convert_all_docs():
    """Convert all markdown files in docs/ to HTML."""
    global PAGE_INDEX
    md_files = list(DOCS_DIR.glob("*.md"))

    if not md_files:
        print("No markdown files found in docs/")
        return

    print(f"Found {len(md_files)} markdown files\n")

    # Build page index first (needed by all pages)
    PAGE_INDEX = build_page_index()

    for md_file in sorted(md_files):
        html_file = convert_md_to_html(md_file)
        print(f"  -> {html_file.name}")

    print(f"\nGenerated {len(md_files)} HTML files in docs/html/")
    print("\nTo create PDF:")
    print("  1. Open the HTML file in a browser")
    print("  2. Click 'Print / Save as PDF' button")
    print("  3. Or use Ctrl+P and select 'Save as PDF'")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Convert specific file
        md_file = Path(sys.argv[1])
        if not md_file.exists():
            md_file = DOCS_DIR / sys.argv[1]
        if not md_file.exists():
            print(f"File not found: {sys.argv[1]}")
            sys.exit(1)
        PAGE_INDEX = build_page_index()
        html_file = convert_md_to_html(md_file)
        print(f"\nGenerated: {html_file}")
        print(f"Open in browser: file:///{html_file.as_posix()}")
    else:
        # Convert all docs
        convert_all_docs()
