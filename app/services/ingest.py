# api/app/services/ingest.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session
import xmltodict

from app.models import device as device_model
from app.models import message as message_model
from app.models import reading as reading_model

# --- Guarded deps ---
try:
    import xmltodict  # type: ignore
except Exception:
    xmltodict = None

# Optional decoder imports (guarded)
try:
    from app.decoders import smartone_c as smartone
    from app.decoders import smartone_util as sutil
except Exception:  # files exist in your tree; if they change, we still run
    smartone = None
    sutil = None

def _ensure_device(db: Session, esn: str, name: str | None = None) -> device_model.Device:
    dev = db.query(device_model.Device).filter_by(esn=esn).first()
    if not dev:
        dev = device_model.Device(esn=esn, name=name)
        db.add(dev)
        db.flush()
    return dev


def _persist_message(db: Session, device_id: int, message_id: str | None, raw_payload: str) -> message_model.Message:
    msg = message_model.Message(
        device_id=device_id,
        message_id=message_id or "",
        raw_payload=raw_payload,
        received_at=datetime.utcnow(),
    )
    db.add(msg)
    db.flush()
    return msg


def _persist_readings(db: Session, device_id: int, message_id: int, readings: List[Dict[str, Any]]) -> int:
    saved = 0
    for rec in readings:
        rd = reading_model.Reading(
            device_id=device_id,
            message_id=message_id,
            depth_cm=float(rec.get("depth_cm", 0)),
            moisture_pct=rec.get("moisture_pct"),
            temperature_c=rec.get("temperature_c"),
            timestamp=rec.get("timestamp") or datetime.utcnow(),
        )
        db.add(rd)
        saved += 1
    return saved


def _parse_xml_envelope(xml_text: str) -> Dict[str, Any]:
    if xmltodict is None:
        return {}  # XML support not installed; just store raw message
    try:
        doc = xmltodict.parse(xml_text)
    except Exception:
        return {}
       

    # flatten a level if there is a single root object
    if isinstance(doc, dict) and len(doc) == 1 and isinstance(next(iter(doc.values())), dict):
        doc = next(iter(doc.values()))

    def first_key(d: dict, keys: list[str]) -> Any:
        for k in keys:
            if k in d:
                return d[k]
        return None

    d = {}
    d["esn"] = str(first_key(doc, ["esn", "ESN", "deviceESN", "DeviceESN"]) or "")
    d["message_id"] = str(first_key(doc, ["messageID", "MessageID", "msgId", "id"]) or "")
    unix = first_key(doc, ["unixTime", "UnixTime", "gpsTime", "GPSTime"])
    if unix:
        try:
            d["unixTime"] = int(str(unix))
        except Exception:
            pass
    payload = first_key(doc, ["hexPayload", "payload", "Payload", "data", "Data"])
    if payload:
        d["hex_payload"] = str(payload).strip()
    return d


def _try_decode_hex(hex_payload: str) -> List[Dict[str, Any]]:
    """
    Attempt to decode SmartOne-C bytes using your decoder modules.
    This is defensive: if API changes, we return [] and keep going.
    Expected return: list of dicts with depth_cm, moisture_pct, temperature_c, timestamp
    """
    if not hex_payload:
        return []

    # Normalize hex (strip spaces/0x)
    clean = hex_payload.strip().lower().replace("0x", "").replace(" ", "")
    try:
        raw = bytes.fromhex(clean)
    except Exception:
        return []

    if not smartone:
        return []

    # Heuristic: look for a function named "decode", "parse", or similar
    decode_fn = getattr(smartone, "decode", None) or getattr(smartone, "parse", None)
    if not callable(decode_fn):
        return []

    try:
        decoded = decode_fn(raw)  # shape depends on your module
        # Try to map common shapes to our Reading fields
        readings: List[Dict[str, Any]] = []
        if isinstance(decoded, dict) and "readings" in decoded:
            for r in decoded["readings"]:
                readings.append(
                    {
                        "depth_cm": float(r.get("depth_cm", 0)),
                        "moisture_pct": r.get("moisture_pct"),
                        "temperature_c": r.get("temperature_c"),
                        "timestamp": r.get("timestamp"),
                    }
                )
        elif isinstance(decoded, list):
            for r in decoded:
                readings.append(
                    {
                        "depth_cm": float(r.get("depth_cm", 0)),
                        "moisture_pct": r.get("moisture_pct"),
                        "temperature_c": r.get("temperature_c"),
                        "timestamp": r.get("timestamp"),
                    }
                )
        # else: unknown shape → ignore
        return readings
    except Exception:
        return []


def ingest_envelope(payload: Any, db: Session) -> dict:
    """Accept JSON dict or XML string/bytes. Persist device, message, and decoded readings when possible."""
    # XML path
    if isinstance(payload, (bytes, str)):
        text = payload.decode("utf-8", errors="ignore") if isinstance(payload, bytes) else payload
        info = _parse_xml_envelope(text)
        esn = info.get("esn") or "UNKNOWN"
        device = _ensure_device(db, esn=esn)
        msg = _persist_message(db, device.id, info.get("message_id"), raw_payload=text)

        saved = 0
        if "hex_payload" in info:
            decoded = _try_decode_hex(info["hex_payload"])
            if decoded:
                saved = _persist_readings(db, device.id, msg.id, decoded)

        db.commit()
        note = "xml stored" + (", decoded" if saved else ", decoder pending")
        return {"status": "ok", "records_saved": saved, "note": note}

    # JSON path
    if not isinstance(payload, dict):
        return {"status": "ignored", "reason": "unsupported payload type"}

    esn = payload.get("esn") or "UNKNOWN"
    device = _ensure_device(db, esn=esn, name=payload.get("device_name"))
    msg = _persist_message(db, device.id, str(payload.get("message_id") or ""), raw_payload=str(payload))

    saved = 0
    # (a) already-decoded readings
    if isinstance(payload.get("readings"), list):
        saved += _persist_readings(db, device.id, msg.id, payload["readings"])

    # (b) raw hex payload to decode
    hex_payload = payload.get("hex_payload")
    if hex_payload:
        decoded = _try_decode_hex(hex_payload)
        if decoded:
            saved += _persist_readings(db, device.id, msg.id, decoded)

    db.commit()
    return {"status": "ok", "records_saved": saved}
