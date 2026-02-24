"""
Генератор PDF для ипотечного калькулятора RIZALTA.
Совкомбанк — акция "Сниженный платёж".

v1.0 (30.01.2026)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from services.mortgage_calculator import calc_mortgage, get_service_fee
from services.units_db import get_lot_by_code

BASE_DIR = Path(__file__).parent.parent
RESOURCES_DIR = BASE_DIR / "services" / "kp_resources"


def load_resource(filename: str) -> str:
    """Загружает ресурс (base64 шрифты, логотип)."""
    path = RESOURCES_DIR / filename
    return path.read_text().strip() if path.exists() else ""


def fmt(value: int) -> str:
    """Форматирует число с пробелами."""
    return f"{value:,}".replace(",", " ")


def get_building_name(building: int) -> str:
    """Возвращает название корпуса."""
    names = {1: "Family", 2: "Business"}
    return names.get(building, "Family")


def generate_html(lot: Dict[str, Any], calc: Dict[str, Any]) -> str:
    """Генерирует HTML для PDF."""
    
    logo_b64 = load_resource("logo_mono_trim_base64.txt")
    font_regular = load_resource("montserrat_regular_base64.txt")
    font_medium = load_resource("montserrat_medium_base64.txt")
    font_semibold = load_resource("montserrat_semibold_base64.txt")
    
    building_name = get_building_name(lot["building"])
    price_m2 = int(lot["price"] / lot["area"])
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_regular}) format('truetype'); font-weight: 400; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_medium}) format('truetype'); font-weight: 500; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_semibold}) format('truetype'); font-weight: 600; }}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Montserrat', Arial, sans-serif; background: #F6F0E3; color: #313D20; font-size: 15px; line-height: 1.4; }}

.header-table {{ width: 100%; height: 140px; background: #313D20; }}
.header-table td {{ text-align: center; vertical-align: middle; }}
.logo-header {{ height: 100px; }}

.title-bar {{ background: #DCB764; padding: 14px 40px; overflow: hidden; }}
.title-left {{ float: left; font-size: 20px; font-weight: 500; color: #313D20; }}
.title-right {{ float: right; font-size: 15px; font-weight: 500; color: #313D20; line-height: 26px; }}

.main {{ padding: 25px 40px; }}

.section {{ background: white; margin-bottom: 20px; }}
.section-header {{ background: #313D20; padding: 14px 25px; }}
.section-title {{ font-size: 18px; font-weight: 500; color: #F6F0E3; }}
.section-body {{ padding: 20px 25px; }}

.detail-table {{ width: 100%; border-collapse: collapse; }}
.detail-table td {{ padding: 10px 0; border-bottom: 1px solid rgba(49, 61, 32, 0.15); }}
.detail-table tr:last-child td {{ border-bottom: none; }}
.detail-label {{ color: #313D20; font-size: 14px; width: 60%; }}
.detail-value {{ text-align: right; font-weight: 600; font-size: 14px; }}
.detail-value-highlight {{ text-align: right; font-weight: 600; font-size: 16px; color: #DCB764; }}

.params-row {{ background: #F6F0E3; padding: 15px 25px; margin: -20px -25px 20px -25px; }}
.params-text {{ font-size: 14px; font-weight: 500; color: #313D20; text-align: center; }}
.params-badge {{ display: inline-block; background: #313D20; color: #F6F0E3; padding: 4px 12px; margin: 0 5px; font-size: 13px; }}

.payment-cards {{ overflow: hidden; }}
.payment-card {{ float: left; width: 48%; background: #F6F0E3; padding: 20px; margin-right: 4%; }}
.payment-card:last-child {{ margin-right: 0; }}
.payment-card-title {{ font-size: 12px; font-weight: 600; color: #313D20; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
.payment-card-period {{ font-size: 13px; color: #313D20; margin-bottom: 12px; }}
.payment-card-amount {{ font-size: 28px; font-weight: 600; color: #313D20; }}
.payment-card-note {{ font-size: 12px; color: #313D20; margin-top: 8px; opacity: 0.7; }}

.totals-section {{ background: #313D20; padding: 20px 25px; margin: 20px -25px -20px -25px; }}
.totals-row {{ overflow: hidden; }}
.totals-item {{ float: left; width: 33%; text-align: center; }}
.totals-label {{ font-size: 12px; color: #F6F0E3; opacity: 0.7; margin-bottom: 5px; }}
.totals-value {{ font-size: 18px; font-weight: 600; color: #DCB764; }}

.disclaimer {{ background: #F6F0E3; padding: 15px 25px; margin-top: 20px; text-align: center; }}
.disclaimer-text {{ font-size: 12px; color: #313D20; opacity: 0.7; }}

.footer {{ background: #313D20; text-align: center; padding: 20px; margin-top: 20px; }}
.footer-text {{ font-size: 12px; color: #F6F0E3; letter-spacing: 3px; }}
</style>
</head>
<body>

<table class="header-table"><tr><td>
{"<img class='logo-header' src='data:image/png;base64," + logo_b64 + "'>" if logo_b64 else ""}
</td></tr></table>

<div class="title-bar">
    <div class="title-left">🏦 Ипотека Совкомбанк</div>
    <div class="title-right">Акция «Сниженный платёж»</div>
</div>

<div class="main">
    <!-- Информация о лоте -->
    <div class="section">
        <div class="section-header">
            <div class="section-title">📍 Лот {lot['code']} • Корпус {lot['building']} «{building_name}»</div>
        </div>
        <div class="section-body">
            <table class="detail-table">
                <tr>
                    <td class="detail-label">Площадь</td>
                    <td class="detail-value">{lot['area']} м²</td>
                </tr>
                <tr>
                    <td class="detail-label">Этаж</td>
                    <td class="detail-value">{lot['floor']}</td>
                </tr>
                <tr>
                    <td class="detail-label">Цена за м²</td>
                    <td class="detail-value">{fmt(price_m2)} ₽</td>
                </tr>
                <tr>
                    <td class="detail-label">Стоимость</td>
                    <td class="detail-value-highlight">{fmt(lot['price'])} ₽</td>
                </tr>
            </table>
        </div>
    </div>

    <!-- Параметры ипотеки -->
    <div class="section">
        <div class="section-header">
            <div class="section-title">⚙️ Параметры расчёта</div>
        </div>
        <div class="section-body">
            <div class="params-row">
                <div class="params-text">
                    <span class="params-badge">ПВ {calc['down_payment_pct']}%</span>
                    <span class="params-badge">{calc['tariff_name']}</span>
                    <span class="params-badge">{calc['loan_term_years']} лет</span>
                </div>
            </div>
            <table class="detail-table">
                <tr>
                    <td class="detail-label">Стоимость для расчёта (−150 000 ₽)</td>
                    <td class="detail-value">{fmt(calc['base_price'])} ₽</td>
                </tr>
                <tr>
                    <td class="detail-label">Первоначальный взнос ({calc['down_payment_pct']}%)</td>
                    <td class="detail-value-highlight">{fmt(calc['down_payment'])} ₽</td>
                </tr>
                <tr>
                    <td class="detail-label">Удорожание за льготный период ({calc['markup_pct']}%)</td>
                    <td class="detail-value">{fmt(calc['markup'])} ₽</td>
                </tr>
                <tr>
                    <td class="detail-label">Стоимость объекта с удорожанием</td>
                    <td class="detail-value">{fmt(calc['object_price'])} ₽</td>
                </tr>
                <tr>
                    <td class="detail-label">Сумма кредита</td>
                    <td class="detail-value-highlight">{fmt(calc['loan_amount'])} ₽</td>
                </tr>
            </table>
        </div>
    </div>

    <!-- Платежи -->
    <div class="section">
        <div class="section-header">
            <div class="section-title">💳 График платежей</div>
        </div>
        <div class="section-body">
            <div class="payment-cards">
                <div class="payment-card">
                    <div class="payment-card-title">Льготный период</div>
                    <div class="payment-card-period">{calc['grace_months']} месяцев</div>
                    <div class="payment-card-amount">{fmt(calc['grace_payment'])} ₽/мес</div>
                    <div class="payment-card-note">Комиссия аккредитива {calc['accreditive_pct']}%</div>
                </div>
                <div class="payment-card">
                    <div class="payment-card-title">После льготного</div>
                    <div class="payment-card-period">{calc['remaining_months']} месяцев</div>
                    <div class="payment-card-amount">{fmt(calc['regular_payment'])} ₽/мес</div>
                    <div class="payment-card-note">Ставка {calc['rate_after_grace']}% годовых</div>
                </div>
            </div>
            
            <div class="totals-section">
                <div class="totals-row">
                    <div class="totals-item">
                        <div class="totals-label">Срок кредита</div>
                        <div class="totals-value">{calc['loan_term_years']} лет</div>
                    </div>
                    <div class="totals-item">
                        <div class="totals-label">Сумма кредита</div>
                        <div class="totals-value">{fmt(calc['loan_amount'])} ₽</div>
                    </div>
                    <div class="totals-item">
                        <div class="totals-label">Первый взнос</div>
                        <div class="totals-value">{fmt(calc['down_payment'])} ₽</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="disclaimer">
        <div class="disclaimer-text">⚠️ Расчёт является предварительным и носит информационный характер. Точные условия кредитования уточняйте в ПАО «Совкомбанк».</div>
    </div>
</div>

<div class="footer">
    <div class="footer-text">RIZALTA RESORT BELOKURIKHA</div>
</div>

</body></html>'''
    
    return html


def generate_mortgage_pdf(
    code: str,
    building: int,
    down_payment_pct: int = 30,
    tariff: str = "base",
    loan_term_months: int = 360,
    output_dir: str = None
) -> Optional[str]:
    """
    Генерирует PDF с расчётом ипотеки.
    
    Returns:
        Путь к PDF файлу или None при ошибке
    """
    # Получаем лот
    lot = get_lot_by_code(code, building)
    if not lot:
        return None
    
    # Расчёт ипотеки
    calc = calc_mortgage(
        price=lot["price"],
        down_payment_pct=down_payment_pct,
        tariff=tariff,
        loan_term_months=loan_term_months
    )
    
    # Генерируем HTML
    html = generate_html(lot, calc)
    
    # Создаём временные файлы
    if output_dir:
        html_path = os.path.join(output_dir, f"mortgage_{code}.html")
        pdf_path = os.path.join(output_dir, f"mortgage_{code}.pdf")
    else:
        tmp = tempfile.mkdtemp()
        html_path = os.path.join(tmp, f"mortgage_{code}.html")
        pdf_path = os.path.join(tmp, f"mortgage_{code}.pdf")
    
    # Сохраняем HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Конвертируем в PDF
    try:
        subprocess.run([
            "wkhtmltopdf",
            "--quiet",
            "--page-size", "A4",
            "--margin-top", "0",
            "--margin-bottom", "0",
            "--margin-left", "0",
            "--margin-right", "0",
            "--enable-local-file-access",
            html_path,
            pdf_path
        ], check=True, capture_output=True)
        
        # Удаляем HTML
        os.unlink(html_path)
        
        return pdf_path
    except subprocess.CalledProcessError as e:
        print(f"[MORTGAGE PDF] Error: {e}")
        return None
    except Exception as e:
        print(f"[MORTGAGE PDF] Error: {e}")
        return None
