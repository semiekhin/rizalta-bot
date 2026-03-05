"""
Генератор PDF для траншевой ипотеки RIZALTA.
Все 4 сценария ПВ в одном файле + планировка лота.

v1.1 (03.03.2026)
"""

import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64

from services.tranche_mortgage_calculator import calc_all_scenarios
from services.units_db import get_lot_by_code

BASE_DIR = Path(__file__).parent.parent
RESOURCES_DIR = BASE_DIR / "services" / "kp_resources"


def load_resource(filename: str) -> str:
    path = RESOURCES_DIR / filename
    return path.read_text().strip() if path.exists() else ""


def fmt(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def get_building_name(building: int) -> str:
    names = {1: "Family", 2: "Business", 3: "Digital"}
    return names.get(building, "Family")


def download_image_b64(url: str) -> str:
    """Скачивает изображение и возвращает base64-строку."""
    if not url:
        return ""
    try:
        import requests, base64
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    except Exception as e:
        print(f"[TRANCHE PDF] Image download error: {e}")
        return ""


def _scenario_html(calc: Dict[str, Any]) -> str:
    """HTML блок одного сценария ПВ."""
    tp = calc["tranche_period"]
    remaining_months = calc["term_months"] - 2 * tp

    return f'''
    <div class="scenario">
        <div class="scenario-header">
            <span class="scenario-badge">ПВ {calc['down_payment_pct']}%</span>
            <span class="scenario-badge">Ставка {calc['rate']}%</span>
        </div>
        <div class="scenario-body">
            <div class="scenario-row">
                <span class="scenario-label">Первоначальный взнос</span>
                <span class="scenario-value">{fmt(calc['down_payment'])} ₽</span>
            </div>
            <div class="scenario-row">
                <span class="scenario-label">Сумма ипотеки</span>
                <span class="scenario-value-highlight">{fmt(calc['mortgage_total'])} ₽</span>
            </div>
            <div class="scenario-tranches">
                <div class="tranche-item">
                    <div class="tranche-label">1 транш ({tp} мес.)</div>
                    <div class="tranche-ep">{fmt(calc['ep_1'])} ₽/мес.</div>
                </div>
                <div class="tranche-item">
                    <div class="tranche-label">2 транш ({tp} мес.)</div>
                    <div class="tranche-ep">{fmt(calc['ep_2'])} ₽/мес.</div>
                </div>
                <div class="tranche-item">
                    <div class="tranche-label">3 транш ({remaining_months} мес.)</div>
                    <div class="tranche-ep">{fmt(calc['ep_3'])} ₽/мес.</div>
                </div>
            </div>
        </div>
    </div>'''


def generate_html(lot: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> str:
    logo_b64 = load_resource("logo_mono_trim_base64.txt")
    font_regular = load_resource("montserrat_regular_base64.txt")
    font_medium = load_resource("montserrat_medium_base64.txt")
    font_semibold = load_resource("montserrat_semibold_base64.txt")

    building_name = get_building_name(lot["building"])
    price_m2 = int(lot["price"] / lot["area"])

    # Планировка
    layout_b64 = ""
    if lot.get("layout_url"):
        layout_b64 = download_image_b64(lot["layout_url"])

    layout_img = ""
    if layout_b64:
        layout_img = f'<img class="layout-img" src="data:image/jpeg;base64,{layout_b64}">'

    # Блоки сценариев
    scenarios_html = ""
    for sc in scenarios:
        if sc:
            scenarios_html += _scenario_html(sc)

    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_regular}) format('truetype'); font-weight: 400; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_medium}) format('truetype'); font-weight: 500; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_semibold}) format('truetype'); font-weight: 600; }}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Montserrat', Arial, sans-serif; background: #F6F0E3; color: #313D20; font-size: 14px; line-height: 1.4; }}

