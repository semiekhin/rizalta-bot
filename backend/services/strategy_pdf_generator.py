"""Strategy PDF generator — RIZALTA branded investment reports.

Two report types:
- Lot report: 4 pages (title, ROI, deposit comparison, payment options)
- Portfolio report: 4 pages (title, lots table, analysis, deposit comparison)

Style matches kp_pdf_generator.py: Montserrat fonts, green/gold/cream palette.
"""

import os
import subprocess
import tempfile
import logging
import base64
import requests
from pathlib import Path
from datetime import datetime

from services.calculator import calculate_roi
from services.installment_calculator import calc_12m, calc_18m
from services.deposit_calculator import calculate_all_scenarios
from services.investment_compare import calculate_rizalta

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
RESOURCES_DIR = BASE_DIR / "resources"


# ─── Utilities ───────────────────────────────────────────────────────────────

def load_resource(filename: str) -> str:
    path = RESOURCES_DIR / filename
    return path.read_text().strip() if path.exists() else ""


def fmt(price) -> str:
    return f"{int(round(price)):,}".replace(",", " ") + " ₽"


def fmt_num(val) -> str:
    return f"{int(round(val)):,}".replace(",", " ")


def fmt_pct(val) -> str:
    return f"{val:.1f}%"


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_building_name(building) -> str:
    if isinstance(building, str):
        return building
    names = {1: '1 — "Family"', 2: '2 — "Business"', 3: '3 — "Digital"'}
    return names.get(building, str(building))


def _download_layout(url: str) -> str:
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    except Exception:
        return ""


# ─── Data extraction from agentic loop results ──────────────────────────────

def _detect_report_type(data: dict) -> str:
    tools = data.get("tools_used", [])
    if "get_lot_details" in tools or "calculate_roi" in tools:
        return "lot"
    if "search_lots" in tools:
        return "portfolio"
    return "lot" if data.get("lot_data") else "portfolio"


def _extract_lot_data(results: dict) -> dict | None:
    for key, val in results.items():
        if key.startswith("get_lot_details") and isinstance(val, dict) and "code" in val and "error" not in val:
            return val
    return None


def _extract_search_lots(results: dict) -> list:
    for key, val in results.items():
        if key.startswith("search_lots") and isinstance(val, dict) and "lots" in val:
            return val["lots"]
    return []


# ─── CSS ─────────────────────────────────────────────────────────────────────

