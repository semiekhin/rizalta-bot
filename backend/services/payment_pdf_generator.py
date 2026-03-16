"""Payment options PDF generator — installment plans for RIZALTA lots."""

import os
import subprocess
import tempfile

from services.installment_calculator import calc_full


def _fmt(val: int) -> str:
    return f"{val:,}".replace(",", " ")


def generate_payment_pdf(price: int, code: str = "") -> str:
    """Generates PDF with installment options. Returns path to temp file."""
    data = calc_full(price)
    i12 = data["i12"]
    i18 = data["i18"]

    title_suffix = f" — Лот {code}" if code else ""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #1a1a1a; }}
    h1 {{ font-size: 20px; color: #1a3a5c; margin-bottom: 5px; }}
    h2 {{ font-size: 14px; color: #555; font-weight: normal; margin-top: 0; }}
    h3 {{ font-size: 15px; margin-top: 25px; margin-bottom: 8px; }}
    .green {{ color: #2e7d32; }}
    .gold {{ color: #b8860b; }}
    table {{ width: 80%; border-collapse: collapse; margin-top: 8px; }}
    th {{ background: #1a3a5c; color: white; padding: 8px 12px; text-align: left; font-size: 12px; }}
    td {{ padding: 7px 12px; border-bottom: 1px solid #ddd; font-size: 12px; }}
    td.val {{ text-align: right; font-family: monospace; }}
    tr:nth-child(even) {{ background: #f5f7fa; }}
    .price-block {{ background: #f0f4f8; padding: 12px 16px; border-radius: 8px; margin-bottom: 15px; }}
    .price-block .label {{ font-size: 12px; color: #666; }}
    .price-block .value {{ font-size: 20px; font-weight: bold; color: #1a3a5c; }}
    .footer {{ margin-top: 30px; font-size: 10px; color: #999; }}
</style></head><body>
    <h1>Варианты оплаты{title_suffix}</h1>
    <div class="price-block">
        <div class="label">Стоимость</div>
        <div class="value">{_fmt(price)} ₽</div>
    </div>

    <h3 class="green">12 месяцев (0%)</h3>
    <table>
        <tr><th>Первонач. взнос</th><th>Сумма ПВ</th><th>Ежемесячный платёж</th></tr>
        <tr><td>30%</td><td class="val">{_fmt(i12['pv_30'])} ₽</td><td class="val">{_fmt(i12['monthly_30'])} ₽/мес</td></tr>
        <tr><td>40%</td><td class="val">{_fmt(i12['pv_40'])} ₽</td><td class="val">11 × 200 000 ₽ + {_fmt(i12['last_40'])} ₽</td></tr>
        <tr><td>50%</td><td class="val">{_fmt(i12['pv_50'])} ₽</td><td class="val">11 × 100 000 ₽ + {_fmt(i12['last_50'])} ₽</td></tr>
    </table>

    <h3 class="gold">18 месяцев (с удорожанием)</h3>
    <table>
        <tr><th>Первонач. взнос</th><th>Сумма ПВ</th><th>Удорожание</th><th>Схема платежей</th></tr>
        <tr>
            <td>30% (+9%)</td>
            <td class="val">{_fmt(i18['pv_30'])} ₽</td>
            <td class="val">{_fmt(i18['markup_30'])} ₽</td>
            <td class="val">18 × {_fmt(i18['monthly_30'])} ₽</td>
        </tr>
        <tr>
            <td>40% (+7%)</td>
            <td class="val">{_fmt(i18['pv_40'])} ₽</td>
            <td class="val">{_fmt(i18['markup_40'])} ₽</td>
            <td class="val">8×250К, 9-й: {_fmt(i18['payment_9'])} ₽, 8×250К, 18-й: {_fmt(i18['last_40'])} ₽</td>
        </tr>
        <tr>
            <td>50% (+4%)</td>
            <td class="val">{_fmt(i18['pv_50'])} ₽</td>
            <td class="val">{_fmt(i18['markup_50'])} ₽</td>
            <td class="val">8×150К, 9-й: {_fmt(i18['payment_9'])} ₽, 8×150К, 18-й: {_fmt(i18['last_50'])} ₽</td>
        </tr>
    </table>

    <p class="footer">RIZALTA Resort Belokurikha • Расчёт предварительный</p>
</body></html>"""

    tmp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    tmp_html.write(html.encode())
    tmp_html.close()

    pdf_path = tmp_html.name.replace(".html", ".pdf")
    subprocess.run([
        "wkhtmltopdf", "--quiet",
        "--page-size", "A4",
        "--orientation", "Landscape",
        "--margin-top", "10mm",
        "--margin-bottom", "10mm",
        tmp_html.name, pdf_path
    ], check=True)

    os.unlink(tmp_html.name)
    return pdf_path
