from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
import os

app = FastAPI(title="RIZALTA Web App API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROD_API = "https://api.rizaltaservice.ru"
DIST_PATH = "/opt/webapp/frontend/dist"

@app.get("/api/lots")
async def get_lots():
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{PROD_API}/api/lots")
            return response.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/assets/{file_path:path}")
async def serve_assets(file_path: str):
    full_path = f"{DIST_PATH}/assets/{file_path}"
    if os.path.isfile(full_path):
        media_type = "application/javascript" if file_path.endswith(".js") else "text/css"
        return FileResponse(full_path, media_type=media_type)
    return Response(status_code=404)

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = f"{DIST_PATH}/{full_path}"
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(f"{DIST_PATH}/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
