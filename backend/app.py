from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="RIZALTA Web App API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROD_API = "https://api.rizaltaservice.ru"

@app.get("/")
async def root():
    return {"status": "ok", "service": "RIZALTA Web App"}

@app.get("/api/lots")
async def get_lots():
    """Проксируем запрос к PROD API"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{PROD_API}/api/lots")
            return response.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "prod_api": PROD_API}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
