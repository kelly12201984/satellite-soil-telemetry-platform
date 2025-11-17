# api/app/services/ingest_min.py
from typing import Optional, Dict, Any, Iterable, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from uuid import uuid4
from datetime import datetime, timezone

from api.app.models import device as device_model
from api.app.models import message as message_model
from api.app.models import reading as reading_model

# Optional decoder imports (guarded)
try:
    from api.app.decoders import smartone_c as smartone
except Exception:
    smartone = None


# ---- utilities --------------------------------------------------------------


def _ensure_device(
    db: Session, *, esn: str, name: Optional[str]
) -> device_model.Device:
    dev = db.query(device_model.Device).filter_by(esn=esn).first()
    if dev:
        if name and getattr(dev, "name", None) != name:
            setattr(dev, "name", name)
            db.add(dev)
        return dev
    dev = device_model.Device(esn=esn, name=name)
    db.add(dev)
    db.flush()
    return dev


def _get(d: Dict[str, Any], *paths: str, default=None):
    """Try multiple dot-paths to pull a value from nested dicts."""
    for p in paths:
        cur = d
        ok = True
        for k in p.split("."):
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok:
            return cur
    return default


def _find_key_ci(obj, key: str):
    """Recursively search dict/list for the first value whose key matches `key` (case-insensitive)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() == key.lower():
                return v
            found = _find_key_ci(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_key_ci(item, key)
            if found is not None:
                return found
    return None


def _to_float(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str) and x.strip() != "":
        try:
            return float(x)
        except ValueError:
            return None
    return None


def _assign_first_attr(obj, candidates: Iterable[str], value) -> Optional[str]:
    """
    Assign `value` to the first attribute name that exists on `obj`.
    Returns the attribute name used, or None if none matched.
    """
    for name in candidates:
        if hasattr(obj, name):
            setattr(obj, name, value)
            return name
    return None


def _try_decode_hex(hex_payload: str) -> List[Dict[str, Any]]:
    """
    Attempt to decode SmartOne-C bytes using decoder modules.
    Returns list of reading dicts with depth_cm, moisture_pct, temperature_c.
    """
    if not hex_payload or not smartone:
        return []

    # Normalize hex (strip spaces/0x)
    clean = str(hex_payload).strip().lower().replace("0x", "").replace(" ", "")
    try:
        raw = bytes.fromhex(clean)
    except Exception:
        return []

    if len(raw) < 1:
        return []

    # Check frame type and decode accordingly
    frame_type = raw[0]

    try:
        if frame_type == 0x02:
            # Type-2: Soil sensor data
            return smartone.decode_type2_soil(raw)
        elif frame_type == 0x00:
            # Type-0: GPS location (not soil data)
            decoded = smartone.decode_type0(raw)
            return []  # GPS frames don't contain soil readings
        else:
            # Unknown frame type
            return []
    except Exception:
        return []


# ---- normalization ----------------------------------------------------------


def _normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map arbitrary XML/JSON (converted to dict) into a minimal structure.
    """
    # Likely ESN locations
    esn_candidates = [
        "message.esn",
        "root.esn",
        "esn",
        "Envelope.Device.ESN",
        "Envelope.Device.esn",
        "Device.ESN",
        "device.esn",
        "bof.device.esn",
        "BOF.Device.ESN",
    ]
    esn = _get(payload, *esn_candidates, default=None) or _find_key_ci(payload, "esn")
    if not esn:
        top = list(payload.keys())[:8] if isinstance(payload, dict) else []
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Missing ESN", "top_level_keys": top},
        )

    device_name = _get(payload, "message.device_name", "device.name", "Device.Name")
    if not device_name:
        device_name = _find_key_ci(payload, "device_name") or _find_key_ci(
            payload, "name"
        )

    # message_id: required by your DB (NOT NULL). Pull if present; else generate.
    message_id = (
        _get(
            payload, "message.message_id", "message.id", "id", "MessageID", "message_id"
        )
        or _find_key_ci(payload, "message_id")
        or _find_key_ci(payload, "id")
        or str(uuid4())
    )

    # raw payload as string (cap size)
    raw_text = str(payload)
    if len(raw_text) > 8000:
        raw_text = raw_text[:8000]

    # Extract hex payload if present (from XML <payload> tag)
    # xmltodict puts tag text in '#text' when attributes exist
    hex_payload = _get(payload, "payload", "hexPayload") or _find_key_ci(
        payload, "payload"
    )
    # Handle xmltodict structure where payload is a dict with '#text'
    if isinstance(hex_payload, dict) and "#text" in hex_payload:
        hex_payload = hex_payload["#text"]

    # optional reading values
    moisture = _get(payload, "message.reading.moisture", "reading.moisture")
    if moisture is None:
        moisture = _find_key_ci(payload, "moisture")

    temp_c = _get(payload, "message.reading.temperature_c", "reading.temperature_c")
    if temp_c is None:
        temp_c = (
            _find_key_ci(payload, "temperature_c")
            or _find_key_ci(payload, "temp_c")
            or _find_key_ci(payload, "temperature")
        )

    return {
        "esn": str(esn),
        "device_name": device_name,
        "message_id": str(message_id),
        "raw_text": raw_text,
        "hex_payload": str(hex_payload) if hex_payload else None,
        "moisture": _to_float(moisture),
        "temp_c": _to_float(temp_c),
    }


