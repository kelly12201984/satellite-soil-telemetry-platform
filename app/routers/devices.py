# api/app/routers/devices.py
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.session import get_db
from app.models import device as device_model
from app.models import device_config as device_config_model
from app.models import reading as reading_model
from app.services.status import compute_device_status, severity_order

router = APIRouter(prefix="/v1/devices", tags=["devices"])


def _format_last_seen(last_seen: Optional[datetime]) -> str:
    """Format last_seen as relative time string."""
    if last_seen is None:
        return "never"
    
    now = datetime.utcnow()
    delta = now - last_seen
    minutes = int(delta.total_seconds() / 60)
    
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"
    days = hours // 24
    return f"{days}d"


@router.get("/attention")
def devices_attention(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get devices needing attention, sorted worst to best.
    Status: 'red' | 'amber' | 'green' | 'blue' | 'stale' | 'offline' | 'gray'
    Priority: RED > AMBER > STALE > OFFLINE > BLUE > GREEN
    """
    devices = db.query(device_model.Device).all()
    result = []
    
    for device in devices:
        # Get device config
        config = (
            db.query(device_config_model.DeviceConfig)
            .filter(device_config_model.DeviceConfig.device_id == device.id)
            .first()
        )
        
        # Compute status
        status_info = compute_device_status(db, device, config)
        
        # Get latest 30cm moisture for display
        latest_30cm = (
            db.query(reading_model.Reading.moisture_pct)
            .filter(
                reading_model.Reading.device_id == device.id,
                reading_model.Reading.depth_cm == 30.0,
            )
            .order_by(reading_model.Reading.timestamp.desc())
            .limit(1)
            .scalar()
        )
        
        last_seen_dt = status_info["last_seen"]
        result.append({
            "device_id": device.id,
            "alias": device.name or device.esn or f"Device {device.id}",
            "status": status_info["status"],
            "last_seen": _format_last_seen(last_seen_dt),
            "last_seen_dt": last_seen_dt,  # Keep datetime for sorting
            "moisture30": round(latest_30cm, 1) if latest_30cm is not None else None,
            "battery_hint": status_info["battery_hint"],
            "worst_depth_cm": status_info["worst_depth_cm"],
            "spike_detected": status_info["spike_detected"],
        })
    
    # Sort by severity (lower severity_order = higher priority), then by most stale
    now = datetime.utcnow()
    result.sort(key=lambda x: (
        severity_order(x["status"]),
        -(
            (now - x["last_seen_dt"]).total_seconds()
            if x["last_seen_dt"] is not None
            else float("inf")
        ),
    ))
    
    # Remove last_seen_dt from response
    for item in result:
        item.pop("last_seen_dt", None)
    
    return result[:limit]


@router.get("")
def devices_list(
    farm_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get list of devices with computed status.
    Later: filter by farm_id when we add org/field model.
    """
    devices = db.query(device_model.Device).all()
    result = []
    
    for device in devices:
        # Get device config (for lat/lon)
        config = (
            db.query(device_config_model.DeviceConfig)
            .filter(device_config_model.DeviceConfig.device_id == device.id)
            .first()
        )
        
        # Compute status
        status_info = compute_device_status(db, device, config)
        
        result.append({
            "id": device.id,
            "alias": device.name or device.esn or f"Device {device.id}",
            "esn": device.esn,
            "field": device.location or "Unassigned",
            "lat": config.lat if config else None,
            "lon": config.lon if config else None,
            "status": status_info["status"],
            "last_seen": status_info["last_seen"],
            "battery_hint": status_info["battery_hint"],
        })
    
    return result

