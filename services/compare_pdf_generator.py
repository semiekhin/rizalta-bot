#!/usr/bin/env python3
"""
Генератор PDF для сравнения Депозит vs RIZALTA
"""

import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from services.deposit_calculator import calculate_all_scenarios
from services.investment_compare import calculate_rizalta, pluralize_years


def fmt(value: float) -> str:
    """Форматирует число с пробелами."""
    return f"{int(round(value)):,}".replace(",", " ")


def generate_compare_pdf(amount: int, years: int, username: str = "") -> Optional[str]:
    """
    Генерирует PDF со сравнением депозит vs RIZALTA.
    
    Returns:
        Путь к PDF файлу или None при ошибке.
    """
    # Расчёты
    deposit = calculate_all_scenarios(amount, years)
    rizalta = calculate_rizalta(amount, years)
    
    dep_base = deposit["base"]
    dep_pess = deposit["pessimistic"]
    dep_opt = deposit["optimistic"]
    
    # Преимущество RIZALTA
    advantage = rizalta.total_profit - dep_base.total_net_interest
    advantage_pct = (advantage / amount) * 100
    
    start_year = 2026
    end_year = start_year + years - 1
    
    # HTML шаблон
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 15mm;
        }}
        body {{
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #1a365d;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .logo {{
            font-size: 28pt;
            font-weight: bold;
            color: #1a365d;
            letter-spacing: 2px;
        }}
        .subtitle {{
            font-size: 10pt;
            color: #666;
            margin-top: 5px;
        }}
        h1 {{
            color: #1a365d;
            font-size: 18pt;
            margin: 20px 0 15px 0;
            text-align: center;
        }}
        h2 {{
            color: #1a365d;
            font-size: 14pt;
            margin: 20px 0 10px 0;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        .params {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
        }}
        .params-row {{
            display: inline-block;
            margin: 0 20px;
        }}
        .params-label {{
            color: #666;
            font-size: 10pt;
        }}
        .params-value {{
            font-size: 16pt;
            font-weight: bold;
            color: #1a365d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th {{
            background: #1a365d;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: normal;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .number {{
            text-align: right;
            font-family: monospace;
        }}
        .highlight {{
            background: #e8f5e9 !important;
        }}
        .highlight td {{
            font-weight: bold;
        }}
        .result-box {{
            background: linear-gradient(135deg, #1a365d 0%, #2d4a7c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
        }}
        .result-title {{
            font-size: 12pt;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        .result-value {{
            font-size: 24pt;
            font-weight: bold;
        }}
        .result-sub {{
            font-size: 14pt;
            margin-top: 5px;
            opacity: 0.9;
        }}
        .comparison {{
            display: table;
            width: 100%;
            margin: 20px 0;
        }}
        .comparison-col {{
            display: table-cell;
            width: 48%;
            vertical-align: top;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .comparison-col:first-child {{
            margin-right: 4%;
        }}
        .comparison-col h3 {{
            margin: 0 0 15px 0;
            color: #1a365d;
            font-size: 13pt;
        }}
        .comparison-row {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }}
        .source {{
            font-size: 9pt;
            color: #888;
            font-style: italic;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            border-radius: 5px;
            font-size: 9pt;
            margin-top: 15px;
        }}
    </style>
</head>
<body>

<div class="header">
    <div class="logo">RIZALTA</div>
    <div class="subtitle">Resort Belokurikha · Инвестиционная аналитика</div>
</div>

<h1>Сравнение: Депозит vs Недвижимость</h1>

<div class="params">
    <div class="params-row">
        <div class="params-label">Сумма инвестиции</div>
        <div class="params-value">{fmt(amount)}</div>
    </div>
    <div class="params-row">
        <div class="params-label">Горизонт</div>
        <div class="params-value">{pluralize_years(years)} ({start_year}–{end_year})</div>
    </div>
</div>

<h2>🏦 Банковский депозит</h2>
<p class="source">Источник: ЦБ РФ (cbr.ru/statistics/avgprocstav/), прогноз ключевой ставки</p>

<table>
    <tr>
        <th>Сценарий</th>
        <th class="number">Чистый доход</th>
        <th class="number">Налог</th>
        <th class="number">Капитал</th>
        <th class="number">ROI</th>
    </tr>
    <tr>
        <td>📈 Пессимистичный (высокие ставки)</td>
        <td class="number">+{fmt(dep_pess.total_net_interest)}</td>
        <td class="number">−{fmt(dep_pess.total_tax)}</td>
        <td class="number">{fmt(dep_pess.final_balance)}</td>
        <td class="number">{dep_pess.total_roi_pct:.0f}%</td>
    </tr>
    <tr class="highlight">
        <td>📊 Базовый (прогноз ЦБ)</td>
        <td class="number">+{fmt(dep_base.total_net_interest)}</td>
        <td class="number">−{fmt(dep_base.total_tax)}</td>
        <td class="number">{fmt(dep_base.final_balance)}</td>
        <td class="number">{dep_base.total_roi_pct:.0f}%</td>
    </tr>
    <tr>
        <td>📉 Оптимистичный (быстрое снижение)</td>
        <td class="number">+{fmt(dep_opt.total_net_interest)}</td>
        <td class="number">−{fmt(dep_opt.total_tax)}</td>
        <td class="number">{fmt(dep_opt.final_balance)}</td>
        <td class="number">{dep_opt.total_roi_pct:.0f}%</td>
    </tr>
</table>

<h2>🏡 RIZALTA Resort</h2>
<p class="source">Источник: финансовая модель застройщика</p>

<table>
    <tr>
        <th>Год</th>
        <th class="number">Рост стоимости</th>
        <th class="number">Доход от аренды</th>
        <th class="number">Итого за год</th>
        <th class="number">Стоимость актива</th>
    </tr>"""

    # Добавляем строки по годам
    for yr in rizalta.yearly_results:
        html += f"""
    <tr>
        <td>{yr.year}</td>
        <td class="number">+{fmt(yr.growth_profit)}</td>
        <td class="number">{'+' + fmt(yr.rental_profit) if yr.rental_profit > 0 else '—'}</td>
        <td class="number">+{fmt(yr.total_profit)}</td>
        <td class="number">{fmt(yr.end_value)}</td>
    </tr>"""

    html += f"""
    <tr class="highlight">
        <td><strong>ИТОГО</strong></td>
        <td class="number"><strong>+{fmt(rizalta.total_growth_profit)}</strong></td>
        <td class="number"><strong>+{fmt(rizalta.total_rental_profit)}</strong></td>
        <td class="number"><strong>+{fmt(rizalta.total_profit)}</strong></td>
        <td class="number"><strong>{fmt(rizalta.final_value)}</strong></td>
    </tr>
</table>

<div class="result-box">
    <div class="result-title">ПРЕИМУЩЕСТВО RIZALTA</div>
    <div class="result-value">+{fmt(advantage)}</div>
    <div class="result-sub">+{advantage_pct:.0f}% к вложенному капиталу</div>
</div>

<h2>📊 Итоговое сравнение</h2>

<table>
    <tr>
        <th>Показатель</th>
        <th class="number">Депозит (базовый)</th>
        <th class="number">RIZALTA</th>
        <th class="number">Разница</th>
    </tr>
    <tr>
        <td>Общий доход</td>
        <td class="number">+{fmt(dep_base.total_net_interest)}</td>
        <td class="number">+{fmt(rizalta.total_profit)}</td>
        <td class="number" style="color: #2e7d32; font-weight: bold;">+{fmt(advantage)}</td>
    </tr>
    <tr>
        <td>ROI за период</td>
        <td class="number">{dep_base.total_roi_pct:.0f}%</td>
        <td class="number">{rizalta.total_roi_pct:.0f}%</td>
        <td class="number" style="color: #2e7d32; font-weight: bold;">+{rizalta.total_roi_pct - dep_base.total_roi_pct:.0f}%</td>
    </tr>
    <tr>
        <td>Итоговый капитал</td>
        <td class="number">{fmt(dep_base.final_balance)}</td>
        <td class="number">{fmt(rizalta.final_value + rizalta.total_rental_profit)}</td>
        <td class="number" style="color: #2e7d32; font-weight: bold;">+{fmt(rizalta.final_value + rizalta.total_rental_profit - dep_base.final_balance)}</td>
    </tr>
</table>


<div class="footer">
    <p>RIZALTA Resort Belokurikha · Алтайский край, г. Белокуриха</p>
    <p>Документ сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    <p style="margin-top: 10px; font-size: 8pt;">
        Данный расчёт носит информационный характер и не является публичной офертой.
        Прогнозы доходности основаны на текущих рыночных условиях и могут измениться.
    </p>
</div>

</body>
</html>"""

    # Создаём PDF через wkhtmltopdf
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            html_path = f.name
        
        pdf_path = html_path.replace('.html', '.pdf')
        
        cmd = [
            'wkhtmltopdf',
            '--quiet',
            '--enable-local-file-access',
            '--encoding', 'UTF-8',
            '--page-size', 'A4',
            '--margin-top', '10mm',
            '--margin-bottom', '10mm',
            '--margin-left', '10mm',
            '--margin-right', '10mm',
            html_path,
            pdf_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Удаляем HTML
        os.unlink(html_path)
        
        return pdf_path
        
    except Exception as e:
        print(f"[PDF] Ошибка генерации: {e}")
        return None


if __name__ == "__main__":
    # Тест
    pdf = generate_compare_pdf(15_000_000, 3, "test_user")
    if pdf:
        print(f"PDF создан: {pdf}")
    else:
        print("Ошибка создания PDF")
