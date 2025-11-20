# api/app/routers/uplink.py
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.ingest_min import ingest_envelope
from app.settings import settings
import xmltodict, json

router = APIRouter(prefix="/v1/uplink", tags=["uplink"])

# Globalstar source IPs (allowed without token authentication)
GLOBALSTAR_IPS = {
    "3.228.87.237",
    "34.231.245.76",
    "3.135.136.171",
    "3.133.245.206",
}

def _get_client_ip(request: Request) -> str:
    """Get real client IP, accounting for Cloudflare and proxies."""
    # Cloudflare sets CF-Connecting-IP with the real client IP
    if cf_ip := request.headers.get("cf-connecting-ip"):
        return cf_ip.strip()
    # Fall back to X-Forwarded-For (take first IP in chain)
    if forwarded := request.headers.get("x-forwarded-for"):
        return forwarded.split(",")[0].strip()
    # Last resort: direct connection IP
    return request.client.host if request.client else "unknown"

def _require_token(request: Request):
    """
    Check authentication:
    - Allow Globalstar IPs without token
    - Require X-Uplink-Token from all other sources
    """
    client_ip = _get_client_ip(request)

    # Allow Globalstar IPs without authentication
    if client_ip in GLOBALSTAR_IPS:
        return

    # Everyone else must provide valid token
    required = (settings.UPLINK_SHARED_TOKEN or "").strip()
    if not required:
        # No token configured -> allow (dev convenience)
        return
    supplied = request.headers.get("x-uplink-token", "").strip()
    if supplied != required:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or missing uplink token (source IP: {client_ip})"
        )

@router.post("/receive")
async def receive_uplink(request: Request, db: Session = Depends(get_db)):
    _require_token(request)

    raw = await request.body()
    ctype = request.headers.get("content-type", "").lower()
    try:
        if "xml" in ctype or raw.strip().startswith(b"<"):
            payload = xmltodict.parse(raw)
        else:
            payload = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bad payload: {e}")

    return ingest_envelope(payload, db)