# ---- main entry -------------------------------------------------------------


def ingest_envelope(payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Normalize payload -> upsert Device -> insert Message (+ optional Reading)
    Commit once, return IDs and totals.
    """
    data = _normalize(payload)

    # Ensure device
    dev = _ensure_device(db, esn=data["esn"], name=data.get("device_name"))

    # Create Message and map to your schema
    msg = message_model.Message()

    # Required: device_id
    _assign_first_attr(msg, ("device_id", "device", "device_fk", "deviceId"), dev.id)

    # Required: message_id (your DB enforces NOT NULL)
    _assign_first_attr(
        msg, ("message_id", "msg_id", "external_id", "externalId"), data["message_id"]
    )

    # Raw payload text
    _assign_first_attr(
        msg,
        (
            "raw_payload",
            "raw",
            "payload",
            "body",
            "content",
            "data",
            "text",
            "message_text",
        ),
        data["raw_text"],
    )

    # Received at (if model has a field)
    _assign_first_attr(
        msg,
        ("received_at", "created_at", "ingested_at", "timestamp_utc"),
        datetime.now(timezone.utc).replace(tzinfo=None),  # naive timestamp for PG
    )

    db.add(msg)
    db.flush()  # ensure msg.id

    # Try to decode hex payload into readings
    readings_saved = 0
    if data.get("hex_payload"):
        decoded_readings = _try_decode_hex(data["hex_payload"])
        if decoded_readings:
            for rd in decoded_readings:
                reading = reading_model.Reading()
                _assign_first_attr(
                    reading, ("device_id", "device", "device_fk", "deviceId"), dev.id
                )
                _assign_first_attr(
                    reading,
                    ("message_id", "message", "message_fk", "messageId"),
                    msg.id,
                )
                _assign_first_attr(
                    reading,
                    ("moisture", "soil_moisture", "moisture_pct", "moisture_percent"),
                    rd.get("moisture_pct"),
                )
                _assign_first_attr(
                    reading,
                    ("temperature_c", "temp_c", "temperature", "temp"),
                    rd.get("temperature_c"),
                )
                _assign_first_attr(
                    reading,
                    ("depth_cm", "depth", "probe_depth_cm"),
                    rd.get("depth_cm", 0.0),
                )
                db.add(reading)
                readings_saved += 1

    # Create Reading if we have values from JSON, mapping to plausible columns
    if data.get("moisture") is not None or data.get("temp_c") is not None:
        reading = reading_model.Reading()
        _assign_first_attr(
            reading, ("device_id", "device", "device_fk", "deviceId"), dev.id
        )
        _assign_first_attr(
            reading, ("message_id", "message", "message_fk", "messageId"), msg.id
        )
        _assign_first_attr(
            reading,
            ("moisture", "soil_moisture", "moisture_pct", "moisture_percent"),
            data.get("moisture"),
        )
        _assign_first_attr(
            reading,
            ("temperature_c", "temp_c", "temperature", "temp"),
            data.get("temp_c"),
        )
        _assign_first_attr(
            reading, ("depth_cm", "depth", "probe_depth_cm"), data.get("depth_cm", 0.0)
        )
        db.add(reading)

    db.commit()

    # Get totals (three separate scalar queries)
    dcnt = db.query(func.count(device_model.Device.id)).scalar() or 0
    mcnt = db.query(func.count(message_model.Message.id)).scalar() or 0
    rcnt = db.query(func.count(reading_model.Reading.id)).scalar() or 0

    return {
        "device_id": dev.id,
        "message_id": msg.id,
        "totals": {"devices": dcnt, "messages": mcnt, "readings": rcnt},
    }
