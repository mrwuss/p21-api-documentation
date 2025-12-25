"""
Generate PDF-ready HTML from Markdown documentation.

This script converts all markdown files in the docs/ folder
to well-formatted HTML files that can be:
1. Opened in a browser and printed to PDF
2. Shared directly as HTML

Usage:
    python scripts/generate_html.py           # Convert all docs
    python scripts/generate_html.py <file>    # Convert specific file

Output:
    docs/html/<filename>.html
"""

import sys
import markdown
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DOCS_DIR = PROJECT_DIR / "docs"
HTML_DIR = DOCS_DIR / "html"

# HTML template with professional styling for PDF
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @media print {{
            body {{
                font-size: 10pt;
                padding: 0;
                margin: 0;
            }}
            h1 {{
                page-break-after: avoid;
                margin-top: 0;
            }}
            h2 {{
                page-break-after: avoid;
                margin-top: 20pt;
            }}
            h3 {{
                page-break-after: avoid;
                margin-top: 15pt;
            }}
            pre, table, blockquote {{
                page-break-inside: avoid;
            }}
            p {{
                orphans: 3;
                widows: 3;
            }}
            .no-print {{ display: none; }}
            hr {{
                margin: 15pt 0;
            }}
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
            color: #333;
            background: #fff;
        }}

        h1 {{
            color: #1a5276;
            border-bottom: 3px solid #1a5276;
            padding-bottom: 15px;
            margin-bottom: 30px;
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

        /* Print button */
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2874a6;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}

        .print-btn:hover {{
            background: #1a5276;
        }}
    </style>
</head>
<body>
    <button class="print-btn no-print" onclick="window.print()">
        Print / Save as PDF
    </button>

    {content}

    <script>
        // Add IDs to headers for TOC linking
        document.querySelectorAll('h2, h3').forEach(function(header) {{
            if (!header.id) {{
                header.id = header.textContent.toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/(^-|-$)/g, '');
            }}
        }});
    </script>
</body>
</html>
"""


def convert_md_to_html(md_file: Path) -> Path:
    """Convert a markdown file to PDF-ready HTML."""
    print(f"Converting: {md_file.name}")

    # Read markdown content
    md_content = md_file.read_text(encoding='utf-8')

    # Extract title from first heading or filename
    title = md_file.stem.replace("-", " ").replace("_", " ")
    for line in md_content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Configure markdown extensions
    md = markdown.Markdown(
        extensions=[
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'meta'
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': False
            }
        }
    )

    # Convert to HTML
    html_content = md.convert(md_content)

    # Wrap in template
    full_html = HTML_TEMPLATE.format(title=title, content=html_content)

    # Ensure output directory exists
    HTML_DIR.mkdir(exist_ok=True)

    # Write output
    html_file = HTML_DIR / f"{md_file.stem}.html"
    html_file.write_text(full_html, encoding='utf-8')

    return html_file


def convert_all_docs():
    """Convert all markdown files in docs/ to HTML."""
    md_files = list(DOCS_DIR.glob("*.md"))

    if not md_files:
        print("No markdown files found in docs/")
        return

    print(f"Found {len(md_files)} markdown files\n")

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
        html_file = convert_md_to_html(md_file)
        print(f"\nGenerated: {html_file}")
        print(f"Open in browser: file:///{html_file.as_posix()}")
    else:
        # Convert all docs
        convert_all_docs()
