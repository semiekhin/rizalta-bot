from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import os

from services.calculator import calculate_roi

app = FastAPI(title="RIZALTA Web App API", version="0.2.0")

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
    return {"status": "healthy", "version": "0.2.0"}

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
