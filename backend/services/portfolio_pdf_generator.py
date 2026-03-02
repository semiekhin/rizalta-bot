"""Portfolio PDF generator — renders chat-style cards to PDF via wkhtmltopdf."""

import os
import re
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
    "white": "#FAFAF5",
}


def _fmt(n) -> str:
    """Format number with space thousands separator."""
    if n is None:
        return "—"
    try:
        return f"{int(n):,}".replace(",", " ")
    except (ValueError, TypeError):
        return str(n)


def _build_metric_cell(label: str, value: str, highlight: bool = False) -> str:
    bg = RIZALTA_COLORS["metric_bg"] if highlight else RIZALTA_COLORS["card_bg"]
    color = RIZALTA_COLORS["gold"] if highlight else RIZALTA_COLORS["text"]
    return f'''
    <div style="background:{bg}; padding:12px; border-radius:8px;">
        <div style="font-size:11px; color:{RIZALTA_COLORS['text_muted']}; text-transform:uppercase; margin-bottom:4px;">{label}</div>
        <div style="font-size:16px; font-weight:600; color:{color};">{value}</div>
    </div>'''


def _build_scenario_1(sp: dict) -> str:
    """Premium lot scenario card."""
    if sp.get("error"):
        return ""
    lot = sp.get("lot", {})
    m = sp.get("metrics", {})
    return f'''
    <div style="background:{RIZALTA_COLORS['card_bg']}; border:1px solid {RIZALTA_COLORS['card_border']}; border-radius:12px; padding:20px; margin-bottom:20px;">
        <div style="color:{RIZALTA_COLORS['gold']}; font-size:16px; font-weight:600; margin-bottom:4px;">◆ Один премиальный лот (100%)</div>
        <div style="color:{RIZALTA_COLORS['text_secondary']}; font-size:13px; margin-bottom:16px;">
            {lot.get("code", "")}, {lot.get("area_m2", "")} м², корпус {lot.get("building", "")} · ROI {sp.get("roi_pct", "")}%
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;">
            {_build_metric_cell("Цена (скидка 5%)", f"{_fmt(sp.get('discounted_price'))} ₽")}
            {_build_metric_cell("Остаток", f"{_fmt(sp.get('remaining_cash'))} ₽")}
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:8px; margin-bottom:12px;">
            {_build_metric_cell("Чистый доход / год", f"{_fmt(m.get('noi'))} ₽", True)}
            {_build_metric_cell("Доходность (Cap Rate)", f"{m.get('cap_rate', 0)}%", True)}
            {_build_metric_cell("ROI 11 лет", f"{sp.get('roi_pct', 0)}%")}
            {_build_metric_cell("Доход на вложенное", f"{m.get('coc_full', 0)}%")}
        </div>
        <div style="display:flex; justify-content:space-between; padding:8px 0; border-top:1px solid {RIZALTA_COLORS['card_border']};">
            <span style="color:{RIZALTA_COLORS['text_secondary']};">Прибыль 11 лет</span>
            <span style="color:{RIZALTA_COLORS['gold']}; font-weight:600;">{_fmt(sp.get('total_profit'))} ₽ ({sp.get('roi_pct', 0)}%)</span>
        </div>
        <div style="color:{RIZALTA_COLORS['text_muted']}; font-size:12px; font-style:italic; margin-top:8px;">
            {sp.get('reasoning', '')}
        </div>
        <div style="color:{RIZALTA_COLORS['green_highlight']}; font-size:13px; margin-top:8px;">
            +{_fmt(sp.get('vs_deposit'))} ₽ vs депозит
        </div>
    </div>'''


def _build_scenario_2(sf: dict) -> str:
    """Full payment portfolio scenario card."""
    if sf.get("error"):
        return ""
    lots_html = ""
    for lot in sf.get("lots", []):
        lots_html += f'''
        <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid {RIZALTA_COLORS['card_border']};">
            <span style="color:{RIZALTA_COLORS['text']}; font-weight:500;">{lot.get("code", "")} <span style="color:{RIZALTA_COLORS['text_secondary']};">К{lot.get("building", "")}, {lot.get("floor", "")}эт. {lot.get("area_m2", "")} м²</span></span>
            <span style="color:{RIZALTA_COLORS['text']};">{_fmt(lot.get("discounted_price"))} ₽ <span style="color:{RIZALTA_COLORS['text_muted']};">ROI {lot.get("roi_pct", "")}%</span></span>
        </div>'''

    return f'''
    <div style="background:{RIZALTA_COLORS['card_bg']}; border:1px solid {RIZALTA_COLORS['card_border']}; border-radius:12px; padding:20px; margin-bottom:20px;">
        <div style="color:{RIZALTA_COLORS['green_highlight']}; font-size:16px; font-weight:600; margin-bottom:4px;">◈ Портфель 100% оплата</div>
        <div style="color:{RIZALTA_COLORS['text_secondary']}; font-size:13px; margin-bottom:16px;">
            {sf.get("lot_count", 0)} лотов, вложено {_fmt(sf.get("total_invested"))} ₽
        </div>
        {lots_html}
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:8px; margin:12px 0;">
            {_build_metric_cell("Чистый доход / год", f"{_fmt(sf.get('total_noi'))} ₽", True)}
            {_build_metric_cell("Доходность (Cap Rate)", f"{sf.get('avg_cap_rate', 0)}%", True)}
            {_build_metric_cell("ROI 11 лет", f"{sf.get('avg_roi_pct', 0)}%")}
            {_build_metric_cell("Доход на вложенное", f"{sf.get('avg_coc_full', 0)}%")}
        </div>
        <div style="display:flex; justify-content:space-between; padding:8px 0; border-top:1px solid {RIZALTA_COLORS['card_border']};">
            <span style="color:{RIZALTA_COLORS['text_secondary']};">Прибыль 11 лет</span>
            <span style="color:{RIZALTA_COLORS['gold']}; font-weight:600;">{_fmt(sf.get('total_profit'))} ₽</span>
        </div>
        <div style="color:{RIZALTA_COLORS['text_muted']}; font-size:12px; font-style:italic; margin-top:8px;">
            {sf.get('reasoning', '')}
        </div>
        <div style="color:{RIZALTA_COLORS['green_highlight']}; font-size:13px; margin-top:8px;">
            +{_fmt(sf.get('vs_deposit'))} ₽ vs депозит
        </div>
    </div>'''


