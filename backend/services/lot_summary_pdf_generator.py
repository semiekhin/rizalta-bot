"""Lot summary PDF generator — all 7 sections from investment summary modal.

Uses wkhtmltopdf with RIZALTA branding (Montserrat, green/gold/cream).
"""

import os
import subprocess
import tempfile
import logging
from datetime import date

logger = logging.getLogger(__name__)

COLORS = {
    "bg": "#F6F0E3",
    "header_bg": "#313D20",
    "gold": "#DCB764",
    "text": "#313D20",
    "text_light": "#F6F0E3",
    "text_muted": "#6B7A5E",
    "success": "#4a7c23",
    "card_bg": "#FFFFFF",
    "border": "rgba(49,61,32,0.15)",
    "stripe": "rgba(49,61,32,0.04)",
}


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


def _section_title(text: str) -> str:
    return f'<div style="font-size:15px; font-weight:600; color:{COLORS["text"]}; margin:24px 0 10px; padding-bottom:5px; border-bottom:2px solid {COLORS["gold"]};">{text}</div>'


def _build_header(lot: dict) -> str:
    building_names = {1: "Family", 2: "Business", 3: "Digital"}
    b = lot.get("building", "")
    name = building_names.get(b, "")
    area = lot.get("area", 0)
    price = lot.get("price", 0)
    price_m2 = round(price / area) if area else 0
    return f'''
    <div style="background:{COLORS["header_bg"]}; color:{COLORS["text_light"]}; padding:20px 30px; border-radius:8px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <div style="font-size:22px; font-weight:600; color:{COLORS["gold"]};">{lot.get("code", "")}</div>
                <div style="font-size:13px; color:{COLORS["text_light"]}; opacity:0.8; margin-top:4px;">
                    Корпус {b} «{name}» · {area} м² · этаж {lot.get("floor", "")}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:20px; font-weight:600;">{_fmt(price)} ₽</div>
                <div style="font-size:11px; opacity:0.7;">{_fmt(price_m2)} ₽/м²</div>
            </div>
        </div>
    </div>'''


def _build_metrics(roi: dict, lot: dict) -> str:
    price = lot.get("price", 0)
    area = lot.get("area", 0)
    daily_rate = 15000
    occupancy = 0.60
    expense_ratio = 0.50
    gross = daily_rate * (area / 26.8) * 365 * occupancy
    noi = round(gross * (1 - expense_ratio))
    cap_rate = round(noi / price * 100, 1) if price else 0
    coc_full = round(noi / (price * 0.95) * 100, 1) if price else 0
    coc_inst = round(noi / (price * 0.3) * 100, 1) if price else 0
    total_profit = roi.get("total_profit", 0)
    eq_full = round((total_profit + price) / (price * 0.95), 2) if price else 0
    eq_inst = round((total_profit + price) / (price * 0.3), 2) if price else 0

    def cell(label, value, sub="", highlight=False):
        bg = COLORS["gold"] if highlight else COLORS["card_bg"]
        color = COLORS["text"] if highlight else COLORS["text"]
        return f'''
        <td style="background:{bg}; padding:10px; border:1px solid {COLORS["border"]}; text-align:center; width:33%;">
            <div style="font-size:9px; text-transform:uppercase; color:{COLORS["text_muted"]}; letter-spacing:0.5px;">{label}</div>
            <div style="font-size:16px; font-weight:600; color:{color}; margin:4px 0;">{value}</div>
            <div style="font-size:9px; color:{COLORS["text_muted"]};">{sub}</div>
        </td>'''

    return f'''
    {_section_title("Инвестиционные метрики")}
    <table style="width:100%; border-collapse:collapse;">
        <tr>
            {cell("Чистый доход / год", f"{_fmt(noi)} ₽", "стабилиз. 2030", True)}
            {cell("Доходность (Cap Rate)", f"{cap_rate}%", "NOI / цена", True)}
            {cell("ROI 11 лет", f"{roi.get('roi_pct', 0)}%", f"~{roi.get('avg_annual_pct', 0)}% / год")}
        </tr>
        <tr>
            {cell("Доход на вложенное (100%)", f"{coc_full}%", "скидка 5%")}
            {cell("Доход на вложенное (30%)", f"{coc_inst}%", "рассрочка")}
            {cell("Мультипликатор", f"{eq_full}x", f"рассрочка {eq_inst}x")}
        </tr>
    </table>'''