def _get_base_css() -> str:
    font_regular = load_resource("montserrat_regular_base64.txt")
    font_medium = load_resource("montserrat_medium_base64.txt")
    font_semibold = load_resource("montserrat_semibold_base64.txt")

    return f"""
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_regular}) format('truetype'); font-weight: 400; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_medium}) format('truetype'); font-weight: 500; }}
@font-face {{ font-family: 'Montserrat'; src: url(data:font/truetype;base64,{font_semibold}) format('truetype'); font-weight: 600; }}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Montserrat', Arial, sans-serif; background: #F6F0E3; color: #313D20; font-size: 13px; line-height: 1.5; }}

.page {{ width: 210mm; min-height: 297mm; position: relative; overflow: hidden; background: #F6F0E3; }}
.page-break {{ page-break-before: always; }}

.header-table {{ width: 100%; height: 140px; background: #313D20; }}
.header-table td {{ text-align: center; vertical-align: middle; }}
.logo-header {{ height: 100px; }}

.title-bar {{ background: #DCB764; padding: 14px 40px; overflow: hidden; }}
.title-left {{ float: left; font-size: 18px; font-weight: 500; color: #313D20; }}
.title-right {{ float: right; font-size: 13px; font-weight: 500; color: #313D20; line-height: 24px; }}

.content {{ padding: 25px 40px; }}

.section-title {{ font-size: 17px; font-weight: 600; color: #313D20; margin: 20px 0 12px; padding-bottom: 6px; border-bottom: 2px solid #DCB764; }}

.data-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
.data-table th {{ background: #313D20; color: #F6F0E3; padding: 8px 12px; text-align: left; font-size: 11px; font-weight: 500; }}
.data-table td {{ padding: 7px 12px; border-bottom: 1px solid rgba(49, 61, 32, 0.15); font-size: 11px; }}
.data-table tr:nth-child(even) {{ background: rgba(49, 61, 32, 0.04); }}
.data-table .num {{ text-align: right; font-weight: 500; }}
.data-table .total {{ background: rgba(220, 183, 100, 0.15); }}
.data-table .total td {{ font-weight: 600; }}

.detail-table {{ width: 100%; border-collapse: collapse; }}
.detail-table td {{ padding: 10px 0; border-bottom: 1px solid rgba(49, 61, 32, 0.15); }}
.detail-label {{ color: #313D20; font-size: 14px; }}
.detail-value {{ text-align: right; font-weight: 600; font-size: 14px; }}

.metrics {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
.metric {{ text-align: center; padding: 15px 10px; background: white; vertical-align: top; border: 1px solid rgba(49, 61, 32, 0.1); }}
.metric-value {{ font-size: 22px; font-weight: 600; color: #313D20; }}
.metric-label {{ font-size: 10px; color: #313D20; margin-top: 4px; opacity: 0.7; }}

.gold-box {{ background: #DCB764; color: #313D20; padding: 18px 25px; text-align: center; margin: 15px 0; }}
.gold-box-title {{ font-size: 11px; font-weight: 500; letter-spacing: 2px; }}
.gold-box-value {{ font-size: 26px; font-weight: 600; margin-top: 4px; }}
.gold-box-sub {{ font-size: 13px; margin-top: 3px; }}

.green-box {{ background: #313D20; color: #F6F0E3; padding: 16px 25px; text-align: center; margin: 15px 0; }}
.green-box-value {{ font-size: 22px; font-weight: 600; color: #DCB764; margin-top: 4px; }}

.options-table {{ width: 100%; border-collapse: collapse; }}
.option-card {{ background: white; border: 2px solid #313D20; padding: 16px; text-align: center; vertical-align: top; }}
.option-card-mid {{ border-left: none; border-right: none; }}
.option-card-18 {{ background: white; border: 2px solid #DCB764; padding: 16px; text-align: center; vertical-align: top; }}
.option-card-18-mid {{ border-left: none; border-right: none; }}
.option-pv {{ font-size: 12px; color: #313D20; margin-bottom: 8px; font-weight: 500; }}
.option-badge {{ display: inline-block; background: #DCB764; color: #313D20; font-size: 10px; font-weight: 600; padding: 2px 6px; margin-left: 4px; }}
.option-amount {{ font-size: 18px; font-weight: 600; color: #313D20; margin-bottom: 10px; }}
.option-monthly {{ font-size: 11px; color: #313D20; line-height: 1.6; font-weight: 500; }}
.option-total {{ font-size: 11px; color: #313D20; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(49, 61, 32, 0.15); }}
.option-total-sum {{ font-size: 13px; font-weight: 600; color: #DCB764; margin-top: 3px; }}

.footer {{ background: #313D20; text-align: center; padding: 18px; }}
.footer-text {{ font-size: 11px; color: #F6F0E3; letter-spacing: 4px; }}

.disclaimer {{ font-size: 9px; color: rgba(49, 61, 32, 0.5); text-align: center; margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(49, 61, 32, 0.15); }}
"""


# ─── Main entry point ────────────────────────────────────────────────────────

def generate_strategy_pdf(data: dict) -> str | None:
    """Generate investment strategy PDF from AI chat analysis.

    Args:
        data: dict with tools_used, results, user_query, response_text, lot_data

    Returns: path to generated PDF or None
    """
    report_type = _detect_report_type(data)

    try:
        if report_type == "lot":
            html = _generate_lot_report(data)
        else:
            html = _generate_portfolio_report(data)

        if not html:
            logger.error("[STRATEGY PDF] Failed to generate HTML")
            return None

        return _html_to_pdf(html)
    except Exception as e:
        logger.error(f"[STRATEGY PDF] Error: {e}")
        return None


# ─── Lot report (4 pages) ────────────────────────────────────────────────────