def _build_scenario_3(sl: dict) -> str:
    """Leverage scenario card."""
    if sl.get("error"):
        return ""
    lots_html = ""
    for lot in sl.get("lots", []):
        lots_html += f'''
        <div style="padding:8px 0; border-bottom:1px solid {RIZALTA_COLORS['card_border']};">
            <div style="display:flex; justify-content:space-between;">
                <span style="color:{RIZALTA_COLORS['text']}; font-weight:500;">{lot.get("code", "")} <span style="color:{RIZALTA_COLORS['text_secondary']};">К{lot.get("building", "")}, {lot.get("floor", "")}эт.</span></span>
                <span style="color:{RIZALTA_COLORS['text']};">{_fmt(lot.get("price_rub"))} ₽ <span style="color:{RIZALTA_COLORS['text_muted']};">ROI {lot.get("roi_pct", "")}%</span></span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:2px;">
                <span style="color:{RIZALTA_COLORS['text_muted']}; font-size:12px;">ПВ {_fmt(lot.get("down_payment"))} ₽</span>
                <span style="color:{RIZALTA_COLORS['text_muted']}; font-size:12px;">{_fmt(lot.get("monthly_payment"))} ₽/мес</span>
            </div>
        </div>'''

    return f'''
    <div style="background:{RIZALTA_COLORS['card_bg']}; border:1px solid {RIZALTA_COLORS['card_border']}; border-radius:12px; padding:20px; margin-bottom:20px;">
        <div style="color:{RIZALTA_COLORS['text']}; font-size:16px; font-weight:600; margin-bottom:4px;">◇ Максимальное плечо (рассрочка)</div>
        <div style="color:{RIZALTA_COLORS['text_secondary']}; font-size:13px; margin-bottom:16px;">
            {sl.get("lot_count", 0)} лотов, портфель {_fmt(sl.get("total_portfolio_value"))} ₽
        </div>
        {lots_html}
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin:12px 0;">
            {_build_metric_cell("Чистый доход / год", f"{_fmt(sl.get('total_noi'))} ₽", True)}
            {_build_metric_cell("Доходность (Cap Rate)", f"{sl.get('avg_cap_rate', 0)}%", True)}
            {_build_metric_cell("ROI 11 лет", f"{sl.get('avg_roi_pct', 0)}%")}
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:12px;">
            {_build_metric_cell("Первоначальный взнос", f"{_fmt(sl.get('total_down_payment'))} ₽")}
            {_build_metric_cell("Платёж / мес", f"{_fmt(sl.get('total_monthly'))} ₽", True)}
            {_build_metric_cell("Переплата по рассрочке", f"{_fmt(sl.get('total_markup'))} ₽")}
        </div>
        <div style="display:flex; justify-content:space-between; padding:8px 0; border-top:1px solid {RIZALTA_COLORS['card_border']};">
            <span style="color:{RIZALTA_COLORS['text_secondary']};">Чистая прибыль</span>
            <span style="color:{RIZALTA_COLORS['gold']}; font-weight:600;">{_fmt(sl.get('net_profit'))} ₽</span>
        </div>
        <div style="color:{RIZALTA_COLORS['text_muted']}; font-size:12px; font-style:italic; margin-top:8px;">
            {sl.get('reasoning', '')}
        </div>
        <div style="color:{RIZALTA_COLORS['green_highlight']}; font-size:13px; margin-top:8px;">
            +{_fmt(sl.get('vs_deposit'))} ₽ vs депозит
        </div>
    </div>'''


