#!/usr/bin/env python3
"""
Генератор Excel-файла с расчётом прибыли от апартамента RIZALTA
На основе формул застройщика
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
import tempfile

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "properties.db"


def get_lot_from_db(code: str) -> Optional[Dict]:
    """Получить лот из БД по коду"""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    code_upper = code.strip().upper()
    table = str.maketrans({"А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "S", "Т": "T"})
    code_latin = code_upper.translate(table)
    cursor.execute("SELECT code, area_m2, price_rub FROM units WHERE code = ? OR code = ? LIMIT 1", (code_upper, code_latin))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"code": row[0], "area": row[1], "price": row[2], "price_m2": int(row[2] / row[1])}
    return None


def get_lot_by_area(area: float) -> Optional[Dict]:
    """Получить лот из БД по площади"""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT code, area_m2, price_rub FROM units WHERE area_m2 = ? LIMIT 1", (area,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"code": row[0], "area": row[1], "price": row[2], "price_m2": int(row[2] / row[1])}
    return None


class ProfitCalculatorGenerator:
    """Генератор Excel-файла с расчётом прибыли"""
    
    # Базовые ставки аренды / эталонная площадь 26.8 м²
    RENT_PRICES_PER_M2 = [664.18, 723.88, 787.31, 858.21, 932.84, 1014.93, 1104.48, 1201.49]
    
    # Загрузка отеля по годам, %
    OCCUPANCY = [40, 60, 70, 70, 70, 70, 70, 70]
    
    # Дней в году (2028-2035)
    DAYS_PER_YEAR = [366, 365, 365, 365, 366, 365, 365, 365]
    
    def __init__(self, area: float, price_m2: float, expense_rate: float = 0.5, growth_rate: float = 0.2):
        self.area = area
        self.price_m2 = price_m2
        self.expense_rate = expense_rate
        self.growth_rate = growth_rate
        self._setup_styles()
    
    def _setup_styles(self):
        """Настройка стилей"""
        thin = Side(style='thin')
        self.border_thin = Border(left=thin, right=thin, top=thin, bottom=thin)
        self.font_red_bold = Font(bold=True, color="FF0000")
        self.font_blue = Font(color="0070C0")
        self.font_bold = Font(bold=True)
        self.align_center_wrap = Alignment(horizontal='center', vertical='center', wrap_text=True)
        self.align_center = Alignment(horizontal='center', vertical='center')
    
    def generate(self, output_path: Optional[str] = None) -> str:
        """Генерирует Excel-файл"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Расчет прибыли"
        
        self._set_dimensions(ws)
        self._create_header(ws)
        self._create_params_section(ws)
        self._create_table_header(ws)
        self._create_pre_rent_years(ws)
        self._create_rent_years(ws)
        self._create_totals(ws)
        
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.xlsx', prefix='profit_calc_')
        
        wb.save(output_path)
        return output_path
    
    def _set_dimensions(self, ws):
        """Устанавливает размеры колонок и строк"""
        col_widths = {
            'A': 8.66, 'B': 16, 'C': 18, 'D': 13, 'E': 21, 
            'F': 18, 'G': 18, 'H': 22, 'I': 20, 'J': 20, 'K': 15.55, 
            'L': 16.5, 'M': 16.5, 'N': 17.5
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width
        
        row_heights = {
            1: 21, 2: 21, 3: 25, 4: 21, 5: 80, 6: 21, 
            7: 21, 8: 21, 9: 17, 10: 80, 11: 29, 12: 29, 
            13: 29, 14: 29, 15: 29, 16: 29, 17: 29, 18: 29, 
            19: 29, 20: 29, 21: 29, 22: 24
        }
        for row, height in row_heights.items():
            ws.row_dimensions[row].height = height
    
    def _create_header(self, ws):
        """Создаёт заголовок"""
        ws['C3'] = 'Расчет прибыли'
        ws['C3'].font = Font(bold=True, size=14)
    
    def _create_params_section(self, ws):
        """Создаёт секцию с параметрами (строки 5-6)"""
        headers = {
            'B': 'Площадь, м2',
            'C': 'Цена за м2',
            'D': 'Стоимость, руб',
            'F': 'Расходы, %',
            'G': 'Прибыль от роста стоимости кв.м. апартамента в год, %',
            'H': 'Срок окупаемости апартамента, лет',
            'I': 'Срок окупаемости апартамента (от сдачи), лет'
        }
        
        for col, val in headers.items():
            cell = ws[f'{col}5']
            cell.value = val
            cell.font = self.font_bold
            cell.alignment = self.align_center_wrap
            cell.border = self.border_thin
        
        ws.merge_cells('D5:E5')
        ws.merge_cells('D6:E6')
        
        # Входные данные
        ws['B6'] = self.area
        ws['B6'].border = self.border_thin
        ws['B6'].alignment = self.align_center
        
        ws['C6'] = self.price_m2
        ws['C6'].border = self.border_thin
        ws['C6'].alignment = self.align_center
        ws['C6'].number_format = '#,##0'
        
        ws['D6'] = '=B6*C6'
        ws['D6'].border = self.border_thin
        ws['D6'].alignment = self.align_center
        ws['D6'].number_format = '#,##0'
        
        ws['E6'].border = self.border_thin
        
        ws['F6'] = self.expense_rate
        ws['F6'].border = self.border_thin
        ws['F6'].alignment = self.align_center
        ws['F6'].number_format = '0%'
        
        ws['G6'] = self.growth_rate
        ws['G6'].font = self.font_red_bold
        ws['G6'].border = self.border_thin
        ws['G6'].alignment = self.align_center
        ws['G6'].number_format = '0%'
        
        ws['H6'] = '=ROUND(D6/(I22/11),2)'
        ws['H6'].font = self.font_red_bold
        ws['H6'].border = self.border_thin
        ws['H6'].alignment = self.align_center
        ws['H6'].number_format = '0.00'
        
        ws['I6'] = '=ROUND(D6/(SUM(G11:G21)/9),2)'
        ws['I6'].font = self.font_red_bold
        ws['I6'].border = self.border_thin
        ws['I6'].alignment = self.align_center
        ws['I6'].number_format = '0.00'
    
    def _create_table_header(self, ws):
        """Создаёт заголовок основной таблицы (строка 10)"""
        headers = {
            'B': 'Год',
            'C': 'Стоимость сдачи номера в сутки, руб',
            'D': 'Загрузка отеля,%',
            'E': 'Стоимость сдачи номера в год, руб',
            'F': 'Расходы, руб',
            'G': 'Прибыль от сдачи апартамента, руб',
            'H': 'Накопительная прибыль от сдачи апартамента, руб',
            'I': 'Прибыль от роста стоимости кв.м. апартамента, руб',
            'J': 'Прибыль накопительно',
            'L': 'Прибыль от сдачи апартамента в год, %',
            'M': 'Прибыль роста цены от стоимости апартамента в год, %',
            'N': 'Общая прибыль от стоимости апартамента в год, %'
        }
        
        for col, val in headers.items():
            cell = ws[f'{col}10']
            cell.value = val
            cell.font = self.font_bold
            cell.alignment = self.align_center_wrap
            cell.border = self.border_thin
    
    def _create_pre_rent_years(self, ws):
        """Создаёт строки 11-13 (годы без аренды)"""
        for i, year in enumerate([2025, 2026, 2027]):
            row = 11 + i
            ws[f'B{row}'] = year
            ws[f'B{row}'].border = self.border_thin
            ws[f'B{row}'].alignment = self.align_center
            
            for col in ['C', 'D', 'E', 'F', 'G', 'H']:
                ws[f'{col}{row}'].border = self.border_thin
        
        # Формулы для роста стоимости
        formulas = [
            {'I': '=ROUND(D6*18%,0)', 'J': '=ROUND(I11,0)', 
             'M': '=ROUND(I11*100/D6,2)', 'N': '=ROUND(M11+L11,2)'},
            {'I': '=ROUND((D6+I11)*G6,0)', 'J': '=ROUND(J11+I12,0)', 
             'M': '=ROUND(I12*100/D6,2)', 'N': '=ROUND(M12+L12,2)'},
            {'I': '=ROUND((D6+I11+I12)*G6,0)', 'J': '=ROUND(J12+I13,0)', 
             'M': '=ROUND(I13*100/D6,2)', 'N': '=ROUND(M13+L13,2)'},
        ]
        
        for i, row in enumerate([11, 12, 13]):
            for col, formula in formulas[i].items():
                ws[f'{col}{row}'] = formula
                ws[f'{col}{row}'].border = self.border_thin
                ws[f'{col}{row}'].alignment = self.align_center
                if col in ['I', 'J']:
                    ws[f'{col}{row}'].number_format = '#,##0'
                else:
                    ws[f'{col}{row}'].number_format = '0.00'
            
            for col in ['L']:
                ws[f'{col}{row}'].border = self.border_thin
                ws[f'{col}{row}'].alignment = self.align_center
                ws[f'{col}{row}'].number_format = '0.00'
    
    def _create_rent_years(self, ws):
        """Создаёт строки 14-21 (годы с арендой)"""
        years = [2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035]
        
        i_formulas = [
            '=ROUND((D6+I11+I12+I13)*G6/2,0)',
            '=ROUND((D6+I11+I12+I13+I14)*0.088,0)',
            '=ROUND((D6+I11+I12+I13+I14+I15)*0.088,0)',
            '=ROUND((D6+I11+I12+I13+I14+I15+I16)*0.088,0)',
            '=ROUND((D6+I11+I12+I13+I14+I15+I16+I17)*0.088,0)',
            '=ROUND((D6+I11+I12+I13+I14+I15+I16+I17+I18)*0.088,0)',
            '=ROUND((D6+I11+I12+I13+I14+I15+I16+I17+I18+I19)*0.088,0)',
            '=ROUND((D6+I11+I12+I13+I14+I15+I16+I17+I18+I19+I20)*0.088,0)'
        ]
        
        for i, year in enumerate(years):
            row = 14 + i
            d = self.DAYS_PER_YEAR[i]
            
            # Год
            ws[f'B{row}'] = year
            ws[f'B{row}'].font = self.font_blue
            ws[f'B{row}'].border = self.border_thin
            ws[f'B{row}'].alignment = self.align_center
            
            # Цена в сутки за весь номер (ставка м² × площадь)
            ws[f'C{row}'] = f'=ROUND({self.RENT_PRICES_PER_M2[i]}*$B$6,0)'
            ws[f'C{row}'].border = self.border_thin
            ws[f'C{row}'].alignment = self.align_center
            ws[f'C{row}'].number_format = '#,##0'
            
            # Загрузка
            ws[f'D{row}'] = self.OCCUPANCY[i]
            ws[f'D{row}'].border = self.border_thin
            ws[f'D{row}'].alignment = self.align_center
            
            # Доход за год = дней * (ставка_м2 * площадь) * загрузка / 100
            ws[f'E{row}'] = f'=ROUND({d}*C{row}*D{row}/100,0)'
            ws[f'E{row}'].border = self.border_thin
            ws[f'E{row}'].alignment = self.align_center
            ws[f'E{row}'].number_format = '#,##0'
            
            # Расходы
            ws[f'F{row}'] = f'=ROUND(E{row}*$F$6,0)'
            ws[f'F{row}'].border = self.border_thin
            ws[f'F{row}'].alignment = self.align_center
            ws[f'F{row}'].number_format = '#,##0'
            
            # Прибыль от сдачи
            ws[f'G{row}'] = f'=ROUND(E{row}-F{row},0)'
            ws[f'G{row}'].border = self.border_thin
            ws[f'G{row}'].alignment = self.align_center
            ws[f'G{row}'].number_format = '#,##0'
            
            # Накопительная прибыль от сдачи (новый столбец H)
            if row == 14:
                ws[f'H{row}'] = f'=ROUND(G{row},0)'
            else:
                ws[f'H{row}'] = f'=ROUND(H{row-1}+G{row},0)'
            ws[f'H{row}'].border = self.border_thin
            ws[f'H{row}'].alignment = self.align_center
            ws[f'H{row}'].number_format = '#,##0'
            
            # Прибыль от роста стоимости (теперь столбец I)
            ws[f'I{row}'] = i_formulas[i]
            ws[f'I{row}'].border = self.border_thin
            ws[f'I{row}'].alignment = self.align_center
            ws[f'I{row}'].number_format = '#,##0'
            
            # Прибыль накопительно (теперь столбец J)
            prev = 13 if row == 14 else row - 1
            ws[f'J{row}'] = f'=ROUND(G{row}+J{prev}+I{row},0)'
            ws[f'J{row}'].border = self.border_thin
            ws[f'J{row}'].alignment = self.align_center
            ws[f'J{row}'].number_format = '#,##0'
            
            # Проценты (теперь L, M, N)
            for col, formula in [
                ('L', f'=ROUND(G{row}*100/$D$6,2)'),
                ('M', f'=ROUND(I{row}*100/$D$6,2)'),
                ('N', f'=ROUND(M{row}+L{row},2)')
            ]:
                ws[f'{col}{row}'] = formula
                ws[f'{col}{row}'].border = self.border_thin
                ws[f'{col}{row}'].alignment = self.align_center
                ws[f'{col}{row}'].number_format = '0.00'
    
    def _create_totals(self, ws):
        """Создаёт строку итогов (строка 22)"""
        ws['B22'] = 'Итого'
        ws['B22'].font = self.font_bold
        ws['B22'].border = self.border_thin
        ws['B22'].alignment = self.align_center
        
        totals = {
            'E': ('=ROUND(SUM(E14:E21),0)', '0'),
            'F': ('=ROUND(SUM(F14:F21),0)', '0'),
            'G': ('=ROUND(SUM(G14:G21),0)', '0'),
            'H': ('=ROUND(H21,0)', '0'),
            'I': ('=ROUND(SUM(I11:I21),0)', '0'),
            'J': ('=ROUND(J21,0)', '0'),
            'N': ('=ROUND(SUM(N11:N21)/11,2)', '0.00'),
        }
        
        for col, (formula, fmt) in totals.items():
            ws[f'{col}22'] = formula
            ws[f'{col}22'].border = self.border_thin
            ws[f'{col}22'].alignment = self.align_center
            ws[f'{col}22'].number_format = fmt
        
        # Пустые ячейки с границами
        for col in ['C', 'D', 'L', 'M']:
            ws[f'{col}22'].border = self.border_thin


def generate_roi_xlsx(unit_code: str = None, area: float = None, output_dir: str = None) -> Optional[str]:
    """
    Генерирует Excel-файл с расчётом прибыли
    """
    lot = None
    if unit_code:
        lot = get_lot_from_db(unit_code)
    elif area:
        lot = get_lot_by_area(area)
    
    if not lot:
        print(f"[XLSX] Лот не найден: code={unit_code}, area={area}")
        return None
    
    generator = ProfitCalculatorGenerator(
        area=lot['area'],
        price_m2=lot['price_m2'],
        expense_rate=0.5,
        growth_rate=0.2
    )
    
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    
    output_path = Path(output_dir) / f"ROI_{lot['code']}.xlsx"
    
    try:
        generator.generate(str(output_path))
        print(f"[XLSX] ✅ Создан: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"[XLSX] Ошибка: {e}")
        return None


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "В200"
    generate_roi_xlsx(unit_code=code, output_dir="/tmp")
