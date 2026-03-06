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

# ---------------------------------------------------------------------------
# Tab infrastructure for multi-language code blocks
# ---------------------------------------------------------------------------

TAB_START = "CODETABS_START_9x7k2m"
TAB_END = "CODETABS_END_9x7k2m"
TAB_LANG = "CODETAB_LANG_9x7k2m"  # language marker: CODETAB_LANG_9x7k2m:python

LANG_DISPLAY = {
    "python": "Python",
    "csharp": "C#",
    "cs": "C#",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "bash": "Bash",
    "shell": "Shell",
    "json": "JSON",
    "xml": "XML",
    "http": "HTTP",
    "text": "Text",
    "sql": "SQL",
    "powershell": "PowerShell",
}

LANG_KEY_NORMALIZE = {
    "cs": "csharp",
    "js": "javascript",
    "ts": "typescript",
}


def preprocess_tabs(md_content: str) -> str:
    """Replace tab markers with sentinels, tagging each code block with its language.

    Inside <!-- tabs --> regions, each ```lang block gets a language sentinel
    injected before it so we can recover the language after codehilite strips it.
    """
    result_parts = []
    remaining = md_content

    while "<!-- tabs -->" in remaining:
        before, _, rest = remaining.partition("<!-- tabs -->")
        result_parts.append(before)

        if "<!-- /tabs -->" in rest:
            inside, _, after = rest.partition("<!-- /tabs -->")
        else:
            # No closing tag — treat rest as inside
            inside = rest
            after = ""

        # Tag each fenced code block with its language
        tagged = f"\n{TAB_START}\n"
        for m in re.finditer(r"```(\w+)\s*\n", inside):
            lang = m.group(1)
            # Insert language sentinel before the code fence
            tagged_block = f"\n{TAB_LANG}:{lang}\n\n```{lang}\n"
            inside = inside.replace(m.group(0), tagged_block, 1)
        tagged += inside + f"\n{TAB_END}\n"

        result_parts.append(tagged)
        remaining = after

    result_parts.append(remaining)
    return "".join(result_parts)


def _build_tab_html(tabs: list[tuple[str, str]]) -> str:
    """Build tabbed code block HTML from list of (lang, block_html) tuples."""
    buttons = []
    panels = []
    for i, (lang, block_html) in enumerate(tabs):
        key = LANG_KEY_NORMALIZE.get(lang, lang)
        display = LANG_DISPLAY.get(lang, lang.title())
        active = " active" if i == 0 else ""
        buttons.append(
            f'<button class="tab-btn{active}" data-lang="{key}">{display}</button>'
        )
        panels.append(
            f'<div class="tab-panel{active}" data-lang="{key}">\n{block_html}\n</div>'
        )

    return (
        '<div class="code-tabs">\n'
        '  <div class="tab-buttons">\n    '
        + "\n    ".join(buttons)
        + "\n  </div>\n  "
        + "\n  ".join(panels)
        + "\n</div>"
    )


