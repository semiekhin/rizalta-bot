"""Расчёт и генерация PDF для МГП (Минимальный Гарантированный Платёж)."""

import os
import subprocess
import tempfile
from config.settings import (
    MGP_TOTAL_AREA, MGP_YEARLY_AMOUNTS,
    MGP_COMM_YEARLY_AMOUNTS,
)

YEAR_NAMES = [
    "Первый", "Второй", "Третий", "Четвёртый", "Пятый",
    "Шестой", "Седьмой", "Восьмой", "Девятый", "Десятый",
    "Одиннадцатый", "Двенадцатый", "Тринадцатый", "Четырнадцатый", "Пятнадцатый",
]


def calc_mgp(area: float) -> list:
    """Рассчитывает МГП номерной + коммерческий. Возвращает список (год, mgp_nom, mgp_comm)."""
    result = []
    for i in range(15):
        mgp_nom = round(MGP_YEARLY_AMOUNTS[i] / MGP_TOTAL_AREA * area)
        mgp_comm = round(MGP_COMM_YEARLY_AMOUNTS[i] / 2 / MGP_TOTAL_AREA * area)
        result.append((i + 1, mgp_nom, mgp_comm))
    return result


def fmt(val: int) -> str:
    return f"{val:,}".replace(",", " ") if val > 0 else "0"


def format_mgp_text(code: str, area: float, building: int = None) -> str:
    """Форматирует МГП как текстовое сообщение."""
    rows = calc_mgp(area)
    total_nom = sum(r[1] for r in rows)
    total_comm = sum(r[2] for r in rows)

    bld = f"Корпус {building} — " if building else ""
    lines = [f"📊 <b>МГП — {bld}{code}</b>", f"Площадь: {area} м²", ""]
    lines.append("<b>Номерной фонд | Коммерч.</b>")
    lines.append("")
    for year_num, mgp_nom, mgp_comm in rows:
        name = YEAR_NAMES[year_num - 1]
        lines.append(f"▸ {name}: <b>{fmt(mgp_nom)} ₽</b> | {fmt(mgp_comm)} ₽")
    lines.append("")
    lines.append(f"💰 <b>ИТОГО 15 лет:</b>")
    lines.append(f"   Номерной: <b>{fmt(total_nom)} ₽</b>")
    lines.append(f"   Коммерч.: <b>{fmt(total_comm)} ₽</b>")

    return "\n".join(lines)


def generate_mgp_pdf(code: str, area: float, building: int = None) -> str:
    """Генерирует PDF с таблицей МГП. Возвращает путь к файлу."""
    rows = calc_mgp(area)
    total_nom = sum(r[1] for r in rows)
    total_comm = sum(r[2] for r in rows)

    bld = f"Корпус {building} — " if building else ""

    table_rows = ""
    for year_num, mgp_nom, mgp_comm in rows:
        name = YEAR_NAMES[year_num - 1]
        table_rows += f"<tr><td>{name}</td><td class='num'>{fmt(mgp_nom)} ₽</td><td class='num'>{fmt(mgp_comm)} ₽</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #1a1a1a; }}
    h1 {{ font-size: 20px; color: #1a3a5c; margin-bottom: 5px; }}
    h2 {{ font-size: 14px; color: #555; font-weight: normal; margin-top: 0; }}
    table {{ width: 75%; border-collapse: collapse; margin-top: 20px; }}
    th {{ background: #1a3a5c; color: white; padding: 10px 14px; text-align: left; font-size: 13px; }}
    th.num {{ text-align: right; }}
    td {{ padding: 8px 14px; border-bottom: 1px solid #ddd; font-size: 13px; }}
    td.num {{ text-align: right; font-family: monospace; }}
    tr:nth-child(even) {{ background: #f5f7fa; }}
    .total td {{ font-weight: bold; border-top: 2px solid #1a3a5c; background: #e8edf2; }}
    .footer {{ margin-top: 30px; font-size: 11px; color: #888; }}
</style></head><body>
    <h1>📊 Минимальный гарантированный платёж</h1>
    <h2>{bld}{code} | Площадь: {area} м²</h2>
    <table>
        <tr><th>Период</th><th class="num">Номерной фонд, ₽/год</th><th class="num">Коммерч. использование, ₽/год</th></tr>
        {table_rows}
        <tr class="total"><td>ИТОГО за 15 лет</td><td class="num">{fmt(total_nom)} ₽</td><td class="num">{fmt(total_comm)} ₽</td></tr>
    </table>
</body></html>"""

    tmp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    tmp_html.write(html.encode())
    tmp_html.close()

    pdf_path = tmp_html.name.replace(".html", ".pdf")
    subprocess.run([
        "wkhtmltopdf", "--quiet",
        "--page-size", "A4",
        "--margin-top", "10mm",
        "--margin-bottom", "10mm",
        tmp_html.name, pdf_path
    ], check=True)

    os.unlink(tmp_html.name)
    return pdf_path
