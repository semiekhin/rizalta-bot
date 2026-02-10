from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import os

from services.calculator import calculate_roi
from services.installment_calculator import calc_full
from services.kp_pdf_generator import generate_kp_pdf
from services.calc_xlsx_generator import generate_roi_xlsx
from services.deposit_calculator import calculate_deposit, calculate_all_scenarios

app = FastAPI(title="RIZALTA Web App API", version="0.5.0")

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
    return {"status": "healthy", "version": "0.5.0"}

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


@app.get("/api/download-kp/{code}")
async def api_download_kp(code: str, type: str = "100"):
    """GET endpoint для скачивания PDF КП (для мобильных)."""
    try:
        pdf_path = generate_kp_pdf(
            code=code,
            include_18m=(type == "full"),
            full_payment=(type == "100"),
            output_dir="/tmp"
        )
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=os.path.basename(pdf_path)
            )
        return {"ok": False, "error": "Лот не найден"}
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


# === File serving (whitelist) ===

PRESENTATIONS_DIR = "/opt/bot-dev/presentations"
DOCUMENTS_DIR = "/opt/bot/docs"
VIDEOS_DIR = "/opt/bot-dev/videos"

ALLOWED_PRESENTATIONS = {
    "presentation_ru": "presentation_ru.pdf",
    "presentation_eng": "presentation_eng.pdf",
    "analytics_corexp": "analytics_corexp.pdf",
    "pergaev_bureau": "pergaev_bureau.pdf",
    "zont_hotel": "zont_hotel.pdf",
}

ALLOWED_DOCUMENTS = {
    "ddu": "ddu.pdf",
    "arenda": "arenda.pdf",
}

ALLOWED_VIDEOS = {
    "nerealno": "nerealno.mp4",
    "vesti_kurort": "vesti_kurort.mp4",
    "bolshoy_altai": "bolshoy_altai.mp4",
    "pravilo_30x30": "pravilo_30x30.mp4",
    "vesti_turpotok": "vesti_turpotok_fixed.mp4",
    "mihalkova": "mihalkova_altai.mp4",
}


@app.get("/api/files/presentations/{key}")
async def serve_presentation(key: str):
    """Отдаёт PDF презентацию из whitelist."""
    filename = ALLOWED_PRESENTATIONS.get(key)
    if not filename:
        raise HTTPException(status_code=404, detail="File not found")
    path = os.path.join(PRESENTATIONS_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@app.get("/api/files/documents/{key}")
async def serve_document(key: str):
    """Отдаёт PDF договор из whitelist."""
    filename = ALLOWED_DOCUMENTS.get(key)
    if not filename:
        raise HTTPException(status_code=404, detail="File not found")
    path = os.path.join(DOCUMENTS_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@app.get("/api/files/videos/{key}")
async def serve_video(key: str):
    """Отдаёт видео из whitelist (streaming)."""
    filename = ALLOWED_VIDEOS.get(key)
    if not filename:
        raise HTTPException(status_code=404, detail="File not found")
    path = os.path.join(VIDEOS_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    file_size = os.path.getsize(path)

    def iter_file():
        with open(path, "rb") as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type="video/mp4",
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        }
    )


# === Курсы валют ===

@app.get("/api/news/currency")
async def get_currency():
    """Курсы валют ЦБ РФ через cbr-xml-daily.ru."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("https://www.cbr-xml-daily.ru/daily_json.js")
            data = resp.json()
            result = []
            for code in ["USD", "EUR", "CNY"]:
                v = data["Valute"].get(code)
                if v:
                    result.append({
                        "code": code,
                        "name": v["Name"],
                        "value": round(v["Value"] / v["Nominal"], 2),
                        "change": round((v["Value"] - v["Previous"]) / v["Nominal"], 2),
                        "date": data.get("Date", "")[:10],
                    })
            return {"ok": True, "data": result}
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