def _generate_lot_report(data: dict) -> str | None:
    results = data.get("results", {})
    lot = data.get("lot_data") or _extract_lot_data(results)
    if not lot:
        logger.warning("[STRATEGY PDF] No lot data found")
        return None

    code = lot.get("code", "")
    area = lot.get("area_m2", 26.8)
    price = lot.get("price_rub", 0)
    floor = lot.get("floor", "—")
    building_num = lot.get("building_num", 1)
    building_str = lot.get("building", "")
    price_m2 = lot.get("price_per_m2", int(price / area) if area > 0 else 0)
    layout_url = lot.get("layout_url", "")
    user_query = _escape_html(data.get("user_query", ""))
    date_str = datetime.now().strftime("%d.%m.%Y")
    logo_b64 = load_resource("logo_mono_trim_base64.txt")
    layout_b64 = _download_layout(layout_url)

    # Calculations
    roi = calculate_roi(area, price)
    deposit_scenarios = calculate_all_scenarios(price, 11)
    dep_base = deposit_scenarios["base"]
    rizalta = calculate_rizalta(price, 11, area)
    advantage = rizalta.total_profit - dep_base.total_net_interest
    advantage_pct = (advantage / price * 100) if price > 0 else 0
    i12 = calc_12m(price)
    i18 = calc_18m(price)

    bname = get_building_name(building_num) if isinstance(building_num, int) and building_num in (1, 2, 3) else building_str or str(building_num)
    css = _get_base_css()

    # ── PAGE 1: Title + Lot Details ──
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>{css}</style></head><body>

<div class="page">
  <table class="header-table"><tr><td>
    {"<img class='logo-header' src='data:image/png;base64," + logo_b64 + "'>" if logo_b64 else ""}
  </td></tr></table>

  <div class="title-bar">
    <div class="title-left">Инвестиционный отчёт</div>
    <div class="title-right">{date_str} &bull; AI Financial Advisor</div>
    <div style="clear:both"></div>
  </div>

  <div class="content">
    <div style="background: white; margin-top: 15px;">
      <div style="background: #313D20; padding: 14px 22px; overflow: hidden;">
        <div style="float: left; font-size: 22px; font-weight: 500; color: #F6F0E3;">Апартамент {code}</div>
        <div style="float: right; font-size: 24px; font-weight: 600; color: #DCB764;">{fmt(price)}</div>
        <div style="clear:both"></div>
      </div>

      <div style="padding: 20px 22px; overflow: hidden;">
        {f'<div style="float: left; width: 340px;"><img style="max-width: 330px; max-height: 280px;" src="data:image/jpeg;base64,{layout_b64}"></div>' if layout_b64 else ''}
        <div style="{'margin-left: 360px;' if layout_b64 else ''}">
          <table class="detail-table">
            <tr><td class="detail-label">Корпус</td><td class="detail-value">{bname}</td></tr>
            <tr><td class="detail-label">Этаж</td><td class="detail-value">{floor}</td></tr>
            <tr><td class="detail-label">Площадь</td><td class="detail-value">{area} м&sup2;</td></tr>
            <tr><td class="detail-label">Цена за м&sup2;</td><td class="detail-value">{fmt(price_m2)}</td></tr>
            <tr><td class="detail-label">Сдача</td><td class="detail-value">4 кв. 2027</td></tr>
          </table>
        </div>
        <div style="clear:both"></div>
      </div>
    </div>

    {f'<div style="margin-top: 20px; font-style: italic; color: rgba(49,61,32,0.6); font-size: 11px; border-left: 3px solid #DCB764; padding-left: 12px;">Запрос: &laquo;{user_query}&raquo;</div>' if user_query else ''}
    <div class="disclaimer">Расчёты носят прогнозный характер и не являются публичной офертой.</div>
  </div>

  <div class="footer"><div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div></div>
</div>
"""

    # ── PAGE 2: ROI ──
    years_rows = ""
    for y in roi["years"]:
        years_rows += f"""<tr>
  <td>{y['year']}</td>
  <td class="num">{fmt(y['growth_profit'])}</td>
  <td class="num">{fmt(y['rental_profit'])}</td>
  <td class="num">{fmt(y['growth_profit'] + y['rental_profit'])}</td>
  <td class="num">{fmt(y['current_value'])}</td>
</tr>
"""

    html += f"""
