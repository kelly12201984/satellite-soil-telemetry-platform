# api/app/main.py
from __future__ import annotations

from pathlib import Path
import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.app.settings import settings
from api.app.routers import uplink
from api.app.routers import readings as readings_router
from api.app.routers import metrics
from api.app.routers import devices
from api.app.routers import constants

# ---------- Logging ----------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("soilprobe")

# ---------- App ----------
app = FastAPI(
    title="Soil Probe Platform API",
    debug=(settings.ENV in {"local", "dev"}),
)

# ---------- Static files (UI) ----------
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Serve /static/* for raw assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Simple page to view latest readings
@app.get("/readings")
def readings_page():
    html = STATIC_DIR / "readings.html"
    if not html.exists():
        # Helpful error if the file is missing
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"{html} not found on server")
    return FileResponse(html, media_type="text/html")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Routers ----------
app.include_router(uplink.router)
app.include_router(readings_router.router)
app.include_router(metrics.router)
app.include_router(devices.router)
app.include_router(constants.router)

# ---------- Root / Health ----------
@app.get("/")
def root():
    return {"status": "running", "env": settings.ENV}

# ---------- DEBUG UTILITIES ----------
@app.api_route("/__debug/echo", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def debug_echo(request: Request):
    raw = await request.body()
    try:
        as_json: Any = await request.json()
    except Exception:
        as_json = None
    return {
        "method": request.method,
        "path": str(request.url),
        "headers": {k: v for k, v in request.headers.items()},
        "json": as_json,
        "raw_len": len(raw),
        "raw_preview": raw[:200].decode("utf-8", errors="ignore"),
    }

@app.get("/__debug/sql")
def debug_sql():
    from sqlalchemy import text
    from api.app.db.session import engine
    with engine.connect() as conn:
        val = conn.execute(text("select 1")).scalar_one()
    return {"db_ok": True, "select_1": val}

# ---------- ERROR HANDLERS ----------
@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(request: Request, exc: StarletteHTTPException):
    payload = {
        "error": "HTTPException",
        "status_code": exc.status_code,
        "detail": exc.detail,
        "method": request.method,
        "path": str(request.url),
    }
    return JSONResponse(status_code=exc.status_code, content=payload)

@app.exception_handler(RequestValidationError)
async def validation_exc_handler(request: Request, exc: RequestValidationError):
    payload = {
        "error": "ValidationError",
        "status_code": 422,
        "detail": exc.errors(),
        "body": (await request.body()).decode("utf-8", errors="ignore"),
        "method": request.method,
        "path": str(request.url),
    }
    return JSONResponse(status_code=422, content=payload)

@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    log.error("Unhandled error on %s %s: %s\n%s", request.method, request.url, exc, tb)
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "method": request.method,
            "path": str(request.url),
            "traceback": tb,
        },
    )