.header-table {{ width: 100%; height: 120px; background: #313D20; }}
.header-table td {{ text-align: center; vertical-align: middle; }}
.logo-header {{ height: 80px; }}

.title-bar {{ background: #DCB764; padding: 12px 40px; overflow: hidden; }}
.title-left {{ float: left; font-size: 20px; font-weight: 600; color: #313D20; }}
.title-right {{ float: right; font-size: 14px; font-weight: 500; color: #313D20; line-height: 26px; }}

.main {{ padding: 20px 40px; }}

/* Лот + планировка */
.lot-section {{ background: white; margin-bottom: 18px; overflow: hidden; }}
.lot-header {{ background: #313D20; padding: 12px 20px; }}
.lot-title {{ font-size: 16px; font-weight: 500; color: #F6F0E3; }}
.lot-body {{ padding: 15px 20px; }}
.lot-body-table {{ width: 100%; border-collapse: collapse; }}
.lot-info {{ width: 58%; vertical-align: top; padding-right: 15px; }}
.lot-layout {{ width: 42%; vertical-align: middle; text-align: center; }}
.layout-img {{ width: 100%; display: block; max-height: 230px; object-fit: contain; }}
.lot-row {{ padding: 14px 0; border-bottom: 1px solid rgba(49,61,32,0.12); overflow: hidden; }}
.lot-row:last-child {{ border-bottom: none; }}
.lot-label {{ float: left; font-size: 16px; font-weight: 600; }}
.lot-value {{ float: right; font-weight: 700; font-size: 17px; }}
.lot-value-big {{ float: right; font-weight: 700; font-size: 19px; color: #DCB764; }}

/* Сценарии */
.scenarios-header {{ background: #313D20; padding: 12px 20px; margin-bottom: 0; }}
.scenarios-title {{ font-size: 16px; font-weight: 500; color: #F6F0E3; }}

.scenario {{ background: white; margin-bottom: 2px; padding: 0; }}
.scenario-header {{ background: #F6F0E3; padding: 10px 20px; }}
.scenario-badge {{ display: inline-block; background: #313D20; color: #F6F0E3; padding: 3px 10px; margin-right: 8px; font-size: 12px; font-weight: 500; }}
.scenario-body {{ padding: 10px 20px 14px 20px; }}
.scenario-row {{ overflow: hidden; padding: 4px 0; }}
.scenario-label {{ float: left; font-size: 13px; }}
.scenario-value {{ float: right; font-weight: 600; font-size: 13px; }}
.scenario-value-highlight {{ float: right; font-weight: 600; font-size: 14px; color: #DCB764; }}

.scenario-tranches {{ margin-top: 8px; overflow: hidden; }}
.tranche-item {{ float: left; width: 33.33%; text-align: center; background: #F6F0E3; padding: 8px 5px; }}
.tranche-label {{ font-size: 11px; color: #313D20; margin-bottom: 4px; }}
.tranche-ep {{ font-size: 15px; font-weight: 600; color: #313D20; }}

.disclaimer {{ padding: 12px 20px; text-align: center; margin-top: 15px; }}
.disclaimer-text {{ font-size: 11px; color: #313D20; opacity: 0.6; }}

.footer {{ background: #313D20; text-align: center; padding: 15px; margin-top: 15px; }}
.footer-text {{ font-size: 11px; color: #F6F0E3; letter-spacing: 3px; }}
</style>
</head>
<body>

<table class="header-table"><tr><td>
{"<img class='logo-header' src='data:image/png;base64," + logo_b64 + "'>" if logo_b64 else ""}
</td></tr></table>

<div class="title-bar">
    <div class="title-left">Траншевая ипотека</div>
    <div class="title-right">3 транша &bull; 20 лет</div>
</div>

<div class="main">
    <div class="lot-section">
        <div class="lot-header">
            <div class="lot-title">Лот {lot['code']} &bull; Корпус {lot['building']} &laquo;{building_name}&raquo;</div>
        </div>
        <div class="lot-body">
            <table class="lot-body-table"><tr>
            <td class="lot-info">
                <div class="lot-row">
                    <span class="lot-label">Площадь</span>
                    <span class="lot-value">{lot['area']} м&sup2;</span>
                </div>
                <div class="lot-row">
                    <span class="lot-label">Этаж</span>
                    <span class="lot-value">{lot['floor']}</span>
                </div>
                <div class="lot-row">
                    <span class="lot-label">Цена за м&sup2;</span>
                    <span class="lot-value">{fmt(price_m2)} &#8381;</span>
                </div>
                <div class="lot-row">
                    <span class="lot-label">Стоимость</span>
                    <span class="lot-value-big">{fmt(lot['price'])} &#8381;</span>
                </div>
            </td>
            <td class="lot-layout">
                {layout_img}
            </td></tr></table>
        </div>
    </div>

    <div class="scenarios-header">
        <div class="scenarios-title">Варианты расчёта</div>
    </div>

    {scenarios_html}

    <div class="disclaimer">
        <div class="disclaimer-text">⚠ Расчёт является предварительным и носит информационный характер. Точные условия кредитования уточняйте в банке.</div>
    </div>
</div>

<div class="footer">
    <div class="footer-text">RIZALTA RESORT BELOKURIKHA</div>
</div>

</body></html>'''

    return html


def generate_tranche_mortgage_pdf(
    code: str,
    building: int,
    output_dir: str = None
) -> Optional[str]:
    lot = get_lot_by_code(code, building)
    if not lot:
        return None

    scenarios = calc_all_scenarios(lot["price"])
    valid = [s for s in scenarios if s is not None]
    if not valid:
        return None

    html = generate_html(lot, valid)

    if output_dir:
        html_path = os.path.join(output_dir, f"tranche_{code}.html")
        pdf_path = os.path.join(output_dir, f"tranche_{code}.pdf")
    else:
        tmp = tempfile.mkdtemp()
        html_path = os.path.join(tmp, f"tranche_{code}.html")
        pdf_path = os.path.join(tmp, f"tranche_{code}.pdf")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

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
            "--disable-smart-shrinking",
            html_path,
            pdf_path
        ], check=True, capture_output=True)

        os.unlink(html_path)
        return pdf_path
    except Exception as e:
        print(f"[TRANCHE PDF] Error: {e}")
        return None
