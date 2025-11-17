# api/app/routers/uplink.py
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from api.app.db.session import get_db
from api.app.services.ingest_min import ingest_envelope
from api.app.settings import settings
import xmltodict, json

router = APIRouter(prefix="/v1/uplink", tags=["uplink"])

def _require_token(request: Request):
    """Simple shared-secret check via header X-Uplink-Token."""
    required = (settings.UPLINK_SHARED_TOKEN or "").strip()
    if not required:
        # No token configured -> allow (dev convenience)
        return
    supplied = request.headers.get("x-uplink-token", "").strip()
    if supplied != required:
        raise HTTPException(status_code=401, detail="Invalid or missing uplink token")

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