<div class="page page-break">
  <div class="content" style="padding-top: 35px;">
    <div class="section-title">Прогноз доходности (2025 — 2035)</div>

    <table class="data-table">
      <tr>
        <th>Год</th>
        <th style="text-align:right">Рост стоимости</th>
        <th style="text-align:right">Доход от аренды</th>
        <th style="text-align:right">Итого за год</th>
        <th style="text-align:right">Стоимость актива</th>
      </tr>
      {years_rows}
      <tr class="total">
        <td><strong>ИТОГО</strong></td>
        <td class="num">{fmt(roi['total_growth'])}</td>
        <td class="num">{fmt(roi['total_rental'])}</td>
        <td class="num">{fmt(roi['total_profit'])}</td>
        <td class="num">{fmt(roi['final_value'])}</td>
      </tr>
    </table>

    <table class="metrics">
      <tr>
        <td class="metric">
          <div class="metric-value">{fmt_pct(roi['roi_pct'])}</div>
          <div class="metric-label">ОБЩИЙ ROI</div>
        </td>
        <td class="metric">
          <div class="metric-value">{fmt_pct(roi['avg_annual_pct'])}</div>
          <div class="metric-label">СРЕДНЕГОДОВАЯ</div>
        </td>
        <td class="metric">
          <div class="metric-value">{fmt(roi['total_rental'])}</div>
          <div class="metric-label">АРЕНДА ЗА 11 ЛЕТ</div>
        </td>
        <td class="metric">
          <div class="metric-value">{fmt(roi['final_value'])}</div>
          <div class="metric-label">СТОИМОСТЬ К 2035</div>
        </td>
      </tr>
    </table>

    <div class="disclaimer">Рост стоимости: +18-20%/год (стройка), +8.8-10%/год (после сдачи). Аренда с 2028.</div>
  </div>

  <div class="footer"><div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div></div>
</div>
"""

    # ── PAGE 3: Deposit Comparison ──
    dep_pess = deposit_scenarios["pessimistic"]
    dep_opt = deposit_scenarios["optimistic"]
    riz_total_capital = rizalta.final_value + rizalta.total_rental_profit

    html += f"""
<div class="page page-break">
  <div class="content" style="padding-top: 35px;">
    <div class="section-title">RIZALTA vs Банковский депозит</div>

    <table class="data-table">
      <tr>
        <th>Показатель</th>
        <th style="text-align:right">Депозит (пессим.)</th>
        <th style="text-align:right">Депозит (базовый)</th>
        <th style="text-align:right">Депозит (оптим.)</th>
      </tr>
      <tr>
        <td>Чистый доход</td>
        <td class="num">{fmt(dep_pess.total_net_interest)}</td>
        <td class="num">{fmt(dep_base.total_net_interest)}</td>
        <td class="num">{fmt(dep_opt.total_net_interest)}</td>
      </tr>
      <tr>
        <td>Налог (13-15%)</td>
        <td class="num">−{fmt(dep_pess.total_tax)}</td>
        <td class="num">−{fmt(dep_base.total_tax)}</td>
        <td class="num">−{fmt(dep_opt.total_tax)}</td>
      </tr>
      <tr>
        <td>Итоговый капитал</td>
        <td class="num">{fmt(dep_pess.final_balance)}</td>
        <td class="num">{fmt(dep_base.final_balance)}</td>
        <td class="num">{fmt(dep_opt.final_balance)}</td>
      </tr>
      <tr>
        <td>ROI</td>
        <td class="num">{fmt_pct(dep_pess.total_roi_pct)}</td>
        <td class="num">{fmt_pct(dep_base.total_roi_pct)}</td>
        <td class="num">{fmt_pct(dep_opt.total_roi_pct)}</td>
      </tr>
    </table>

    <div class="section-title" style="margin-top: 25px;">Итоговое сравнение (11 лет)</div>

    <table class="data-table">
      <tr>
        <th>Показатель</th>
        <th style="text-align:right">Депозит (базовый)</th>
        <th style="text-align:right">RIZALTA</th>
        <th style="text-align:right">Разница</th>
      </tr>
      <tr>
        <td>Вложено</td>
        <td class="num">{fmt(price)}</td>
        <td class="num">{fmt(price)}</td>
        <td class="num">—</td>
      </tr>
      <tr>
        <td>Доход</td>
        <td class="num">{fmt(dep_base.total_net_interest)}</td>
        <td class="num">{fmt(rizalta.total_profit)}</td>
        <td class="num" style="color: #4a7c23; font-weight: 600;">+{fmt(advantage)}</td>
      </tr>
      <tr>
        <td>Итоговый капитал</td>
        <td class="num">{fmt(dep_base.final_balance)}</td>
        <td class="num">{fmt(riz_total_capital)}</td>
        <td class="num" style="color: #4a7c23; font-weight: 600;">+{fmt(riz_total_capital - dep_base.final_balance)}</td>
      </tr>
      <tr>
        <td>ROI</td>
        <td class="num">{fmt_pct(dep_base.total_roi_pct)}</td>
        <td class="num">{fmt_pct(rizalta.total_roi_pct)}</td>
        <td class="num" style="color: #4a7c23; font-weight: 600;">+{fmt_pct(rizalta.total_roi_pct - dep_base.total_roi_pct)}</td>
      </tr>
    </table>

    <div class="gold-box">
      <div class="gold-box-title">ПРЕИМУЩЕСТВО RIZALTA</div>
      <div class="gold-box-value">+{fmt(advantage)}</div>
      <div class="gold-box-sub">+{fmt_pct(advantage_pct)} к капиталу за 11 лет</div>
    </div>

    <div class="disclaimer">Депозит: прогноз ЦБ (ключевая 16.5% → 7%). Источник: cbr.ru</div>
  </div>

  <div class="footer"><div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div></div>