def postprocess_tabs(html_content: str) -> str:
    """Convert sentinel-wrapped code blocks into tabbed containers."""
    start_re = re.compile(
        rf"<p>\s*{re.escape(TAB_START)}\s*</p>|{re.escape(TAB_START)}"
    )
    end_re = re.compile(
        rf"<p>\s*{re.escape(TAB_END)}\s*</p>|{re.escape(TAB_END)}"
    )

    # Language sentinel pattern (becomes <p>CODETAB_LANG_9x7k2m:python</p>)
    lang_sentinel_re = re.compile(
        rf"<p>\s*{re.escape(TAB_LANG)}:(\w+)\s*</p>|{re.escape(TAB_LANG)}:(\w+)"
    )

    # Code block pattern: <pre> blocks, possibly wrapped in <div class="highlight">
    code_block_re = re.compile(
        r'(?:<div[^>]*class="[^"]*highlight[^"]*"[^>]*>\s*)?'
        r"<pre>.*?</pre>"
        r"(?:\s*</div>)?",
        re.DOTALL,
    )

    while True:
        start_match = start_re.search(html_content)
        if not start_match:
            break
        end_match = end_re.search(html_content, start_match.end())
        if not end_match:
            html_content = (
                html_content[: start_match.start()] + html_content[start_match.end() :]
            )
            continue

        between = html_content[start_match.end() : end_match.start()]

        # Extract languages from sentinels (in order)
        langs = [
            m.group(1) or m.group(2) for m in lang_sentinel_re.finditer(between)
        ]

        # Remove language sentinels from the between content
        between_clean = lang_sentinel_re.sub("", between)

        # Find all code blocks
        blocks = code_block_re.findall(between_clean)

        # Pair languages with blocks
        tabs = []
        for i, block_html in enumerate(blocks):
            lang = langs[i] if i < len(langs) else "text"
            tabs.append((lang, block_html))

        if len(tabs) >= 2:
            replacement = _build_tab_html(tabs)
        else:
            replacement = between_clean.strip()

        html_content = (
            html_content[: start_match.start()]
            + replacement
            + html_content[end_match.end() :]
        )

    # Clean up any stray sentinels
    html_content = lang_sentinel_re.sub("", html_content)

    return html_content


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
            <a href="index.html" style="color: inherit; text-decoration: none;"><strong>P21 API Docs</strong></a>
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
            .tab-buttons {{ display: none; }}
            .tab-panel {{ display: block !important; }}
            .tab-panel::before {{
                content: attr(data-lang);
                display: block;
                font-weight: bold;
                color: #333;
                font-size: 0.85em;
                margin-bottom: 2px;
                text-transform: uppercase;
            }}
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

        /* ===== Code Tabs ===== */
        .code-tabs {{
            margin: 20px 0;
        }}

        .tab-buttons {{
            display: flex;
            gap: 0;
            margin-bottom: 0;
        }}

        .tab-btn {{
            padding: 7px 16px;
            border: none;
            background: #1a2836;
            color: #8a9bb5;
            cursor: pointer;
            font-size: 0.8em;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            border-radius: 5px 5px 0 0;
            transition: background 0.15s, color 0.15s;
        }}

        .tab-btn:hover {{
            background: #243447;
            color: #c8d6e5;
        }}

        .tab-btn.active {{
            background: #2c3e50;
            color: #ecf0f1;
            font-weight: 600;
        }}

        .tab-panel {{
            display: none;
        }}

        .tab-panel.active {{
            display: block;
        }}

        .code-tabs .tab-panel pre {{
            margin-top: 0;
            border-radius: 0 5px 5px 5px;
        }}

        .code-tabs .tab-panel:first-of-type pre {{
            border-radius: 0 5px 5px 5px;
        }}

        .code-tabs .tab-panel:last-of-type pre {{
            border-radius: 0 0 5px 5px;
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

        // Code tab switching with global language sync + localStorage persistence
        (function() {{
            var savedLang = localStorage.getItem('p21-docs-lang');

            document.querySelectorAll('.code-tabs').forEach(function(container) {{
                var buttons = container.querySelectorAll('.tab-btn');
                var panels = container.querySelectorAll('.tab-panel');

                // Restore saved language preference
                if (savedLang) {{
                    var target = container.querySelector('.tab-btn[data-lang="' + savedLang + '"]');
                    if (target) {{
                        buttons.forEach(function(b) {{ b.classList.remove('active'); }});
                        panels.forEach(function(p) {{ p.classList.remove('active'); }});
                        target.classList.add('active');
                        var panel = container.querySelector('.tab-panel[data-lang="' + savedLang + '"]');
                        if (panel) panel.classList.add('active');
                    }}
                }}

                // Click handlers
                buttons.forEach(function(btn) {{
                    btn.addEventListener('click', function() {{
                        var lang = this.getAttribute('data-lang');
                        localStorage.setItem('p21-docs-lang', lang);

                        // Switch ALL tab groups on the page to this language
                        document.querySelectorAll('.code-tabs').forEach(function(c) {{
                            var cBtns = c.querySelectorAll('.tab-btn');
                            var cPanels = c.querySelectorAll('.tab-panel');
                            var hasLang = c.querySelector('.tab-btn[data-lang="' + lang + '"]');
                            if (hasLang) {{
                                cBtns.forEach(function(b) {{ b.classList.remove('active'); }});
                                cPanels.forEach(function(p) {{ p.classList.remove('active'); }});
                                hasLang.classList.add('active');
                                var p = c.querySelector('.tab-panel[data-lang="' + lang + '"]');
                                if (p) p.classList.add('active');
                            }}
                        }});
                    }});
                }});
            }});
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

    # Replace tab markers with sentinels (before markdown conversion)
    md_content = preprocess_tabs(md_content)

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

    # Convert tab sentinels into tabbed code block containers
    html_content = postprocess_tabs(html_content)

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


def generate_index_page():
    """Generate index.html using the same sidebar template as other pages."""
    # Page descriptions for the landing page content
    page_info = {
        "00-Authentication": ("Authentication", "Token generation, credentials vs consumer keys, V1 and V2 endpoints, and token refresh patterns."),
        "01-API-Selection-Guide": ("API Selection Guide", "Decision tree and comparison table to help you choose the right API for your use case."),
        "02-OData-API": ("OData API", "Query any P21 table using standard OData v3 protocol. Filtering, pagination, and complex queries.", "READ"),
        "03-Transaction-API": ("Transaction API", "Stateless bulk operations for creating and updating records. Service discovery and async operations.", "WRITE"),
        "04-Interactive-API": ("Interactive API", "Stateful window interactions with full business logic. Sessions, windows, and response handling.", "READ/WRITE"),
        "05-Entity-API": ("Entity API", "Simple REST operations on customers, vendors, contacts, and addresses.", "CRUD"),
        "06-Error-Handling": ("Error Handling", "HTTP status codes, API-specific errors, Python error handling patterns, and debugging tips."),
        "07-Session-Pool-Troubleshooting": ("Session Pool Issues", "Diagnosing and fixing Transaction API session pool contamination and related problems."),
        "08-SalesPricePage-Codes": ("SalesPricePage Codes", "Dropdown code mappings for the Sales Price Page window in the Interactive API."),
        "09-Batch-Processing-Patterns": ("Batch Processing Patterns", "Production patterns for bulk operations: session batching, error recovery, and async client."),
        "10-Changelog": ("Changelog", "Complete history of changes, additions, and contributors to this documentation project."),
        "11-Inventory-REST-API": ("Inventory REST API", "Inventory item CRUD and multi-company workflows. Read inv_loc data, append locations and suppliers.", "CRUD"),
    }

    # Build sections
    getting_started = ["00-Authentication", "01-API-Selection-Guide"]
    api_reference = ["02-OData-API", "03-Transaction-API", "04-Interactive-API", "05-Entity-API", "11-Inventory-REST-API"]
    troubleshooting = ["06-Error-Handling", "07-Session-Pool-Troubleshooting", "08-SalesPricePage-Codes", "09-Batch-Processing-Patterns", "10-Changelog"]

    def make_card(stem):
        info = page_info.get(stem, (stem, ""))
        title = info[0]
        desc = info[1]
        badge = info[2] if len(info) > 2 else None
        badge_html = ""
        if badge:
            badge_class = "badge-read" if badge == "READ" else "badge-write" if badge == "WRITE" else "badge-both"
            badge_html = f' <span class="badge {badge_class}">{badge}</span>'
        return f"""<a href="{stem}.html" class="index-card">
            <h3>{title}{badge_html}</h3>
            <p>{desc}</p>
        </a>"""

    cards_getting_started = "\n".join(make_card(s) for s in getting_started)
    cards_api = "\n".join(make_card(s) for s in api_reference)
    cards_troubleshooting = "\n".join(make_card(s) for s in troubleshooting)

    content = f"""
<h1 id="p21-api-documentation">P21 API Documentation</h1>
<p class="index-subtitle">Comprehensive guides and examples for Epicor Prophet 21 APIs</p>
<blockquote>
<strong>Disclaimer:</strong> This is unofficial, community-created documentation.
It is not affiliated with, endorsed by, or supported by Epicor Software Corporation.
All trademarks are property of their respective owners. Use at your own risk.
</blockquote>

<h2 id="getting-started">Getting Started</h2>
<div class="index-grid">
{cards_getting_started}
</div>

<h2 id="api-reference">API Reference</h2>
<div class="index-grid">
{cards_api}
</div>

<h2 id="troubleshooting-reference">Troubleshooting &amp; Reference</h2>
<div class="index-grid">
{cards_troubleshooting}
</div>

<hr>
<p style="text-align: center; color: #666;">
<a href="https://github.com/mrwuss/p21-api-documentation">View on GitHub</a>
</p>

<style>
.index-subtitle {{
    font-size: 1.15em;
    color: #555;
    margin-top: -20px;
    margin-bottom: 30px;
}}
.index-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 30px;
}}
.index-card {{
    display: block;
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    text-decoration: none;
    color: inherit;
    transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}}
.index-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border-color: #2874a6;
}}
.index-card h3 {{
    color: #1a5276;
    margin: 0 0 8px 0;
    font-size: 1.1em;
    border: none;
    padding: 0;
}}
.index-card p {{
    color: #666;
    margin: 0;
    font-size: 0.9em;
    line-height: 1.5;
}}
.badge {{
    display: inline-block;
    padding: 2px 7px;
    border-radius: 3px;
    font-size: 0.7em;
    font-weight: bold;
    margin-left: 6px;
    vertical-align: middle;
}}
.badge-read {{ background: #3498db; color: white; }}
.badge-write {{ background: #e74c3c; color: white; }}
.badge-both {{ background: #9b59b6; color: white; }}
</style>
"""

    # Build ToC for the index page
    toc_html = """<ul>
<li><a href="#getting-started">Getting Started</a></li>
<li><a href="#api-reference">API Reference</a></li>
<li><a href="#troubleshooting-reference">Troubleshooting &amp; Reference</a></li>
</ul>"""

    sidebar_html = build_sidebar_html("__index__", toc_html)
    full_html = get_html_template("Home", sidebar_html, content)

    index_file = HTML_DIR / "index.html"
    index_file.write_text(full_html, encoding="utf-8")
    return index_file


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

    # Generate index page
    index_file = generate_index_page()
    print(f"\nGenerated index: {index_file.name}")

    print(f"\nGenerated {len(md_files) + 1} HTML files in docs/html/")
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
