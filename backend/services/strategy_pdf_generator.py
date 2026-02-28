"""Strategy PDF generator for RIZALTA investment reports."""

import os
import json
import re
import tempfile
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_strategy_pdf(data: dict) -> str | None:
    """Generate investment strategy PDF from AI chat analysis.

    Args:
        data: dict with keys:
            - user_query: original user question
            - response_text: AI response (markdown-like)
            - tools_used: list of tool names
            - results: dict of tool results

    Returns: path to generated PDF or None
    """
    user_query = data.get("user_query", "")
    response_text = data.get("response_text", "")

    # Format AI response: markdown → HTML
    html_body = _markdown_to_html(response_text)

    date_str = datetime.now().strftime("%d.%m.%Y")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 20mm 15mm 20mm 15mm;
    }}
    body {{
        font-family: 'Arial', sans-serif;
        color: #263524;
        font-size: 12px;
        line-height: 1.6;
    }}
    .header {{
        background: linear-gradient(135deg, #263524 0%, #2F4A2D 100%);
        color: #F2EBD9;
        padding: 30px;
        margin: -20mm -15mm 20px -15mm;
        text-align: center;
    }}
    .header h1 {{
        font-size: 24px;
        margin: 0 0 5px 0;
        color: #D4A84B;
    }}
    .header .subtitle {{
        font-size: 14px;
        color: #F2EBD9;
    }}
    .header .date {{
        font-size: 11px;
        color: #C8BBAA;
        margin-top: 10px;
    }}
    .query-box {{
        background: #f5f3ed;
        border-left: 4px solid #D4A84B;
        padding: 15px 20px;
        margin: 20px 0;
        font-style: italic;
    }}
    h2 {{
        color: #263524;
        border-bottom: 2px solid #D4A84B;
        padding-bottom: 5px;
        margin-top: 30px;
    }}
    h3 {{
        color: #2F4A2D;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }}
    th {{
        background: #263524;
        color: #F2EBD9;
        padding: 8px 12px;
        text-align: left;
    }}
    td {{
        padding: 8px 12px;
        border-bottom: 1px solid #ddd;
    }}
    tr:nth-child(even) {{
        background: #f9f7f2;
    }}
    .footer {{
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #ddd;
        font-size: 10px;
        color: #A89880;
        text-align: center;
    }}
    strong {{ color: #263524; }}
    li {{ margin-bottom: 4px; }}
</style>
</head>
<body>

<div class="header">
    <h1>RIZALTA RESORT BELOKURIKHA</h1>
    <div class="subtitle">Инвестиционная стратегия</div>
    <div class="date">Подготовлено: {date_str} | AI Financial Advisor</div>
</div>

<div class="query-box">
    Запрос инвестора: &laquo;{_escape_html(user_query)}&raquo;
</div>

{html_body}

<div class="footer">
    RIZALTA Resort Belokurikha &mdash; AI Financial Advisor<br>
    Данный отчёт подготовлен автоматически на основе актуальных данных проекта.<br>
    Расчёты носят прогнозный характер и не являются офертой.
</div>

</body>
</html>"""

    try:
        html_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        html_file.write(html)
        html_file.close()

        pdf_path = html_file.name.replace(".html", ".pdf")

        subprocess.run([
            "wkhtmltopdf",
            "--encoding", "utf-8",
            "--page-size", "A4",
            "--margin-top", "0",
            "--margin-bottom", "10mm",
            "--margin-left", "0",
            "--margin-right", "0",
            "--enable-local-file-access",
            html_file.name,
            pdf_path
        ], check=True, capture_output=True, timeout=30)

        os.unlink(html_file.name)
        return pdf_path

    except Exception as e:
        logger.error(f"[STRATEGY PDF] Error: {e}")
        return None


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _markdown_to_html(text: str) -> str:
    """Simple markdown-like to HTML conversion for AI response."""
    lines = text.split("\n")
    html_lines = []

    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3>{_escape_html(line[4:])}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{_escape_html(line[3:])}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{_escape_html(line[2:])}</h1>")
        elif "**" in line:
            line = _escape_html(line)
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            html_lines.append(f"<p>{line}</p>")
        elif line.strip().startswith("- "):
            html_lines.append(f"<li>{_escape_html(line.strip()[2:])}</li>")
        elif line.strip() == "":
            html_lines.append("")
        else:
            html_lines.append(f"<p>{_escape_html(line)}</p>")

    return "\n".join(html_lines)