def _build_profitability(roi: dict) -> str:
    return f'''
    {_section_title("Доходность за 11 лет")}
    <div style="background:{COLORS["success"]}; color:white; padding:14px 20px; border-radius:8px; margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:14px; font-weight:500;">Доходность за 11 лет</span>
            <span style="font-size:24px; font-weight:600;">{roi.get("roi_pct", 0)}%</span>
        </div>
        <div style="font-size:12px; opacity:0.85;">~{roi.get("avg_annual_pct", 0)}% годовых</div>
    </div>
    <table style="width:100%; border-collapse:collapse; margin-bottom:8px;">
        <tr>
            <td style="background:{COLORS["card_bg"]}; padding:10px 14px; border:1px solid {COLORS["border"]}; width:50%;">
                <div style="font-size:10px; color:{COLORS["text_muted"]};">Аренда</div>
                <div style="font-size:15px; font-weight:600; color:{COLORS["text"]};">{_fmt(roi.get("total_rental", 0))} ₽</div>
            </td>
            <td style="background:{COLORS["card_bg"]}; padding:10px 14px; border:1px solid {COLORS["border"]}; width:50%;">
                <div style="font-size:10px; color:{COLORS["text_muted"]};">Рост стоимости</div>
                <div style="font-size:15px; font-weight:600; color:{COLORS["text"]};">{_fmt(roi.get("total_growth", 0))} ₽</div>
            </td>
        </tr>
    </table>
    <table style="width:100%; border-collapse:collapse;">
        <tr>
            <td style="background:{COLORS["card_bg"]}; padding:10px 14px; border:1px solid {COLORS["border"]}; width:50%;">
                <div style="font-size:10px; color:{COLORS["text_muted"]};">Общая прибыль</div>
                <div style="font-size:15px; font-weight:600; color:{COLORS["gold"]};">{_fmt(roi.get("total_profit", 0))} ₽</div>
            </td>
            <td style="background:{COLORS["card_bg"]}; padding:10px 14px; border:1px solid {COLORS["border"]}; width:50%;">
                <div style="font-size:10px; color:{COLORS["text_muted"]};">Стоимость в 2035</div>
                <div style="font-size:15px; font-weight:600; color:{COLORS["text"]};">{_fmt(roi.get("final_value", 0))} ₽</div>
            </td>
        </tr>
    </table>'''


def _build_payments(inst: dict, price: int) -> str:
    price_100 = round(price * 0.95)
    saving = round(price * 0.05)
    i12 = inst.get("i12", {})
    i18 = inst.get("i18", {})

    def row(label, value):
        return f'<tr><td style="padding:5px 10px; font-size:11px; color:{COLORS["text_muted"]};">{label}</td><td style="padding:5px 10px; font-size:11px; font-weight:500; text-align:right;">{value}</td></tr>'

    return f'''
    {_section_title("Варианты оплаты")}
    <div style="background:{COLORS["success"]}; color:white; padding:12px 16px; border-radius:8px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:600;">💰 100% оплата (скидка 5%)</div>
        <div style="font-size:18px; font-weight:600; margin-top:4px;">{_fmt(price_100)} ₽</div>
        <div style="font-size:11px; opacity:0.85;">Экономия: {_fmt(saving)} ₽</div>
    </div>
    <div style="background:{COLORS["card_bg"]}; border:2px solid {COLORS["success"]}; border-radius:8px; padding:12px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:600; color:{COLORS["success"]}; margin-bottom:8px;">12 месяцев (0%)</div>
        <table style="width:100%; border-collapse:collapse;">
            {row("ПВ 30%", f"{_fmt(i12.get('pv_30', 0))} ₽ → {_fmt(i12.get('monthly_30', 0))} ₽/мес")}
            {row("ПВ 40%", f"{_fmt(i12.get('pv_40', 0))} ₽ → 11×200К + {_fmt(i12.get('last_40', 0))} ₽")}
            {row("ПВ 50%", f"{_fmt(i12.get('pv_50', 0))} ₽ → 11×100К + {_fmt(i12.get('last_50', 0))} ₽")}
        </table>
    </div>
    <div style="background:{COLORS["card_bg"]}; border:2px solid {COLORS["gold"]}; border-radius:8px; padding:12px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:600; color:{COLORS["gold"]}; margin-bottom:8px;">18 месяцев</div>
        <table style="width:100%; border-collapse:collapse;">
            {row("ПВ 30% (+9%)", f"{_fmt(i18.get('pv_30', 0))} ₽ · 18 × {_fmt(i18.get('monthly_30', 0))} ₽ → {_fmt(i18.get('final_price_30', 0))} ₽")}
            {row("ПВ 40% (+7%)", f"{_fmt(i18.get('pv_40', 0))} ₽ · 8×250К + {_fmt(i18.get('last_40', 0))} ₽")}
            {row("ПВ 50% (+4%)", f"{_fmt(i18.get('pv_50', 0))} ₽ · 8×150К + {_fmt(i18.get('last_50', 0))} ₽")}
        </table>
    </div>'''