</div>
"""

    # ── PAGE 4: Payment Options ──
    price_95 = int(price * 0.95)
    html += f"""
<div class="page page-break">
  <div class="content" style="padding-top: 35px;">
    <div class="section-title">Варианты оплаты</div>

    <div class="green-box">
      <div style="font-size: 11px; letter-spacing: 2px; opacity: 0.9;">ПРИ 100% ОПЛАТЕ</div>
      <div class="green-box-value">{fmt(price_95)}</div>
      <div style="font-size: 12px; margin-top: 3px; opacity: 0.8;">Скидка 5% — экономия {fmt(price - price_95)}</div>
    </div>

    <div style="font-size: 15px; font-weight: 500; margin: 20px 0 12px;">Рассрочка 0% на 12 месяцев</div>
    <table class="options-table"><tr>
      <td class="option-card">
        <div class="option-pv">Первый взнос 30%</div>
        <div class="option-amount">{fmt(i12['pv_30'])}</div>
        <div class="option-monthly">Ежемесячно:<br>{fmt(i12['monthly_30'])}</div>
      </td>
      <td class="option-card option-card-mid">
        <div class="option-pv">Первый взнос 40%</div>
        <div class="option-amount">{fmt(i12['pv_40'])}</div>
        <div class="option-monthly">11 платежей × 200 000 ₽<br>12-й: {fmt(i12['last_40'])}</div>
      </td>
      <td class="option-card">
        <div class="option-pv">Первый взнос 50%</div>
        <div class="option-amount">{fmt(i12['pv_50'])}</div>
        <div class="option-monthly">11 платежей × 100 000 ₽<br>12-й: {fmt(i12['last_50'])}</div>
      </td>
    </tr></table>

    <div style="font-size: 15px; font-weight: 500; margin: 20px 0 12px;">Рассрочка на 18 месяцев</div>
    <table class="options-table"><tr>
      <td class="option-card-18">
        <div class="option-pv">Первый взнос 30% <span class="option-badge">+9%</span></div>
        <div class="option-amount">{fmt(i18['pv_30'])}</div>
        <div class="option-monthly">18 платежей × {fmt(i18['monthly_30'])}</div>
        <div class="option-total">Удорожание: +{fmt(i18['markup_30'])}<div class="option-total-sum">Итого: {fmt(i18['final_price_30'])}</div></div>
      </td>
      <td class="option-card-18 option-card-18-mid">
        <div class="option-pv">Первый взнос 40% <span class="option-badge">+7%</span></div>
        <div class="option-amount">{fmt(i18['pv_40'])}</div>
        <div class="option-monthly">8 × 250 000 ₽ + {fmt(i18['payment_9'])}<br>8 × 250 000 ₽ + {fmt(i18['last_40'])}</div>
        <div class="option-total">Удорожание: +{fmt(i18['markup_40'])}<div class="option-total-sum">Итого: {fmt(i18['final_price_40'])}</div></div>
      </td>
      <td class="option-card-18">
        <div class="option-pv">Первый взнос 50% <span class="option-badge">+4%</span></div>
        <div class="option-amount">{fmt(i18['pv_50'])}</div>
        <div class="option-monthly">8 × 150 000 ₽ + {fmt(i18['payment_9'])}<br>8 × 150 000 ₽ + {fmt(i18['last_50'])}</div>
        <div class="option-total">Удорожание: +{fmt(i18['markup_50'])}<div class="option-total-sum">Итого: {fmt(i18['final_price_50'])}</div></div>
      </td>
    </tr></table>

    <div class="disclaimer">Сервисный сбор 150 000 ₽ включён в стоимость. Рассрочка от застройщика, без банка.</div>
  </div>

  <div class="footer"><div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div></div>
