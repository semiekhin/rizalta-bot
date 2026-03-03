"""Lot summary PDF generator — all 7 sections from investment summary modal.

Uses wkhtmltopdf with RIZALTA dark theme (Montserrat, green/gold/cream).
Matches portfolio_pdf_generator.py visual style.
"""

import os
import subprocess
import tempfile
import logging
from datetime import date

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
    """Format number with space thousands separator."""
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


def _metric_cell(label: str, value: str, sub: str = "", highlight: bool = False) -> str:
    bg = C["metric_bg"] if highlight else C["card_bg"]
    color = C["gold"] if highlight else C["text"]
    sub_html = f'<div style="font-size:9px; color:{C["text_muted"]}; margin-top:2px;">{sub}</div>' if sub else ""
    return f'''<div style="background:{bg}; padding:10px; border-radius:8px; text-align:center;">
        <div style="font-size:9px; text-transform:uppercase; letter-spacing:0.5px; color:{C["text_muted"]};">{label}</div>
        <div style="font-size:15px; font-weight:600; color:{color}; margin:3px 0;">{value}</div>
        {sub_html}
    </div>'''


def _section_title(text: str) -> str:
    return f'<div style="font-size:14px; font-weight:600; color:{C["gold"]}; margin:20px 0 10px; padding-bottom:5px; border-bottom:2px solid {C["gold"]};">{text}</div>'