def _build_deposit_card(deposit: dict) -> str:
    """Deposit comparison card."""
    base = deposit.get("base", {})
    final = base.get("final_balance", 0)
    interest = base.get("total_net_interest", 0)
    roi = base.get("total_roi_pct", 0)
    return f'''
    <div style="background:{RIZALTA_COLORS['metric_bg']}; border:1px solid {RIZALTA_COLORS['card_border']}; border-radius:12px; padding:16px; margin-bottom:20px;">
        <div style="color:{RIZALTA_COLORS['text_muted']}; font-size:12px; text-transform:uppercase; margin-bottom:4px;">Депозит для сравнения (11 лет)</div>
        <div style="color:{RIZALTA_COLORS['text']}; font-size:20px; font-weight:600;">{_fmt(final)} ₽</div>
        <div style="color:{RIZALTA_COLORS['text_secondary']}; font-size:13px;">Проценты: {_fmt(interest)} ₽ · ROI {roi}%</div>
    </div>'''


def generate_portfolio_pdf(data: dict, ai_text: str = "") -> bytes | None:
    """Generate portfolio PDF from report data + AI analysis text.

    Returns PDF bytes or None on error.
    """
    budget = data.get("budget", 0)
    sp = data.get("scenario_premium", {})
    sf = data.get("scenario_portfolio", {})
    sl = data.get("scenario_leverage", {})
    deposit = data.get("deposit_comparison", {})

    # AI text — convert **bold** and newlines to paragraphs
    ai_paragraphs = ""
    if ai_text:
        for para in ai_text.strip().split("\n\n"):
            clean = para.strip().replace("\n", " ")
            if clean:
                clean = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', clean)
                ai_paragraphs += f'<p style="margin:0 0 12px 0; line-height:1.6;">{clean}</p>'

    # Read Montserrat font base64 for embedded font
    webapp_root = os.getenv("WEBAPP_ROOT", ".")
    font_face = ""
    font_path = os.path.join(webapp_root, "backend/resources/montserrat_regular_base64.txt")
    font_medium_path = os.path.join(webapp_root, "backend/resources/montserrat_medium_base64.txt")
    font_semibold_path = os.path.join(webapp_root, "backend/resources/montserrat_semibold_base64.txt")

    if os.path.exists(font_path):
        with open(font_path) as f:
            font_regular = f.read().strip()
        font_face += f"@font-face {{ font-family: 'Montserrat'; font-weight: 400; src: url(data:font/ttf;base64,{font_regular}) format('truetype'); }}\n"
    if os.path.exists(font_medium_path):
        with open(font_medium_path) as f:
            font_medium = f.read().strip()
        font_face += f"@font-face {{ font-family: 'Montserrat'; font-weight: 500; src: url(data:font/ttf;base64,{font_medium}) format('truetype'); }}\n"
    if os.path.exists(font_semibold_path):
        with open(font_semibold_path) as f:
            font_semibold = f.read().strip()
        font_face += f"@font-face {{ font-family: 'Montserrat'; font-weight: 600; src: url(data:font/ttf;base64,{font_semibold}) format('truetype'); }}\n"

    today = date.today().strftime('%d.%m.%Y')

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    {font_face}
    @page {{ size: A4; margin: 20mm 15mm; }}
    body {{
        font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif;
        background: {RIZALTA_COLORS['bg']};
        color: {RIZALTA_COLORS['text']};
        font-size: 14px;
        line-height: 1.5;
        margin: 0;
        padding: 20px;
    }}
</style>
</head>
<body>

<div style="text-align:center; margin-bottom:24px; padding-bottom:16px; border-bottom:2px solid {RIZALTA_COLORS['gold']};">
    <div style="font-size:24px; font-weight:700; color:{RIZALTA_COLORS['gold']};">RIZALTA Resort Belokurikha</div>
    <div style="font-size:14px; color:{RIZALTA_COLORS['text_secondary']}; margin-top:4px;">Портфельный анализ — 3 сценария</div>
    <div style="font-size:28px; font-weight:700; color:{RIZALTA_COLORS['text']}; margin-top:8px;">{_fmt(budget)} ₽</div>
</div>

{_build_scenario_1(sp)}
{_build_scenario_2(sf)}
{_build_scenario_3(sl)}
{_build_deposit_card(deposit)}

{"" if not ai_paragraphs else f"""
<div style="background:{RIZALTA_COLORS['card_bg']}; border-radius:12px; padding:20px; margin-bottom:20px;">
    <div style="font-size:16px; font-weight:600; color:{RIZALTA_COLORS['gold']}; margin-bottom:12px;">Аналитика</div>
    <div style="color:{RIZALTA_COLORS['text']}; font-size:13px;">
        {ai_paragraphs}
    </div>
</div>"""}

<div style="text-align:center; color:{RIZALTA_COLORS['text_muted']}; font-size:11px; margin-top:24px; padding-top:12px; border-top:1px solid {RIZALTA_COLORS['card_border']};">
    RIZALTA Resort Belokurikha · Инвестиционный анализ · {today}
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

        logger.error(f"[PORTFOLIO PDF] wkhtmltopdf failed: {result.stderr.decode()}")
        os.unlink(html_path)
        return None

    except Exception as e:
        logger.error(f"[PORTFOLIO PDF] Error: {e}")
        return None
