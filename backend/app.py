from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Response, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import sqlite3
import secrets
import json
from pathlib import Path
import time
import logging
from contextlib import asynccontextmanager
from collections import defaultdict

from services.calculator import calculate_roi
from services.installment_calculator import calc_full
from services.kp_pdf_generator import generate_kp_pdf
from services.calc_xlsx_generator import generate_roi_xlsx
from services.deposit_calculator import calculate_deposit, calculate_all_scenarios
from services.compare_pdf_generator import generate_compare_pdf
from services.notifications import notify_showing_request
from services.ai_chat import stream_chat_with_tools, stream_lot_report, stream_portfolio_report
from services.intent_router import quick_classify_navigation
from services import rag_service
from services.secretary_db import init_secretary_db, add_task, get_tasks_for_date, get_tasks_for_week, mark_done, mark_undone, move_task, delete_task
from services.secretary_ai import parse_task_with_ai
from services.rclick_service import init_rclick_table, rclick_auth, rclick_check_status, rclick_create_fixation, rclick_logout
from services.news_service import get_weather, get_flights, get_news_digest
from services.mgp_calculator import calc_mgp, generate_mgp_pdf, fmt as mgp_fmt
from services.mortgage_calculator import calc_mortgage, get_mortgage_options, generate_mortgage_pdf
from services.tranche_mortgage_calculator import calc_tranche_mortgage, calc_all_scenarios as calc_tranche_all, get_down_payment_options as get_tranche_dp_options
from services.payment_pdf_generator import generate_payment_pdf
from services.strategy_pdf_generator import generate_strategy_pdf

# === Whitelist DB ===
WEBAPP_DB = os.getenv("WEBAPP_DB", "./webapp.db")
# DEACTIVATED: Corp3 now in properties.db. Reuse for Corp4.
# CORP3_DATA_PATH = os.getenv("CORP3_DATA_PATH", "/opt/bot-dev/data/corp3_units.json")
# CORP3_LAYOUTS_DIR = os.getenv("CORP3_LAYOUTS_DIR", "/opt/bot-dev/data/corp3_layouts")


