"""
Инвестиционный калькулятор RIZALTA для webapp
"""

from typing import Dict, List

# Константы из бота
EXPENSES_PCT = 0.50

RATE_PER_M2 = {
    2028: 664.18, 2029: 723.88, 2030: 787.31, 2031: 858.21,
    2032: 932.84, 2033: 1014.93, 2034: 1104.48, 2035: 1201.49,
}

OCCUPANCY = {
    2028: 40, 2029: 60, 2030: 70, 2031: 70,
    2032: 70, 2033: 70, 2034: 70, 2035: 70,
}

DAYS_IN_YEAR = {
    2028: 366, 2029: 365, 2030: 365, 2031: 365,
    2032: 366, 2033: 365, 2034: 365, 2035: 365,
}


def calculate_roi(area: float, price: int) -> Dict:
    """Расчёт ROI для лота."""
    price_m2 = int(price / area) if area > 0 else 0
    D6 = price
    
    H_values: List[float] = []
    years_data = []
    cumulative_profit = 0
    
    for year in range(2025, 2036):
        sum_prev_H = sum(H_values)
        
        if year == 2025:
            H = D6 * 0.18
        elif year == 2026:
            H = (D6 + sum_prev_H) * 0.20
        elif year == 2027:
            H = (D6 + sum_prev_H) * 0.20
        elif year == 2028:
            H = (D6 + sum_prev_H) * 0.10
        else:
            H = (D6 + sum_prev_H) * 0.088
        
        H_values.append(H)
        
        G = 0
        if year >= 2028:
            rate_m2 = RATE_PER_M2.get(year, 0)
            occupancy = OCCUPANCY.get(year, 0)
            days = DAYS_IN_YEAR.get(year, 365)
            gross_income = days * rate_m2 * area * occupancy / 100
            G = gross_income * (1 - EXPENSES_PCT)
        
        cumulative_profit += G + H
        current_value = D6 + sum(H_values)
        
        years_data.append({
            "year": year,
            "rental_profit": int(G),
            "growth_profit": int(H),
            "cumulative_profit": int(cumulative_profit),
            "current_value": int(current_value),
        })
    
    total_rental = sum(y["rental_profit"] for y in years_data)
    total_growth = sum(y["growth_profit"] for y in years_data)
    total_profit = total_rental + total_growth
    final_value = D6 + sum(H_values)
    roi_pct = (total_profit / D6 * 100) if D6 > 0 else 0
    avg_annual_pct = roi_pct / 11
    
    return {
        "area": area,
        "price": price,
        "price_m2": price_m2,
        "total_rental": total_rental,
        "total_growth": total_growth,
        "total_profit": total_profit,
        "final_value": int(final_value),
        "roi_pct": round(roi_pct, 1),
        "avg_annual_pct": round(avg_annual_pct, 1),
        "years": years_data,
    }