def _build_header(lot: dict) -> str:
    building_names = {1: "Family", 2: "Business", 3: "Digital"}
    b = lot.get("building", "")
    name = building_names.get(b, "")
    area = lot.get("area", 0)
    price = lot.get("price", 0)
    price_m2 = round(price / area) if area else 0
    return f'''
    <div style="background:{C["card_bg"]}; border:1px solid {C["card_border"]}; border-radius:12px; padding:20px; margin-bottom:16px;">
        <table style="width:100%;"><tr>
            <td style="vertical-align:top;">
                <div style="font-size:22px; font-weight:600; color:{C["gold"]};">{lot.get("code", "")}</div>
                <div style="font-size:13px; color:{C["text_secondary"]}; margin-top:4px;">
                    Корпус {b} «{name}» · {area} м² · этаж {lot.get("floor", "")}
                </div>
            </td>
            <td style="vertical-align:top; text-align:right;">
                <div style="font-size:20px; font-weight:600; color:{C["text"]};">{_fmt(price)} ₽</div>
                <div style="font-size:11px; color:{C["text_muted"]};">{_fmt(price_m2)} ₽/м²</div>
            </td>
        </tr></table>
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

    return f'''
    {_section_title("Инвестиционные метрики")}
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:8px;">
        {_metric_cell("Чистый доход / год", f"{_fmt(noi)} ₽", "стабилиз. 2030", True)}
        {_metric_cell("Доходность (Cap Rate)", f"{cap_rate}%", "NOI / цена", True)}
        {_metric_cell("ROI 11 лет", f"{roi.get('roi_pct', 0)}%", f"~{roi.get('avg_annual_pct', 0)}% / год")}
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px;">
        {_metric_cell("Доход на вложенное (100%)", f"{coc_full}%", "скидка 5%")}
        {_metric_cell("Доход на вложенное (30%)", f"{coc_inst}%", "рассрочка")}
        {_metric_cell("Мультипликатор", f"{eq_full}x", f"рассрочка {eq_inst}x")}
    </div>'''


def _build_profitability(roi: dict) -> str:
    return f'''
    {_section_title("Доходность за 11 лет")}
    <div style="background:rgba(91,140,90,0.15); border:1px solid {C["green_highlight"]}; border-radius:12px; padding:16px; margin-bottom:12px;">
        <table style="width:100%;"><tr>
            <td><div style="font-size:14px; font-weight:500; color:{C["green_highlight"]};">Доходность за 11 лет</div>
                <div style="font-size:12px; color:{C["text_secondary"]};">~{roi.get("avg_annual_pct", 0)}% годовых</div></td>
            <td style="text-align:right;"><div style="font-size:28px; font-weight:600; color:{C["green_highlight"]};">{roi.get("roi_pct", 0)}%</div></td>
        </tr></table>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px;">
            <div style="background:{C["metric_bg"]}; border-radius:8px; padding:10px;">
                <div style="font-size:10px; color:{C["text_muted"]};">Аренда</div>
                <div style="font-size:14px; font-weight:600; color:{C["gold"]};">{_fmt(roi.get("total_rental", 0))} ₽</div>
            </div>
            <div style="background:{C["metric_bg"]}; border-radius:8px; padding:10px;">
                <div style="font-size:10px; color:{C["text_muted"]};">Рост стоимости</div>
                <div style="font-size:14px; font-weight:600; color:{C["gold"]};">{_fmt(roi.get("total_growth", 0))} ₽</div>
            </div>
        </div>
        <div style="margin-top:10px; padding-top:10px; border-top:1px solid {C["card_border"]};">
            <table style="width:100%;"><tr>
                <td><div style="font-size:10px; color:{C["text_muted"]};">Общая прибыль</div>
                    <div style="font-size:15px; font-weight:600; color:{C["gold"]};">{_fmt(roi.get("total_profit", 0))} ₽</div></td>
                <td style="text-align:right;"><div style="font-size:10px; color:{C["text_muted"]};">Стоимость в 2035</div>
                    <div style="font-size:15px; font-weight:600; color:{C["text"]};">{_fmt(roi.get("final_value", 0))} ₽</div></td>
            </tr></table>
        </div>
    </div>'''


def _build_payments(inst: dict, price: int) -> str:
    price_100 = round(price * 0.95)
    saving = round(price * 0.05)
    i12 = inst.get("i12", {})
    i18 = inst.get("i18", {})

    def row(label, value):
        return f'''<tr>
            <td style="padding:4px 0; font-size:11px; color:{C["text_secondary"]};">{label}</td>
            <td style="padding:4px 0; font-size:11px; font-weight:500; text-align:right; color:{C["text"]};">{value}</td>
        </tr>'''

    return f'''
    {_section_title("Варианты оплаты")}
    <div style="background:rgba(91,140,90,0.15); border:1px solid {C["green_highlight"]}; border-radius:12px; padding:14px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:600; color:{C["green_highlight"]};">100% оплата (скидка 5%)</div>
        <div style="font-size:18px; font-weight:600; color:{C["text"]}; margin-top:4px;">{_fmt(price_100)} ₽</div>
        <div style="font-size:11px; color:{C["text_muted"]};">Экономия: {_fmt(saving)} ₽</div>
    </div>
    <div style="background:{C["card_bg"]}; border:1px solid {C["green_highlight"]}; border-radius:12px; padding:14px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:600; color:{C["green_highlight"]}; margin-bottom:8px;">12 месяцев (0%)</div>
        <table style="width:100%; border-collapse:collapse;">
            {row("ПВ 30%", f"{_fmt(i12.get('pv_30', 0))} ₽ → {_fmt(i12.get('monthly_30', 0))} ₽/мес")}
            {row("ПВ 40%", f"{_fmt(i12.get('pv_40', 0))} ₽ → 11×200К + {_fmt(i12.get('last_40', 0))} ₽")}
            {row("ПВ 50%", f"{_fmt(i12.get('pv_50', 0))} ₽ → 11×100К + {_fmt(i12.get('last_50', 0))} ₽")}
        </table>
    </div>
    <div style="background:{C["card_bg"]}; border:1px solid {C["gold"]}; border-radius:12px; padding:14px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:600; color:{C["gold"]}; margin-bottom:8px;">18 месяцев</div>
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
            <td style="padding:7px 10px; font-size:11px; color:{C["text_secondary"]}; border-bottom:1px solid {C["card_border"]};">{d.get("scenario_name", key)}</td>
            <td style="padding:7px 10px; font-size:11px; font-weight:500; text-align:right; color:{C["text"]}; border-bottom:1px solid {C["card_border"]};">{_fmt(d.get("total_net_interest", 0))} ₽</td>
            <td style="padding:7px 10px; font-size:11px; text-align:right; color:{C["text_muted"]}; border-bottom:1px solid {C["card_border"]};">{d.get("total_roi_pct", 0)}%</td>
        </tr>'''

    advantage_html = ""
    if advantage > 0:
        advantage_html = f'''
        <div style="background:{C["gold"]}; color:{C["bg"]}; padding:10px 16px; border-radius:8px; margin-bottom:10px; font-weight:600; font-size:13px;">
            ✅ RIZALTA выгоднее на {_fmt(advantage)} ₽
        </div>'''

    return f'''
    {_section_title("RIZALTA vs Депозит (11 лет)")}
    {advantage_html}
    <div style="background:rgba(91,140,90,0.15); border:1px solid {C["green_highlight"]}; border-radius:8px; padding:12px; margin-bottom:10px;">
        <table style="width:100%;"><tr>
            <td><span style="font-size:13px; font-weight:500; color:{C["green_highlight"]};">🏠 RIZALTA</span></td>
            <td style="text-align:right;"><span style="font-size:18px; font-weight:600; color:{C["green_highlight"]};">{_fmt(total_profit)} ₽</span></td>
        </tr></table>
        <div style="font-size:11px; color:{C["text_secondary"]};">ROI: {roi.get("roi_pct", 0)}% за 11 лет</div>
    </div>
    <table style="width:100%; border-collapse:collapse; background:{C["card_bg"]}; border-radius:8px;">
        <thead>
            <tr style="background:{C["metric_bg"]};">
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:left; color:{C["text_muted"]};">Сценарий</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right; color:{C["text_muted"]};">Доход</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right; color:{C["text_muted"]};">ROI</th>
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
        bg = C["metric_bg"] if i % 2 == 1 else C["card_bg"]
        rows += f'''
        <tr style="background:{bg};">
            <td style="padding:5px 10px; font-size:11px; font-weight:500; color:{C["text"]};">{yr.get("year", "")}</td>
            <td style="padding:5px 10px; font-size:11px; font-weight:500; text-align:right; color:{C["gold"]};">{_fmt(yr.get("nominal", 0))} ₽</td>
            <td style="padding:5px 10px; font-size:11px; text-align:right; color:{C["text_secondary"]};">{_fmt(yr.get("commercial", 0))} ₽</td>
        </tr>'''

    return f'''
    {_section_title("Минимальный гарантированный платёж")}
    <table style="width:100%; border-collapse:collapse; border-radius:8px; overflow:hidden;">
        <thead>
            <tr style="background:{C["metric_bg"]};">
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:left; color:{C["text_muted"]};">Год</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right; color:{C["text_muted"]};">Номерной, ₽</th>
                <th style="padding:8px 10px; font-size:10px; font-weight:500; text-align:right; color:{C["text_muted"]};">Коммерч., ₽</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
        <tfoot>
            <tr style="background:{C["gold"]};">
                <td style="padding:7px 10px; font-size:11px; font-weight:600; color:{C["bg"]};">Итого</td>
                <td style="padding:7px 10px; font-size:11px; font-weight:600; text-align:right; color:{C["bg"]};">{_fmt(mgp.get("total_nominal", 0))} ₽</td>
                <td style="padding:7px 10px; font-size:11px; font-weight:600; text-align:right; color:{C["bg"]};">{_fmt(mgp.get("total_commercial", 0))} ₽</td>
            </tr>
        </tfoot>
    </table>'''


