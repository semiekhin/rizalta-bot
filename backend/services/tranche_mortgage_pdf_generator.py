"""Tranche mortgage PDF generator — all scenarios for a lot.

Uses wkhtmltopdf with RIZALTA dark theme (Montserrat, green/gold/cream).
Matches lot_summary_pdf_generator.py visual style.
"""

import os
import sqlite3
import subprocess
import tempfile
import logging
from datetime import date

from services.tranche_mortgage_calculator import calc_all_scenarios

logger = logging.getLogger(__name__)

RIZALTA_COLORS = {
    "bg": "#263524",
    "card_bg": "#2F4A2D",
    "card_border": "#3A5C38",
    "text": "#F2EBD9",
    "text_secondary": "#C8BBAA",
    "text_muted": "#A89880",
    "gold": "#D4A84B",
    "green_highlight": "#5B8C5A",
    "metric_bg": "#1C2A1B",
}

C = RIZALTA_COLORS


def _fmt(n) -> str:
    if n is None:
        return "—"
    try:
        return f"{int(round(n)):,}".replace(",", " ")
    except (ValueError, TypeError):
        return str(n)


def _load_fonts() -> str:
    webapp_root = os.getenv("WEBAPP_ROOT", ".")
    font_face = ""
    for weight, name in [(400, "montserrat_regular_base64.txt"),
                         (500, "montserrat_medium_base64.txt"),
                         (600, "montserrat_semibold_base64.txt")]:
        path = os.path.join(webapp_root, "backend/resources", name)
        if os.path.exists(path):
            with open(path) as f:
                b64 = f.read().strip()
            font_face += f"@font-face {{ font-family: 'Montserrat'; font-weight: {weight}; src: url(data:font/ttf;base64,{b64}) format('truetype'); }}\n"
    return font_face


def _get_lot(code: str, building: int = None) -> dict | None:
    """Get lot from properties.db."""
    db_path = os.getenv("PROPERTIES_DB", "/opt/bot/properties.db")
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if building:
        cursor.execute(
            "SELECT code, building, floor, rooms, area_m2, price_rub, status, layout_url "
            "FROM units WHERE code = ? AND building = ?", (code, building)
        )
    else:
        cursor.execute(
            "SELECT code, building, floor, rooms, area_m2, price_rub, status, layout_url "
            "FROM units WHERE code = ?", (code,)
        )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "code": row[0],
        "building": row[1],
        "floor": row[2],
        "rooms": row[3],
        "area": row[4],
        "price": row[5],
        "status": row[6],
        "layout_url": row[7],
    }


def _build_scenario_card(sc: dict) -> str:
    """Build HTML card for one tranche scenario."""
    tp = sc["tranche_period"]
    tp3 = sc["term_months"] - 2 * tp
    return f'''
    <div style="background:{C["card_bg"]}; border:1px solid {C["card_border"]}; border-radius:12px; padding:16px; margin-bottom:12px;">
        <table style="width:100%;"><tr>
            <td><span style="font-size:16px; font-weight:600; color:{C["gold"]};">ПВ {sc["down_payment_pct"]}%</span></td>
            <td style="text-align:right;"><span style="font-size:13px; color:{C["text_secondary"]};">Ставка {sc["rate"]}%</span></td>
        </tr></table>
        <table style="width:100%; border-collapse:collapse; margin-top:10px;">
            <tr>
                <td style="padding:5px 0; font-size:12px; color:{C["text_secondary"]};">Первоначальный взнос</td>
                <td style="padding:5px 0; font-size:12px; font-weight:600; text-align:right; color:{C["text"]};">{_fmt(sc["down_payment"])} ₽</td>
            </tr>
            <tr>
                <td style="padding:5px 0; font-size:12px; color:{C["text_secondary"]};">Сумма ипотеки</td>
                <td style="padding:5px 0; font-size:12px; font-weight:600; text-align:right; color:{C["text"]};">{_fmt(sc["mortgage_total"])} ₽</td>
            </tr>
        </table>
        <div style="border-top:1px solid {C["card_border"]}; margin:10px 0; padding-top:10px;">
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="width:33%; text-align:center; vertical-align:top;">
                        <div style="background:{C["metric_bg"]}; border-radius:8px; padding:10px; margin:0 3px;">
                            <div style="font-size:9px; text-transform:uppercase; letter-spacing:0.5px; color:{C["text_muted"]};">1 транш</div>
                            <div style="font-size:10px; color:{C["text_secondary"]};">({tp} мес.)</div>
                            <div style="font-size:14px; font-weight:600; color:{C["gold"]}; margin-top:4px;">{_fmt(sc["ep_1"])} ₽</div>
                        </div>
                    </td>
                    <td style="width:33%; text-align:center; vertical-align:top;">
                        <div style="background:{C["metric_bg"]}; border-radius:8px; padding:10px; margin:0 3px;">
                            <div style="font-size:9px; text-transform:uppercase; letter-spacing:0.5px; color:{C["text_muted"]};">2 транш</div>
                            <div style="font-size:10px; color:{C["text_secondary"]};">({tp} мес.)</div>
                            <div style="font-size:14px; font-weight:600; color:{C["gold"]}; margin-top:4px;">{_fmt(sc["ep_2"])} ₽</div>
                        </div>
                    </td>
                    <td style="width:33%; text-align:center; vertical-align:top;">
                        <div style="background:{C["metric_bg"]}; border-radius:8px; padding:10px; margin:0 3px;">
                            <div style="font-size:9px; text-transform:uppercase; letter-spacing:0.5px; color:{C["text_muted"]};">3 транш</div>
                            <div style="font-size:10px; color:{C["text_secondary"]};">({tp3} мес.)</div>
                            <div style="font-size:14px; font-weight:600; color:{C["gold"]}; margin-top:4px;">{_fmt(sc["ep_3"])} ₽</div>
                        </div>
                    </td>
                </tr>
            </table>
        </div>
    </div>'''


