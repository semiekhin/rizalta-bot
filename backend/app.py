from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import os

from services.calculator import calculate_roi
from services.installment_calculator import calc_full
from services.kp_pdf_generator import generate_kp_pdf
from services.calc_xlsx_generator import generate_roi_xlsx
from services.deposit_calculator import calculate_deposit, calculate_all_scenarios

app = FastAPI(title="RIZALTA Web App API", version="0.3.0")

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROD_API = "http://127.0.0.1:8000"  # Локально к PROD боту
DIST_PATH = "/opt/webapp/frontend/dist"


# === Модели ===

class ROIRequest(BaseModel):
    area: float
    price: int

class ShowingRequest(BaseModel):
    name: str
    phone: str
    lot_code: str = ""
    comment: str = ""

class InstallmentRequest(BaseModel):
    price: int

class KPRequest(BaseModel):
    code: str
    include_18m: bool = True
    full_payment: bool = False

class XLSXRequest(BaseModel):
    code: str

class DepositRequest(BaseModel):
    amount: int
    years: int = 11
    scenario: str = "base"  # base, optimistic, pessimistic


# === API endpoints ===

@app.get("/api/lots")
async def get_lots():
    """Проксируем к PROD боту."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{PROD_API}/api/lots")
            return response.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "0.3.0"}

@app.post("/api/calculate-roi")
async def api_calculate_roi(req: ROIRequest):
    """Расчёт ROI для лота."""
    try:
        result = calculate_roi(req.area, req.price)
        return {"ok": True, "data": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/book-showing")
async def api_book_showing(req: ShowingRequest):
    """Заявка на показ."""
    # TODO: отправка в Telegram/email
    print(f"[SHOWING] {req.name} / {req.phone} / {req.lot_code}")
    return {"ok": True, "message": "Заявка принята"}

@app.post("/api/installment")
async def api_installment(req: InstallmentRequest):
    """Расчёт вариантов рассрочки."""
    try:
        result = calc_full(req.price)
        return {"ok": True, "data": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/generate-kp")
async def api_generate_kp(req: KPRequest):
    """Генерация PDF коммерческого предложения."""
    try:
        pdf_path = generate_kp_pdf(
            code=req.code,
            include_18m=req.include_18m,
            full_payment=req.full_payment,
            output_dir="/tmp"
        )
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=os.path.basename(pdf_path)
            )
        return {"ok": False, "error": "Лот не найден или ошибка генерации"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/download-xlsx/{code}")
async def api_download_xlsx(code: str):
    """GET endpoint для скачивания Excel (для мобильных)."""
    try:
        xlsx_path = generate_roi_xlsx(unit_code=code, output_dir="/tmp")
        if xlsx_path and os.path.exists(xlsx_path):
            return FileResponse(
                xlsx_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=os.path.basename(xlsx_path)
            )
        return {"ok": False, "error": "Лот не найден"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/generate-xlsx")
async def api_generate_xlsx(req: XLSXRequest):
    """Генерация Excel с расчётом ROI."""
    try:
        xlsx_path = generate_roi_xlsx(
            unit_code=req.code,
            output_dir="/tmp"
        )
        if xlsx_path and os.path.exists(xlsx_path):
            return FileResponse(
                xlsx_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=os.path.basename(xlsx_path)
            )
        return {"ok": False, "error": "Лот не найден или ошибка генерации"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/compare-deposit")
async def api_compare_deposit(req: DepositRequest):
    """Сравнение с банковским депозитом."""
    try:
        if req.scenario == "all":
            results = calculate_all_scenarios(req.amount, req.years)
            data = {}
            for key, result in results.items():
                data[key] = {
                    "scenario_name": result.scenario_name,
                    "initial_amount": result.initial_amount,
                    "years": result.years,
                    "total_gross_interest": result.total_gross_interest,
                    "total_tax": result.total_tax,
                    "total_net_interest": result.total_net_interest,
                    "final_balance": result.final_balance,
                    "effective_rate": result.effective_rate,
                    "total_roi_pct": result.total_roi_pct,
                }
            return {"ok": True, "data": data}
        else:
            result = calculate_deposit(req.amount, req.years, req.scenario)
            return {"ok": True, "data": {
                "scenario_name": result.scenario_name,
                "initial_amount": result.initial_amount,
                "years": result.years,
                "total_gross_interest": result.total_gross_interest,
                "total_tax": result.total_tax,
                "total_net_interest": result.total_net_interest,
                "final_balance": result.final_balance,
                "effective_rate": result.effective_rate,
                "total_roi_pct": result.total_roi_pct,
                "yearly_results": [
                    {
                        "year": yr.year,
                        "deposit_rate": yr.deposit_rate,
                        "gross_interest": yr.gross_interest,
                        "tax_amount": yr.tax_amount,
                        "net_interest": yr.net_interest,
                        "end_balance": yr.end_balance,
                    }
                    for yr in result.yearly_results
                ]
            }}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Статика ===

app.mount("/assets", StaticFiles(directory=f"{DIST_PATH}/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = f"{DIST_PATH}/{full_path}"
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(f"{DIST_PATH}/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
