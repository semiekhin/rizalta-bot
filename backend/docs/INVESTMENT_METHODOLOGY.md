# RIZALTA Investment Methodology

## Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Stabilized year | 2030 | Year when occupancy reaches 70% |
| Rate per m2/day | 787.31 RUB | RATE_PER_M2[2030] |
| Occupancy | 70% | OCCUPANCY[2030] |
| Operating expenses | 50% of gross | EXPENSES_PCT |
| Full payment discount | 5% | Installment config |
| Installment down payment | 30% | Installment config |
| Projection period | 11 years (2025-2035) | ROI model |

## Metrics

### NOI (Net Operating Income)
Annual net income after operating expenses, stabilized year.

```
Gross Income = 365 days * 787.31 RUB/m2 * Area * 0.70
NOI = Gross Income * (1 - 0.50)
```

### Cap Rate (Capitalization Rate)
Ratio of NOI to property price. Industry-standard measure of property yield.

```
Cap Rate = NOI / Price * 100%
```

Benchmarks: 4-6% — conservative, 6-8% — balanced, 8%+ — aggressive.

### Cash-on-Cash Return
Annual return on actual cash invested.

**100% payment (5% discount):**
```
CoC = NOI / (Price * 0.95) * 100%
```

**Installment (30% down payment):**
```
CoC = NOI / (Price * 0.30) * 100%
```

### Equity Multiple
Total return on invested capital over the full projection period (11 years).

```
Equity Multiple = (Final Value + Total Rental Income) / Invested Capital
```

Where:
- Final Value = purchase price + cumulative capital growth (11 years)
- Total Rental Income = sum of net rental income 2028-2035
- Invested Capital = price * 0.95 (full) or price (installment)

Benchmarks: 1.5x — conservative, 2.0x — good, 2.5x+ — excellent.

### ROI (Return on Investment)
Total percentage return over 11 years, including both rental income and capital appreciation.

```
ROI = (Total Rental + Total Growth) / Price * 100%
Avg Annual = ROI / 11
```

## Capital Growth Model
Annual property value appreciation based on project stage:

| Year | Growth Rate | Rationale |
|------|------------|-----------|
| 2025 | 18% | Pre-construction premium |
| 2026 | 20% | Construction phase |
| 2027 | 20% | Near completion |
| 2028 | 10% | Launch year |
| 2029-2035 | 8.8% | Stabilized growth |

## Data Sources
- `backend/services/calculator.py` — all calculations
- `backend/data/rizalta_finance.json` — project financial parameters
- `backend/services/report_builder.py` — data assembly for reports