</div>

</body></html>"""

    return html


# ─── Portfolio report (4 pages) ──────────────────────────────────────────────

def _generate_portfolio_report(data: dict) -> str | None:
    results = data.get("results", {})
    lots = _extract_search_lots(results)
    user_query = _escape_html(data.get("user_query", ""))
    date_str = datetime.now().strftime("%d.%m.%Y")
    logo_b64 = load_resource("logo_mono_trim_base64.txt")

    if not lots:
        logger.warning("[STRATEGY PDF] No lots found in search results")
        return None

    # Determine budget: from lots max price or from user_query context
    budget = max(lot.get("price_rub", 0) for lot in lots)

    # Calculate ROI for each lot (up to 8)
    lot_rois = []
    for lot in lots[:8]:
        area = lot.get("area_m2", 26.8)
        price = lot.get("price_rub", 0)
        if price <= 0:
            continue
        roi = calculate_roi(area, price)
        lot_rois.append({**lot, "roi": roi})

    # Sort by ROI descending
    lot_rois.sort(key=lambda x: x["roi"]["roi_pct"], reverse=True)

    # Deposit comparison on budget
    deposit_scenarios = calculate_all_scenarios(budget, 11)
    dep_base = deposit_scenarios["base"]

    # Average lot for RIZALTA comparison
    avg_price = int(sum(lr.get("price_rub", 0) for lr in lot_rois) / len(lot_rois)) if lot_rois else budget
    avg_area = sum(lr.get("area_m2", 26.8) for lr in lot_rois) / len(lot_rois) if lot_rois else 26.8
    rizalta = calculate_rizalta(avg_price, 11, avg_area)
    advantage = rizalta.total_profit - dep_base.total_net_interest
    advantage_pct = (advantage / budget * 100) if budget > 0 else 0

    css = _get_base_css()

    # ── PAGE 1: Title ──
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>{css}</style></head><body>

<div class="page">
  <table class="header-table"><tr><td>
    {"<img class='logo-header' src='data:image/png;base64," + logo_b64 + "'>" if logo_b64 else ""}
  </td></tr></table>

  <div class="title-bar">
    <div class="title-left">Инвестиционная стратегия</div>
    <div class="title-right">{date_str} &bull; AI Financial Advisor</div>
    <div style="clear:both"></div>
  </div>

  <div class="content">
    <div class="gold-box" style="margin-top: 40px;">
      <div class="gold-box-title">БЮДЖЕТ ИНВЕСТОРА</div>
      <div class="gold-box-value">{fmt(budget)}</div>
    </div>

    {f'<div style="margin-top: 30px; font-style: italic; color: rgba(49,61,32,0.6); font-size: 12px; border-left: 3px solid #DCB764; padding-left: 14px; line-height: 1.6;">Запрос: &laquo;{user_query}&raquo;</div>' if user_query else ''}

    <div style="margin-top: 40px;">
      <table class="data-table">
        <tr>
          <th style="text-align: center;">Лотов подобрано</th>
          <th style="text-align: center;">Лучший ROI</th>
          <th style="text-align: center;">Диапазон цен</th>
        </tr>
        <tr>
          <td style="text-align: center; font-size: 20px; font-weight: 600; padding: 18px;">{len(lot_rois)}</td>
          <td style="text-align: center; font-size: 20px; font-weight: 600; padding: 18px; color: #4a7c23;">{fmt_pct(lot_rois[0]['roi']['roi_pct']) if lot_rois else '—'}</td>
          <td style="text-align: center; font-size: 14px; font-weight: 500; padding: 18px;">{fmt(min(lr['price_rub'] for lr in lot_rois))} — {fmt(max(lr['price_rub'] for lr in lot_rois))}</td>
        </tr>
      </table>
    </div>

    <div class="disclaimer">Расчёты носят прогнозный характер и не являются публичной офертой.</div>
  </div>

  <div class="footer"><div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div></div>
</div>
"""

    # ── PAGE 2: Lots Table ──
    lots_rows = ""
    for lr in lot_rois:
        bname = get_building_name(lr.get("building_num", 1)) if isinstance(lr.get("building_num"), int) else lr.get("building", "—")
        lots_rows += f"""<tr>
  <td style="font-weight: 600;">{lr.get('code', '')}</td>
  <td>{bname}</td>
  <td class="num">{lr.get('floor', '—')}</td>
  <td class="num">{lr.get('area_m2', '')} м²</td>
  <td class="num">{fmt(lr.get('price_rub', 0))}</td>
  <td class="num">{fmt(int(lr.get('price_rub', 0) / lr.get('area_m2', 1)))}</td>
  <td class="num" style="color: #4a7c23; font-weight: 600;">{fmt_pct(lr['roi']['roi_pct'])}</td>
</tr>
"""

    html += f"""
<div class="page page-break">
  <div class="content" style="padding-top: 35px;">
    <div class="section-title">Подобранные апартаменты</div>

    <table class="data-table">
      <tr>
        <th>Код</th>
        <th>Корпус</th>
        <th style="text-align:right">Этаж</th>
        <th style="text-align:right">Площадь</th>
        <th style="text-align:right">Цена</th>
        <th style="text-align:right">Цена/м²</th>
        <th style="text-align:right">ROI (11 лет)</th>
      </tr>
      {lots_rows}
    </table>
"""

    # Top-3 details
    if lot_rois:
        html += '<div class="section-title" style="margin-top: 25px;">Топ по доходности</div>'
        for i, lr in enumerate(lot_rois[:3]):
            roi = lr["roi"]
            html += f"""
    <div style="background: white; padding: 12px 16px; margin-bottom: 8px; {'border-left: 4px solid #DCB764;' if i == 0 else 'border-left: 4px solid rgba(49,61,32,0.2);'}">
      <div style="font-weight: 600; font-size: 14px;">{lr.get('code', '')} — {fmt(lr.get('price_rub', 0))}</div>
      <div style="font-size: 11px; margin-top: 4px; color: rgba(49,61,32,0.7);">
        ROI {fmt_pct(roi['roi_pct'])} &bull; Аренда {fmt(roi['total_rental'])}/11 лет &bull; Актив к 2035: {fmt(roi['final_value'])}
      </div>
    </div>"""

    html += """
    <div class="disclaimer">ROI включает рост стоимости и арендный доход за 11 лет (2025-2035).</div>
  </div>

  <div class="footer"><div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div></div>
</div>
"""

    # ── PAGE 3: Comparative Analysis ──
    if len(lot_rois) >= 2:
        best_roi = lot_rois[0]
        cheapest = min(lot_rois, key=lambda x: x.get("price_rub", float("inf")))

        html += f"""
<div class="page page-break">
  <div class="content" style="padding-top: 35px;">
    <div class="section-title">Сравнительный анализ</div>

    <table class="data-table">
      <tr>
        <th>Показатель</th>
        <th style="text-align:right">Лучший по ROI ({best_roi.get('code', '')})</th>
        <th style="text-align:right">Лучший по цене ({cheapest.get('code', '')})</th>
      </tr>
      <tr>
        <td>Цена</td>
        <td class="num">{fmt(best_roi.get('price_rub', 0))}</td>
        <td class="num">{fmt(cheapest.get('price_rub', 0))}</td>
      </tr>
      <tr>
        <td>Площадь</td>
        <td class="num">{best_roi.get('area_m2', '')} м²</td>
        <td class="num">{cheapest.get('area_m2', '')} м²</td>
      </tr>
      <tr>
        <td>ROI (11 лет)</td>
        <td class="num" style="color: #4a7c23;">{fmt_pct(best_roi['roi']['roi_pct'])}</td>
        <td class="num">{fmt_pct(cheapest['roi']['roi_pct'])}</td>
      </tr>
      <tr>
        <td>Аренда (11 лет)</td>
        <td class="num">{fmt(best_roi['roi']['total_rental'])}</td>
        <td class="num">{fmt(cheapest['roi']['total_rental'])}</td>
      </tr>
      <tr>
        <td>Общий доход</td>
        <td class="num">{fmt(best_roi['roi']['total_profit'])}</td>
        <td class="num">{fmt(cheapest['roi']['total_profit'])}</td>
      </tr>
      <tr>
        <td>Стоимость к 2035</td>
        <td class="num">{fmt(best_roi['roi']['final_value'])}</td>
        <td class="num">{fmt(cheapest['roi']['final_value'])}</td>
      </tr>
      <tr>
        <td>При 100% оплате (−5%)</td>
        <td class="num">{fmt(int(best_roi.get('price_rub', 0) * 0.95))}</td>
        <td class="num">{fmt(int(cheapest.get('price_rub', 0) * 0.95))}</td>
      </tr>
      <tr>
        <td>ПВ 30% (рассрочка)</td>
        <td class="num">{fmt(int(best_roi.get('price_rub', 0) * 0.3))}</td>
        <td class="num">{fmt(int(cheapest.get('price_rub', 0) * 0.3))}</td>
      </tr>
    </table>
"""
    else:
        # Only 1 lot — simplified page
        lr = lot_rois[0] if lot_rois else None
        html += f"""
<div class="page page-break">
  <div class="content" style="padding-top: 35px;">
    <div class="section-title">Анализ</div>
"""
        if lr:
            html += f"""
    <div class="gold-box">
      <div class="gold-box-title">РЕКОМЕНДАЦИЯ</div>
      <div class="gold-box-value">{lr.get('code', '')} — {fmt(lr.get('price_rub', 0))}</div>
      <div class="gold-box-sub">ROI {fmt_pct(lr['roi']['roi_pct'])} за 11 лет</div>
    </div>
"""

    # Deposit comparison on this page too
    dep_pess = deposit_scenarios["pessimistic"]
    dep_opt = deposit_scenarios["optimistic"]
    riz_total_capital = rizalta.final_value + rizalta.total_rental_profit

    html += f"""
    <div class="section-title" style="margin-top: 25px;">RIZALTA vs Банковский депозит</div>

    <table class="data-table">
      <tr>
        <th>Показатель</th>
        <th style="text-align:right">Депозит (базовый)</th>
        <th style="text-align:right">RIZALTA</th>
        <th style="text-align:right">Разница</th>
      </tr>
      <tr>
        <td>Вложено</td>
        <td class="num">{fmt(budget)}</td>
        <td class="num">{fmt(avg_price)}</td>
        <td class="num">—</td>
      </tr>
      <tr>
        <td>Доход (11 лет)</td>
        <td class="num">{fmt(dep_base.total_net_interest)}</td>
        <td class="num">{fmt(rizalta.total_profit)}</td>
        <td class="num" style="color: #4a7c23; font-weight: 600;">+{fmt(advantage)}</td>
      </tr>
      <tr>
        <td>Итоговый капитал</td>
        <td class="num">{fmt(dep_base.final_balance)}</td>
        <td class="num">{fmt(riz_total_capital)}</td>
        <td class="num" style="color: #4a7c23; font-weight: 600;">+{fmt(riz_total_capital - dep_base.final_balance)}</td>
      </tr>
      <tr>
        <td>ROI</td>
        <td class="num">{fmt_pct(dep_base.total_roi_pct)}</td>
        <td class="num">{fmt_pct(rizalta.total_roi_pct)}</td>
        <td class="num" style="color: #4a7c23; font-weight: 600;">+{fmt_pct(rizalta.total_roi_pct - dep_base.total_roi_pct)}</td>
      </tr>
    </table>

    <div class="gold-box">
      <div class="gold-box-title">ПРЕИМУЩЕСТВО RIZALTA</div>
      <div class="gold-box-value">+{fmt(advantage)}</div>
      <div class="gold-box-sub">+{fmt_pct(advantage_pct)} к капиталу за 11 лет</div>
    </div>

    <div class="disclaimer">Депозит: прогноз ЦБ (ключевая 16.5% → 7%). Источник: cbr.ru</div>
  </div>

  <div class="footer"><div class="footer-text">R I Z A L T A &nbsp;&nbsp; R E S O R T &nbsp;&nbsp; B E L O K U R I K H A</div></div>
</div>

</body></html>"""

    return html


# ─── HTML to PDF ─────────────────────────────────────────────────────────────

def _html_to_pdf(html: str) -> str | None:
    try:
        html_file = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        )
        html_file.write(html)
        html_file.close()

        pdf_path = html_file.name.replace(".html", ".pdf")

        subprocess.run([
            "wkhtmltopdf",
            "--page-size", "A4",
            "--orientation", "Portrait",
            "--margin-top", "0",
            "--margin-bottom", "0",
            "--margin-left", "0",
            "--margin-right", "0",
            "--enable-local-file-access",
            "--disable-smart-shrinking",
            "--quiet",
            html_file.name,
            pdf_path,
        ], check=True, capture_output=True, timeout=60)

        os.unlink(html_file.name)
        return pdf_path
    except Exception as e:
        logger.error(f"[STRATEGY PDF] wkhtmltopdf error: {e}")
        return None