def _build_deposit(deposit: dict, roi: dict) -> str:
    total_profit = roi.get("total_profit", 0)
    base = deposit.get("base", {})
    base_interest = base.get("total_net_interest", 0)
    advantage = total_profit - base_interest

    rows = ""
    for key, d in deposit.items():
        rows += f'''
        <tr>
            <td style="padding:7px 10px; font-size:11px; border-bottom:1px solid {COLORS["border"]};">{d.get("scenario_name", key)}</td>
            <td style="padding:7px 10px; font-size:11px; font-weight:500; text-align:right; border-bottom:1px solid {COLORS["border"]};">{_fmt(d.get("total_net_interest", 0))} ₽</td>
            <td style="padding:7px 10px; font-size:11px; text-align:right; border-bottom:1px solid {COLORS["border"]};">{d.get("total_roi_pct", 0)}%</td>
        </tr>'''

    advantage_html = ""
    if advantage > 0:
        advantage_html = f'''
        <div style="background:{COLORS["gold"]}; color:{COLORS["text"]}; padding:10px 16px; border-radius:8px; margin-bottom:10px; font-weight:600;">
            ✅ RIZALTA выгоднее на {_fmt(advantage)} ₽
        </div>'''

    return f'''
    {_section_title("RIZALTA vs Депозит (11 лет)")}
    {advantage_html}
    <div style="background:{COLORS["success"]}; color:white; padding:10px 16px; border-radius:8px; margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:500;">🏠 RIZALTA</span>
            <span style="font-size:18px; font-weight:600;">{_fmt(total_profit)} ₽</span>
        </div>
        <div style="font-size:11px; opacity:0.85;">ROI: {roi.get("roi_pct", 0)}% за 11 лет</div>
    </div>
    <table style="width:100%; border-collapse:collapse; background:{COLORS["card_bg"]}; border-radius:8px;">
        <thead>
            <tr style="background:{COLORS["header_bg"]}; color:{COLORS["text_light"]};">
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:left;">Сценарий</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right;">Доход</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right;">ROI</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>'''


def _build_mgp(mgp: dict) -> str:
    years = mgp.get("years", [])
    if not years:
        return ""
    rows = ""
    for i, yr in enumerate(years):
        bg = COLORS["stripe"] if i % 2 == 1 else COLORS["card_bg"]
        rows += f'''
        <tr style="background:{bg};">
            <td style="padding:5px 10px; font-size:11px; font-weight:500;">{yr.get("year", "")}</td>
            <td style="padding:5px 10px; font-size:11px; font-weight:500; text-align:right; color:{COLORS["gold"]};">{_fmt(yr.get("nominal", 0))} ₽</td>
            <td style="padding:5px 10px; font-size:11px; text-align:right;">{_fmt(yr.get("commercial", 0))} ₽</td>
        </tr>'''

    return f'''
    {_section_title("Минимальный гарантированный платёж")}
    <table style="width:100%; border-collapse:collapse; background:{COLORS["card_bg"]}; border-radius:8px;">
        <thead>
            <tr style="background:{COLORS["header_bg"]}; color:{COLORS["text_light"]};">
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:left;">Год</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right;">Номерной, ₽</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right;">Коммерч., ₽</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
        <tfoot>
            <tr style="background:{COLORS["gold"]};">
                <td style="padding:7px 10px; font-size:11px; font-weight:600;">Итого</td>
                <td style="padding:7px 10px; font-size:11px; font-weight:600; text-align:right;">{_fmt(mgp.get("total_nominal", 0))} ₽</td>
                <td style="padding:7px 10px; font-size:11px; font-weight:600; text-align:right;">{_fmt(mgp.get("total_commercial", 0))} ₽</td>
            </tr>
        </tfoot>
    </table>'''