def generate_tranche_mortgage_pdf(code: str, building: int = None) -> bytes | None:
    """Generate tranche mortgage PDF for a lot.

    Looks up lot in properties.db, calculates all scenarios, generates PDF.
    Returns PDF bytes or None.
    """
    lot = _get_lot(code, building)
    if not lot:
        return None

    scenarios = calc_all_scenarios(lot["price"])
    valid = [s for s in scenarios if s is not None]
    if not valid:
        return None

    font_face = _load_fonts()
    today = date.today().strftime('%d.%m.%Y')

    building_names = {1: "Family", 2: "Business", 3: "Digital"}
    bname = building_names.get(lot["building"], "")
    price_m2 = round(lot["price"] / lot["area"]) if lot["area"] else 0

    cards = "".join(_build_scenario_card(sc) for sc in valid)

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    {font_face}
    @page {{ size: A4; margin: 20mm 15mm; }}
    body {{
        font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif;
        background: {C["bg"]};
        color: {C["text"]};
        font-size: 14px;
        line-height: 1.5;
        margin: 0;
        padding: 20px;
    }}
</style>
</head>
<body>

<div style="text-align:center; margin-bottom:20px; padding-bottom:14px; border-bottom:2px solid {C["gold"]};">
    <div style="font-size:24px; font-weight:700; color:{C["gold"]};">RIZALTA Resort Belokurikha</div>
    <div style="font-size:14px; color:{C["text_secondary"]}; margin-top:4px;">Траншевая ипотека · {code}</div>
</div>

<div style="background:{C["card_bg"]}; border:1px solid {C["card_border"]}; border-radius:12px; padding:20px; margin-bottom:16px;">
    <table style="width:100%;"><tr>
        <td style="vertical-align:top;">
            <div style="font-size:22px; font-weight:600; color:{C["gold"]};">{code}</div>
            <div style="font-size:13px; color:{C["text_secondary"]}; margin-top:4px;">
                Корпус {lot["building"]} «{bname}» · {lot["area"]} м² · этаж {lot["floor"]}
            </div>
        </td>
        <td style="vertical-align:top; text-align:right;">
            <div style="font-size:20px; font-weight:600; color:{C["text"]};">{_fmt(lot["price"])} ₽</div>
            <div style="font-size:11px; color:{C["text_muted"]};">{_fmt(price_m2)} ₽/м²</div>
        </td>
    </tr></table>
</div>

<div style="font-size:12px; color:{C["text_muted"]}; margin-bottom:16px; text-align:center;">
    3 транша · 20 лет · Сервисный сбор 150 000 ₽
</div>

{cards}

<div style="text-align:center; color:{C["text_muted"]}; font-size:11px; margin-top:24px; padding-top:12px; border-top:1px solid {C["card_border"]};">
    Расчёт предварительный. Точные условия уточняйте в банке.<br>
    RIZALTA Resort Belokurikha · {today}
</div>

</body>
</html>'''

    try:
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
            f.write(html)
            html_path = f.name

        pdf_path = html_path.replace('.html', '.pdf')

        result = subprocess.run(
            [
                'wkhtmltopdf',
                '--enable-local-file-access',
                '--encoding', 'utf-8',
                '--page-size', 'A4',
                '--margin-top', '10mm',
                '--margin-bottom', '10mm',
                '--margin-left', '10mm',
                '--margin-right', '10mm',
                '--no-stop-slow-scripts',
                html_path, pdf_path,
            ],
            capture_output=True,
            timeout=30,
        )

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            os.unlink(html_path)
            os.unlink(pdf_path)
            return pdf_bytes

        logger.error(f"[TRANCHE PDF] wkhtmltopdf failed: {result.stderr.decode()}")
        os.unlink(html_path)
        return None

    except Exception as e:
        logger.error(f"[TRANCHE PDF] Error: {e}")
        return None