def _build_mortgage(mort: dict) -> str:
    def row(label, value, bold=False, gold=False):
        weight = "600" if bold else "400"
        color = C["gold"] if gold else C["text"]
        return f'''<tr>
            <td style="padding:5px 0; font-size:12px; color:{C["text_secondary"]};">{label}</td>
            <td style="padding:5px 0; font-size:{'14px' if gold else '12px'}; font-weight:{weight}; text-align:right; color:{color};">{value}</td>
        </tr>'''

    return f'''
    {_section_title("Ипотека (Совкомбанк)")}
    <div style="background:{C["card_bg"]}; border:1px solid {C["card_border"]}; border-radius:12px; padding:16px;">
        <div style="font-size:11px; color:{C["text_muted"]}; margin-bottom:10px;">Базовый тариф · ПВ 30% · 30 лет</div>
        <table style="width:100%; border-collapse:collapse;">
            {row("Первонач. взнос", f"{_fmt(mort.get('down_payment', 0))} ₽", bold=True)}
            {row("Сумма кредита", f"{_fmt(mort.get('loan_amount', 0))} ₽", bold=True)}
        </table>
        <div style="border-top:1px solid {C["card_border"]}; margin:6px 0;"></div>
        <table style="width:100%; border-collapse:collapse;">
            {row("Платёж (льготный)", f"{_fmt(mort.get('grace_payment', 0))} ₽/мес", bold=True, gold=True)}
            {row("Платёж (после)", f"{_fmt(mort.get('regular_payment', 0))} ₽/мес", bold=True)}
            {row("Ставка", f"{mort.get('rate_after_grace', '')}% годовых")}
        </table>
    </div>'''


def generate_lot_summary_pdf(data: dict) -> bytes | None:
    """Generate comprehensive lot summary PDF (dark theme).

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
    <div style="font-size:14px; color:{C["text_secondary"]}; margin-top:4px;">Инвестиционная сводка · {code}</div>
</div>

{sections}

<div style="text-align:center; color:{C["text_muted"]}; font-size:11px; margin-top:24px; padding-top:12px; border-top:1px solid {C["card_border"]};">
    RIZALTA Resort Belokurikha · Инвестиционная сводка · {today}
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

        logger.error(f"[LOT SUMMARY PDF] wkhtmltopdf failed: {result.stderr.decode()}")
        os.unlink(html_path)
        return None

    except Exception as e:
        logger.error(f"[LOT SUMMARY PDF] Error: {e}")
        return None
