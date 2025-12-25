"""
Generate PDF-ready HTML from Markdown documentation.

This script converts the Transaction API Troubleshooting Guide
to a well-formatted HTML file that can be:
1. Opened in a browser and printed to PDF
2. Shared directly as HTML

Usage:
    python scripts/generate_pdf_doc.py

Output:
    docs/P21_Transaction_API_Troubleshooting_Guide.html
"""

import markdown
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
MD_FILE = PROJECT_DIR / "docs" / "P21_Transaction_API_Troubleshooting_Guide.md"
HTML_FILE = PROJECT_DIR / "docs" / "P21_Transaction_API_Troubleshooting_Guide.html"

# HTML template with professional styling for PDF
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>P21 Transaction API Troubleshooting Guide</title>
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

        .warning {{
            background: #fef9e7;
            border-left: 4px solid #f4d03f;
            padding: 15px;
            margin: 20px 0;
        }}

        .info {{
            background: #eaf2f8;
            border-left: 4px solid #2874a6;
            padding: 15px;
            margin: 20px 0;
        }}

        a {{
            color: #2874a6;
        }}

        /* Header styling */
        .doc-header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px double #2874a6;
        }}

        .doc-header h1 {{
            border: none;
            margin-bottom: 10px;
        }}

        .doc-meta {{
            color: #666;
            font-size: 0.9em;
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

        /* TOC styling */
        .toc {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-radius: 5px;
            margin: 20px 0;
        }}

        .toc h2 {{
            margin-top: 0;
            border: none;
        }}

        .toc ul {{
            margin: 0;
            padding-left: 20px;
        }}

        .toc li {{
            margin: 8px 0;
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


def convert_md_to_html():
    """Convert markdown file to PDF-ready HTML."""
    print(f"Reading: {MD_FILE}")

    # Read markdown content
    md_content = MD_FILE.read_text(encoding='utf-8')

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
    full_html = HTML_TEMPLATE.format(content=html_content)

    # Write output
    HTML_FILE.write_text(full_html, encoding='utf-8')

    print(f"Generated: {HTML_FILE}")
    print(f"\nTo create PDF:")
    print(f"  1. Open the HTML file in a browser")
    print(f"  2. Click 'Print / Save as PDF' button")
    print(f"  3. Or use Ctrl+P and select 'Save as PDF'")

    return HTML_FILE


if __name__ == "__main__":
    output = convert_md_to_html()
    print(f"\nDone! Open in browser: file:///{output.as_posix()}")
