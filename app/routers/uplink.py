# api/app/routers/uplink.py
import logging
from fastapi import APIRouter, Depends, Request, HTTPException, Response
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

log = logging.getLogger("soilprobe.uplink")

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

def _is_xml_request(raw: bytes, content_type: str) -> bool:
    """Check if the incoming request is XML format."""
    ctype = (content_type or "").lower()
    return "xml" in ctype or raw.strip().startswith(b"<")


def _parse_payload(raw: bytes, content_type: str):
    if not raw:
        raise HTTPException(status_code=400, detail="Empty body")
    ctype = (content_type or "").lower()
    try:
        if "xml" in ctype or raw.strip().startswith(b"<"):
            return xmltodict.parse(raw)
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Bad payload: {exc}")


def _make_response(data: dict, is_xml: bool) -> Response:
    """
    Return response in the same format as the request.
    XML requests get XML responses, JSON requests get JSON responses.
    """
    if is_xml:
        xml_content = xmltodict.unparse({"response": data}, pretty=True)
        return Response(content=xml_content, media_type="application/xml")
    return Response(
        content=json.dumps(data),
        media_type="application/json"
    )

@router.post("/receive")
async def receive_uplink(request: Request, db: Session = Depends(get_db)):
    _require_token(request)

    raw = await request.body()
    content_type = request.headers.get("content-type", "")
    is_xml = _is_xml_request(raw, content_type)
    payload = _parse_payload(raw, content_type)

    result = ingest_envelope(payload, db)
    return _make_response(result, is_xml)


@router.post("/confirmation")
async def provisioning_confirmation(request: Request):
    """
    Confirmation endpoint (Globalstar form B4.3).
    Accepts XML or JSON payloads indicating provisioning/activation events.
    Returns response in the same format as the request (XML or JSON).
    """
    _require_token(request)
    raw = await request.body()
    content_type = request.headers.get("content-type", "")
    is_xml = _is_xml_request(raw, content_type)
    payload = _parse_payload(raw, content_type)

    esn = None
    if isinstance(payload, dict):
        # attempt to pull ESN/Device identifier for logging
        for key in ("esn", "ESN", "device_esn", "deviceId"):
            if key in payload:
                esn = payload[key]
                break
        if not esn:
            # look deeper if Globalstar style envelope
            if isinstance(payload.get("stuMessage"), dict):
                esn = payload["stuMessage"].get("esn")
            elif isinstance(payload.get("stuMessages"), dict):
                inner = payload["stuMessages"].get("stuMessage")
                if isinstance(inner, dict):
                    esn = inner.get("esn")

    log.info(
        "Received provisioning confirmation",
        extra={"esn": esn, "payload_preview": str(payload)[:500]},
    )

    result = {
        "status": "ok",
        "type": "provisioning_confirmation",
        "esn": esn,
        "ack": True,
    }
    return _make_response(result, is_xml)