def _build_mortgage(mort: dict) -> str:
    return f'''
    {_section_title("Ипотека (Совкомбанк)")}
    <div style="background:{COLORS["card_bg"]}; border:1px solid {COLORS["border"]}; border-radius:8px; padding:14px;">
        <div style="font-size:11px; color:{COLORS["text_muted"]}; margin-bottom:8px;">Базовый тариф · ПВ 30% · 30 лет</div>
        <table style="width:100%; border-collapse:collapse;">
            <tr><td style="padding:5px 0; font-size:12px; color:{COLORS["text_muted"]};">Первонач. взнос</td><td style="padding:5px 0; font-size:12px; font-weight:600; text-align:right;">{_fmt(mort.get("down_payment", 0))} ₽</td></tr>
            <tr><td style="padding:5px 0; font-size:12px; color:{COLORS["text_muted"]};">Сумма кредита</td><td style="padding:5px 0; font-size:12px; font-weight:600; text-align:right;">{_fmt(mort.get("loan_amount", 0))} ₽</td></tr>
            <tr style="border-top:1px solid {COLORS["border"]};">
                <td style="padding:8px 0 5px; font-size:12px; color:{COLORS["text_muted"]};">Платёж (льготный)</td>
                <td style="padding:8px 0 5px; font-size:14px; font-weight:600; text-align:right; color:{COLORS["gold"]};">{_fmt(mort.get("grace_payment", 0))} ₽/мес</td>
            </tr>
            <tr><td style="padding:5px 0; font-size:12px; color:{COLORS["text_muted"]};">Платёж (после)</td><td style="padding:5px 0; font-size:12px; font-weight:600; text-align:right;">{_fmt(mort.get("regular_payment", 0))} ₽/мес</td></tr>
            <tr><td style="padding:5px 0; font-size:12px; color:{COLORS["text_muted"]};">Ставка</td><td style="padding:5px 0; font-size:12px; text-align:right;">{mort.get("rate_after_grace", "")}% годовых</td></tr>
        </table>
    </div>'''


def generate_lot_summary_pdf(data: dict) -> bytes | None:
    """Generate comprehensive lot summary PDF.

    Expects: { lot, roi, installment, deposit, mgp, mortgage }
    Returns PDF bytes or None.
    """
    lot = data.get("lot", {})
    roi = data.get("roi")
    installment = data.get("installment")
    deposit = data.get("deposit")
    mgp = data.get("mgp")
    mortgage = data.get("mortgage")

    font_face = _load_fonts()
    today = date.today().strftime('%d.%m.%Y')
    code = lot.get("code", "")

    sections = _build_header(lot)
    if roi:
        sections += _build_metrics(roi, lot)
        sections += _build_profitability(roi)
    if installment:
        sections += _build_payments(installment, lot.get("price", 0))
    if deposit and roi:
        sections += _build_deposit(deposit, roi)
    if mgp:
        sections += _build_mgp(mgp)
    if mortgage:
        sections += _build_mortgage(mortgage)

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    {font_face}
    @page {{ size: A4; margin: 0; }}
    body {{
        font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif;
        background: {COLORS["bg"]};
        color: {COLORS["text"]};
        font-size: 12px;
        line-height: 1.4;
        margin: 0;
        padding: 0;
    }}
    .page {{
        width: 210mm;
        min-height: 297mm;
        background: {COLORS["bg"]};
        position: relative;
    }}
    .header-bar {{
        background: {COLORS["header_bg"]};
        padding: 30px 40px 20px;
    }}
    .title-bar {{
        background: {COLORS["gold"]};
        padding: 12px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .content {{
        padding: 10px 40px 30px;
    }}
    .footer {{
        background: {COLORS["header_bg"]};
        text-align: center;
        padding: 14px;
        position: fixed;
        bottom: 0;
        width: 100%;
    }}
    .footer-text {{
        font-size: 10px;
        color: {COLORS["text_light"]};
        letter-spacing: 4px;
    }}
</style>
</head>
<body>
<div class="page">
    <div class="header-bar">
        <div style="font-size:22px; font-weight:600; color:{COLORS["gold"]};">RIZALTA Resort Belokurikha</div>
        <div style="font-size:12px; color:{COLORS["text_light"]}; opacity:0.7; margin-top:4px;">Инвестиционный анализ</div>
    </div>
    <div class="title-bar">
        <div style="font-size:16px; font-weight:500; color:{COLORS["text"]};">Инвестиционная сводка · {code}</div>
        <div style="font-size:11px; color:{COLORS["text"]};">{today}</div>
    </div>
    <div class="content">
        {sections}
    </div>
    <div class="footer">
        <div class="footer-text">R I Z A L T A &nbsp; R E S O R T &nbsp; B E L O K U R I K H A</div>
    </div>
</div>
</body>
</html>'''

    try:
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
            f.write(html)
            html_path = f.name

        pdf_path = html_path.replace('.html', '.pdf')

        subprocess.run(
            [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--orientation', 'Portrait',
                '--margin-top', '0',
                '--margin-bottom', '0',
                '--margin-left', '0',
                '--margin-right', '0',
                '--enable-local-file-access',
                '--disable-smart-shrinking',
                '--quiet',
                html_path, pdf_path,
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            os.unlink(html_path)
            os.unlink(pdf_path)
            return pdf_bytes

        logger.error("[LOT SUMMARY PDF] wkhtmltopdf failed")
        os.unlink(html_path)
        return None

    except Exception as e:
        logger.error(f"[LOT SUMMARY PDF] Error: {e}")
        return None