def init_webapp_db():
    """Creates webapp tables on startup."""
    conn = sqlite3.connect(WEBAPP_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS access_tokens (
            token TEXT PRIMARY KEY,
            name TEXT,
            level TEXT DEFAULT 'white',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def seed_token():
    """Creates a token if DB is empty."""
    conn = sqlite3.connect(WEBAPP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM access_tokens")
    if cursor.fetchone()[0] == 0:
        token = secrets.token_urlsafe(16)
        cursor.execute(
            "INSERT INTO access_tokens (token, name, level) VALUES (?, ?, ?)",
            (token, "Общий белый список", "white")
        )
        conn.commit()
        print(f"[WEBAPP] Created whitelist token: {token}")
    conn.close()


def get_access_level(request: Request) -> str:
    """Determines access level from token (header or query param)."""
    token = request.headers.get("X-Access-Token", "") or request.query_params.get("token", "")
    if not token:
        return "public"
    conn = sqlite3.connect(WEBAPP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT level FROM access_tokens WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "public"


@asynccontextmanager
async def lifespan(app_instance):
    init_webapp_db()
    seed_token()
    init_secretary_db()
    init_rclick_table()
    try:
        logging.info("[STARTUP] Initializing RAG service...")
        rag_service.init()
        logging.info("[STARTUP] RAG service initialized OK")
    except Exception as e:
        logging.error(f"[STARTUP] RAG init failed (non-fatal): {e}")
    yield


app = FastAPI(title="RIZALTA Web App API", version="0.9.6", lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROD_API = "http://127.0.0.1:8000"  # Локально к PROD боту
DIST_PATH = os.getenv("DIST_PATH", "../frontend/dist")

# Latin → Cyrillic normalization for lot codes (desktop browsers may send Latin lookalikes)
_LAT_TO_CYR = str.maketrans({
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н',
    'K': 'К', 'M': 'М', 'O': 'О', 'P': 'Р', 'S': 'С', 'T': 'Т',
})

def normalize_lot_code(code: str) -> str:
    """Normalize lot code: uppercase, Latin lookalikes → Cyrillic."""
    return code.strip().upper().translate(_LAT_TO_CYR)


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
    building: int = None
    include_18m: bool = True
    full_payment: bool = False

class XLSXRequest(BaseModel):
    code: str
    building: int = None

class DepositRequest(BaseModel):
    amount: int
    years: int = 11
    scenario: str = "base"  # base, optimistic, pessimistic

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    mode: str = "free"           # "lot_report" | "portfolio" | "free"
    lot_code: str | None = None
    building: int | None = None
    budget: int | None = None

class TaskCreateRequest(BaseModel):
    task: str
    date: str
    time: Optional[str] = None
    client_name: Optional[str] = None
    priority: str = "normal"

class TaskMoveRequest(BaseModel):
    new_date: str

class TaskParseRequest(BaseModel):
    text: str

class FixationAuthRequest(BaseModel):
    phone: str
    password: str

class FixationCreateRequest(BaseModel):
    client_name: str
    client_phone: str
    comment: str = ""

class MortgageRequest(BaseModel):
    price: int
    down_payment_pct: int = 30
    tariff: str = "base"
    loan_term_months: int = 360

class TrancheMortgageRequest(BaseModel):
    price: int
    down_payment_pct: float = 30.1

class TrancheMortgageAllRequest(BaseModel):
    price: int


# === Rate limiter (10 req/min per IP for /api/chat) ===
_chat_rate: dict[str, list[float]] = defaultdict(list)
CHAT_RATE_LIMIT = 10
CHAT_RATE_WINDOW = 60  # seconds


def check_chat_rate(request: Request):
    """Simple in-memory rate limiter for chat endpoint."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    # Clean old entries
    _chat_rate[ip] = [t for t in _chat_rate[ip] if now - t < CHAT_RATE_WINDOW]
    if len(_chat_rate[ip]) >= CHAT_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Слишком много запросов, подождите минуту")
    _chat_rate[ip].append(now)


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
    return {"status": "healthy", "version": "0.9.6"}


DOCS_BASE_DIR = Path(os.getenv("WEBAPP_ROOT", "/opt/webapp"))

@app.get("/api/docs/file")
async def docs_file(path: str = ""):
    """Read project files for Claude orchestration."""
    if not path:
        raise HTTPException(status_code=400, detail="?path= required")
    resolved = (DOCS_BASE_DIR / path).resolve()
    if not str(resolved).startswith(str(DOCS_BASE_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"{path} not found")
    ALLOWED_EXT = {'.py', '.md', '.txt', '.json', '.js', '.jsx', '.html', '.css',
                   '.toml', '.yaml', '.yml', '.cfg', '.ini', '.sh'}
    if resolved.suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(status_code=403, detail=f"Extension {resolved.suffix} not allowed")
    content = resolved.read_text(encoding="utf-8")
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/lots/search")
async def search_lot(code: str):
    """Search lot by code across all buildings (K1, K2, K3 — all in properties.db)."""
    code = normalize_lot_code(code)
    found = []

    db_path = os.getenv("PROPERTIES_DB", "/opt/bot/properties.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT code, building, floor, rooms, area_m2, price_rub, price_per_m2_rub, status, layout_url "
            "FROM units WHERE code = ?", (code,)
        )
        for row in cursor.fetchall():
            bname = {1: "Family", 2: "Business", 3: "Digital"}.get(row[1], f"Корпус {row[1]}")
            found.append({
                "code": row[0], "building": row[1], "buildingName": bname,
                "floor": row[2], "rooms": row[3], "area": row[4],
                "price": row[5], "priceM2": row[6], "status": row[7] or "available",
                "layout_url": row[8],
            })
        conn.close()

    if not found:
        return {"ok": False, "error": "Лот не найден"}
    if len(found) == 1:
        return {"ok": True, "lot": found[0]}
    return {"ok": True, "multiple": True, "lots": found}


@app.post("/api/chat")
async def api_chat(req: ChatRequest, request: Request):
    """AI chat with three modes: lot_report, portfolio, free."""
    check_chat_rate(request)

    # Mode routing
    if req.mode == "lot_report" and req.lot_code:
        generator = stream_lot_report(req.lot_code, req.building)
    elif req.mode == "portfolio" and req.budget:
        generator = stream_portfolio_report(req.budget)
    else:
        # Free chat
        if not req.message.strip():
            raise HTTPException(status_code=400, detail="Empty message")

        # Quick navigation (regex, no OpenAI)
        try:
            nav = quick_classify_navigation(req.message)
            if nav:
                return nav
        except Exception as e:
            logging.error(f"[CHAT] Navigation classify error: {e}")

        generator = stream_chat_with_tools(req.message, req.history)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

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
    """Заявка на показ — отправка в Telegram и Email."""
    try:
        result = await notify_showing_request(
            name=req.name,
            phone=req.phone,
            lot_code=req.lot_code,
            comment=req.comment,
            source="webapp"
        )

        # Заявка "принята" даже если отправка частично провалилась
        return {
            "ok": True,
            "message": "Заявка принята! Мы свяжемся с вами в ближайшее время.",
            "notifications": result
        }
    except Exception as e:
        import logging
        logging.error(f"[SHOWING ERROR] {e}")
        return {"ok": True, "message": "Заявка принята! Мы свяжемся с вами в ближайшее время."}

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
            building=req.building,
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
async def api_download_kp(code: str, type: str = "100", building: int = None):
    """GET endpoint для скачивания PDF КП (для мобильных)."""
    code = normalize_lot_code(code)
    try:
        pdf_path = generate_kp_pdf(
            code=code,
            building=building,
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
async def api_download_xlsx(code: str, building: int = None):
    """GET endpoint для скачивания Excel (для мобильных)."""
    code = normalize_lot_code(code)
    try:
        xlsx_path = generate_roi_xlsx(unit_code=code, output_dir="/tmp", building=building)
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
            output_dir="/tmp",
            building=req.building
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



@app.get("/api/payment-pdf")
async def api_payment_pdf(price: int, code: str = ""):
    """Generate and download payment options PDF."""
    code = normalize_lot_code(code) if code else ""
    try:
        pdf_path = generate_payment_pdf(price, code)
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"Payment_{code or price}.pdf"
            )
        return {"ok": False, "error": "Ошибка генерации PDF"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/strategy-pdf")
async def api_strategy_pdf(request: Request):
    """Generate investment strategy PDF from AI chat data."""
    body = await request.json()
    try:
        pdf_path = generate_strategy_pdf(body)
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"RIZALTA_Strategy_{int(time.time())}.pdf"
            )
        return {"ok": False, "error": "Ошибка генерации PDF"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/portfolio-pdf")
async def api_portfolio_pdf(request: Request):
    """Generate portfolio PDF from report data + AI text (chat-style cards)."""
    from services.portfolio_pdf_generator import generate_portfolio_pdf
    body = await request.json()
    data = body.get("data", {})
    ai_text = body.get("ai_text", "")
    pdf_bytes = generate_portfolio_pdf(data, ai_text)
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation failed")
    budget = data.get("budget", 0)
    filename = f"RIZALTA_Portfolio_{budget // 1_000_000}M.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/lot-summary-pdf")
async def api_lot_summary_pdf(request: Request):
    """Generate comprehensive lot summary PDF (all 7 sections)."""
    from services.lot_summary_pdf_generator import generate_lot_summary_pdf
    body = await request.json()
    pdf_bytes = generate_lot_summary_pdf(body)
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation failed")
    import urllib.parse
    code = body.get("lot", {}).get("code", "lot")
    filename = f"RIZALTA_{code}_Summary.pdf"
    filename_ascii = filename.encode('ascii', 'ignore').decode()
    filename_utf8 = urllib.parse.quote(filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename_ascii}\"; filename*=UTF-8''{filename_utf8}"},
    )


@app.get("/api/download-compare-pdf")
async def api_download_compare_pdf(amount: int, years: int = 11, area: float = 26.8):
    """Генерация PDF сравнения Депозит vs RIZALTA."""
    try:
        pdf_path = generate_compare_pdf(amount, years, area_m2=area)
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"RIZALTA_vs_Deposit_{amount}.pdf"
            )
        return {"ok": False, "error": "Ошибка генерации PDF"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# === Secretary endpoints ===

@app.get("/api/secretary/tasks")
async def api_get_tasks(date: str):
    """Get tasks for a specific date (YYYY-MM-DD)."""
    try:
        tasks = get_tasks_for_date(date)
        return {"ok": True, "date": date, "tasks": tasks}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/secretary/tasks/week")
async def api_get_tasks_week(start: str):
    """Get tasks for 7 days starting from date."""
    try:
        week = get_tasks_for_week(start)
        return {"ok": True, "start": start, "week": week}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/secretary/tasks")
async def api_create_task(req: TaskCreateRequest):
    """Create a new task."""
    try:
        task = add_task(
            task=req.task, date=req.date, time=req.time,
            client_name=req.client_name, priority=req.priority
        )
        return {"ok": True, "task": task}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.put("/api/secretary/tasks/{task_id}/done")
async def api_mark_done(task_id: int):
    """Mark task as done."""
    success = mark_done(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@app.put("/api/secretary/tasks/{task_id}/undone")
async def api_mark_undone(task_id: int):
    """Mark task as not done."""
    success = mark_undone(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@app.put("/api/secretary/tasks/{task_id}/move")
async def api_move_task(task_id: int, req: TaskMoveRequest):
    """Move task to a different date."""
    success = move_task(task_id, req.new_date)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@app.delete("/api/secretary/tasks/{task_id}")
async def api_delete_task(task_id: int):
    """Delete a task."""
    success = delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@app.post("/api/secretary/parse")
async def api_parse_task(req: TaskParseRequest):
    """AI-parse free text into a structured task."""
    try:
        parsed = parse_task_with_ai(req.text)
        return {"ok": True, **parsed}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Fixation endpoints ===

def _get_session_id(request: Request) -> str:
    """Get or generate session ID from cookie or header."""
    sid = request.cookies.get("rclick_session") or request.headers.get("X-Session-Id", "")
    if not sid:
        import secrets as sec
        sid = sec.token_urlsafe(16)
    return sid


@app.post("/api/fixation/auth")
async def api_fixation_auth(req: FixationAuthRequest, request: Request):
    """Authenticate with ri.rclick.ru."""
    session_id = _get_session_id(request)
    result = await rclick_auth(req.phone, req.password, session_id)
    if result.get("ok"):
        from fastapi.responses import JSONResponse
        resp = JSONResponse(result)
        resp.set_cookie("rclick_session", session_id, httponly=True, max_age=86400 * 30)
        return resp
    return result


@app.get("/api/fixation/status")
async def api_fixation_status(request: Request):
    """Check if user is authenticated with rclick."""
    session_id = _get_session_id(request)
    return await rclick_check_status(session_id)


@app.post("/api/fixation/create")
async def api_fixation_create(req: FixationCreateRequest, request: Request):
    """Create a client fixation."""
    session_id = _get_session_id(request)
    return await rclick_create_fixation(
        session_id=session_id,
        client_name=req.client_name,
        client_phone=req.client_phone,
        comment=req.comment,
    )


@app.post("/api/fixation/logout")
async def api_fixation_logout(request: Request):
    """Logout from rclick."""
    session_id = _get_session_id(request)
    result = await rclick_logout(session_id)
    from fastapi.responses import JSONResponse
    resp = JSONResponse(result)
    resp.delete_cookie("rclick_session")
    return resp


# === Whitelist endpoints ===

@app.get("/api/access/check")
async def check_access(level: str = Depends(get_access_level)):
    """Checks token and returns access level."""
    return {"level": level}


# DEACTIVATED: Corp3 now in properties.db. Reuse for Corp4.
# @app.get("/api/corp3/lots")
# async def get_corp3_lots(level: str = Depends(get_access_level)):
#     """Returns Corp3 lots (whitelist only)."""
#     if level != "white":
#         raise HTTPException(status_code=403, detail="Access denied")
#     with open(CORP3_DATA_PATH, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#     units = [u for u in data.get("units", [])
#              if u.get("area", 0) >= 23.5 and u.get("status") == "available"]
#     return {
#         "ok": True,
#         "building_name": data.get("building_name", "Корпус 3"),
#         "total": len(units),
#         "lots": units
#     }

# @app.get("/api/corp3/layout/{code}")
# async def get_corp3_layout(code: str, level: str = Depends(get_access_level)):
#     """Serves Corp3 lot layout image (whitelist only)."""
#     if level != "white":
#         raise HTTPException(status_code=403, detail="Access denied")
#     code = normalize_lot_code(code)
#     with open(CORP3_DATA_PATH, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#     unit = next((u for u in data.get("units", []) if u.get("code") == code), None)
#     if not unit or not unit.get("layout_path"):
#         raise HTTPException(status_code=404, detail="Layout not found")
#     layout_path = unit["layout_path"]
#     real_path = os.path.realpath(layout_path)
#     if not real_path.startswith(os.path.realpath(CORP3_LAYOUTS_DIR)):
#         raise HTTPException(status_code=403, detail="Invalid path")
#     if not os.path.isfile(real_path):
#         raise HTTPException(status_code=404, detail="File not found")
#     return FileResponse(real_path, media_type="image/jpeg")


# === File serving (whitelist) ===

PRESENTATIONS_DIR = os.getenv("PRESENTATIONS_DIR", "/opt/bot-dev/presentations")
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "/opt/bot/docs")
VIDEOS_DIR = os.getenv("VIDEOS_DIR", "/opt/bot-dev/videos")

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


# === News endpoints ===

@app.get("/api/news/weather")
async def api_news_weather():
    """Weather in Belokurikha via Open-Meteo."""
    try:
        data = await get_weather()
        if data:
            return {"ok": True, "data": data}
        return {"ok": False, "error": "Не удалось получить погоду"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/news/flights")
async def api_news_flights():
    """Flight prices Moscow → Gorno-Altaysk via Aviasales."""
    try:
        data = await get_flights()
        if data:
            return {"ok": True, "data": data}
        return {"ok": False, "error": "Нет данных о рейсах"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/news/digest")
async def api_news_digest():
    """Investment news digest from RSS feeds."""
    try:
        news = await get_news_digest()
        return {"ok": True, "data": news}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === MGP endpoints ===

@app.get("/api/mgp/calculate")
async def api_mgp_calculate(area: float):
    """Calculate MGP for a given area."""
    try:
        rows = calc_mgp(area)
        data = []
        for year_num, mgp_nom, mgp_comm in rows:
            data.append({
                "year": year_num,
                "nominal": mgp_nom,
                "commercial": mgp_comm,
            })
        total_nom = sum(r[1] for r in rows)
        total_comm = sum(r[2] for r in rows)
        return {
            "ok": True,
            "area": area,
            "years": data,
            "total_nominal": total_nom,
            "total_commercial": total_comm,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/mgp/pdf")
async def api_mgp_pdf(code: str, area: float, building: int = None):
    """Generate and download MGP PDF."""
    code = normalize_lot_code(code)
    try:
        pdf_path = generate_mgp_pdf(code, area, building)
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"MGP_{code}.pdf"
            )
        return {"ok": False, "error": "Ошибка генерации PDF"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Mortgage endpoints ===

@app.get("/api/mortgage/options")
async def api_mortgage_options():
    """Returns available mortgage options (tariffs, terms, down payments)."""
    try:
        return {"ok": True, "data": get_mortgage_options()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/mortgage/calculate")
async def api_mortgage_calculate(req: MortgageRequest):
    """Calculate mortgage for given parameters."""
    try:
        result = calc_mortgage(
            price=req.price,
            down_payment_pct=req.down_payment_pct,
            tariff=req.tariff,
            loan_term_months=req.loan_term_months,
        )
        return {"ok": True, "data": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/mortgage/pdf")
async def api_mortgage_pdf(price: int, down_payment_pct: int = 30, tariff: str = "base", loan_term_months: int = 360):
    """Generate and download mortgage PDF."""
    try:
        data = calc_mortgage(price, down_payment_pct, tariff, loan_term_months)
        pdf_path = generate_mortgage_pdf(data)
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"Mortgage_{price}.pdf"
            )
        return {"ok": False, "error": "Ошибка генерации PDF"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Tranche mortgage endpoints ===

@app.post("/api/tranche-mortgage/calculate")
async def api_tranche_mortgage_calculate(req: TrancheMortgageRequest):
    """Calculate tranche mortgage for given price and down payment."""
    try:
        result = calc_tranche_mortgage(req.price, req.down_payment_pct)
        if result is None:
            return {"ok": False, "error": "Невозможно рассчитать для данных параметров"}
        return {"ok": True, "data": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/tranche-mortgage/all")
async def api_tranche_mortgage_all(req: TrancheMortgageAllRequest):
    """Calculate all 4 tranche mortgage scenarios for a given price."""
    try:
        results = calc_tranche_all(req.price)
        return {"ok": True, "data": [r for r in results if r is not None]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/tranche-mortgage/pdf")
async def api_tranche_mortgage_pdf(code: str, building: int = None):
    """Generate and download tranche mortgage PDF."""
    code = normalize_lot_code(code)
    try:
        from services.tranche_mortgage_pdf_generator import generate_tranche_mortgage_pdf
        pdf_bytes = generate_tranche_mortgage_pdf(code, building)
        if not pdf_bytes:
            raise HTTPException(status_code=404, detail="Лот не найден или расчёт невозможен")
        import urllib.parse
        filename = f"RIZALTA_{code}_Tranche.pdf"
        filename_ascii = filename.encode('ascii', 'ignore').decode()
        filename_utf8 = urllib.parse.quote(filename)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=\"{filename_ascii}\"; filename*=UTF-8''{filename_utf8}"},
        )
    except HTTPException:
        raise
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
