# api/app/routers/metrics.py
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from api.app.db.session import get_db
from api.app.models import reading as reading_model
from api.app.models import device as device_model
from api.app.models import device_config as device_config_model
from api.app.services.status import compute_device_status

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


def _downsample_readings(readings: List[dict], max_points: int = 800) -> List[dict]:
    """
    Simple downsampling: take evenly spaced points.
    For production, use LTTB (Largest-Triangle-Three-Buckets) algorithm.
    """
    if len(readings) <= max_points:
        return readings
    
    step = len(readings) / max_points
    return [readings[int(i * step)] for i in range(max_points)]


def _should_aggregate_daily(from_dt: datetime, to_dt: datetime) -> bool:
    """Return True if range > 90 days."""
    return (to_dt - from_dt).days > 90


@router.get("/summary")
def metrics_summary(
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
    device_ids: Optional[List[int]] = Query(None, alias="device_ids[]"),
    depths: Optional[List[float]] = Query(None, alias="depths[]"),
    db: Session = Depends(get_db),
):
    """Get summary metrics for the selected time range and filters."""
    query = db.query(reading_model.Reading).join(device_model.Device)
    
    # Time filter
    if from_dt:
        try:
            from_date = datetime.fromisoformat(from_dt.replace("Z", "+00:00"))
            query = query.filter(reading_model.Reading.timestamp >= from_date)
        except Exception:
            pass
    
    if to_dt:
        try:
            to_date = datetime.fromisoformat(to_dt.replace("Z", "+00:00"))
            query = query.filter(reading_model.Reading.timestamp <= to_date)
        except Exception:
            pass
    
    # Device filter
    if device_ids:
        query = query.filter(reading_model.Reading.device_id.in_(device_ids))
    
    # Depth filter
    if depths:
        query = query.filter(reading_model.Reading.depth_cm.in_(depths))
    
    readings = query.all()
    
    if not readings:
        return {
            "avg_moisture": None,
            "avg_temp": None,
            "devices_needing_attention": [],
            "last_reading_at": None,
        }
    
    # Calculate averages
    moistures = [r.moisture_pct for r in readings if r.moisture_pct is not None]
    temps = [r.temperature_c for r in readings if r.temperature_c is not None]
    
    avg_moisture = sum(moistures) / len(moistures) if moistures else None
    avg_temp = sum(temps) / len(temps) if temps else None
    
    # Last reading timestamp
    last_reading = max(readings, key=lambda r: r.timestamp)
    last_reading_at = last_reading.timestamp.isoformat() if last_reading else None
    
    # Devices needing attention (RED or AMBER status)
    # Get unique device IDs from readings
    device_ids_in_range = list(set(r.device_id for r in readings))
    attention_devices = []
    
    for device_id in device_ids_in_range:
        device = db.query(device_model.Device).filter_by(id=device_id).first()
        if not device:
            continue
        
        # Get device config
        config = (
            db.query(device_config_model.DeviceConfig)
            .filter(device_config_model.DeviceConfig.device_id == device.id)
            .first()
        )
        
        # Compute status
        status_info = compute_device_status(db, device, config)
        status = status_info["status"]
        
        # Include if RED or AMBER
        if status in ("red", "amber"):
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
            
            attention_devices.append({
                "device_id": device_id,
                "alias": device.name or device.esn or f"Device {device_id}",
                "avg_moisture_30cm": round(latest_30cm, 1) if latest_30cm is not None else None,
                "status": status,
            })
    
    return {
        "avg_moisture": round(avg_moisture, 2) if avg_moisture else None,
        "avg_temp": round(avg_temp, 2) if avg_temp else None,
        "devices_needing_attention": attention_devices,
        "last_reading_at": last_reading_at,
    }


@router.get("/moisture-series")
def moisture_series(
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
    device_ids: Optional[List[int]] = Query(None, alias="device_ids[]"),
    depths: Optional[List[float]] = Query(None, alias="depths[]"),
    max_points: int = Query(800, alias="max_points"),
    db: Session = Depends(get_db),
):
    """Get moisture time series data, downsampled to max_points."""
    query = db.query(
        reading_model.Reading.device_id,
        reading_model.Reading.depth_cm,
        reading_model.Reading.timestamp,
        reading_model.Reading.moisture_pct,
        device_model.Device.name.label("device_name"),
    ).join(device_model.Device)
    
    # Filters
    if from_dt:
        try:
            from_date = datetime.fromisoformat(from_dt.replace("Z", "+00:00"))
            query = query.filter(reading_model.Reading.timestamp >= from_date)
        except Exception:
            pass
    
    if to_dt:
        try:
            to_date = datetime.fromisoformat(to_dt.replace("Z", "+00:00"))
            query = query.filter(reading_model.Reading.timestamp <= to_date)
        except Exception:
            pass
    
    if device_ids:
        query = query.filter(reading_model.Reading.device_id.in_(device_ids))
    
    if depths:
        query = query.filter(reading_model.Reading.depth_cm.in_(depths))
    
    query = query.order_by(reading_model.Reading.timestamp)
    rows = query.all()
    
    # Group by device_id + depth_cm
    series = {}
    for row in rows:
        if row.moisture_pct is None:
            continue
        key = f"{row.device_id}-{row.depth_cm}"
        if key not in series:
            series[key] = {
                "device_id": row.device_id,
                "depth_cm": row.depth_cm,
                "device_name": row.device_name or f"Device {row.device_id}",
                "points": [],
            }
        series[key]["points"].append({
            "t": row.timestamp.isoformat(),
            "v": round(row.moisture_pct, 2),
        })
    
    # Downsample each series
    result = []
    for key, data in series.items():
        if len(data["points"]) > max_points:
            data["points"] = _downsample_readings(data["points"], max_points)
        result.append({
            "device_id": data["device_id"],
            "depth_cm": data["depth_cm"],
            "device_name": data["device_name"],
            "points": data["points"],
        })
    
    return result


@router.get("/temp-series")
def temp_series(
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
    device_ids: Optional[List[int]] = Query(None, alias="device_ids[]"),
    max_points: int = Query(800, alias="max_points"),
    db: Session = Depends(get_db),
):
    """Get temperature time series data, downsampled to max_points."""
    query = db.query(
        reading_model.Reading.device_id,
        reading_model.Reading.timestamp,
        reading_model.Reading.temperature_c,
        device_model.Device.name.label("device_name"),
    ).join(device_model.Device)
    
    # Filters
    if from_dt:
        try:
            from_date = datetime.fromisoformat(from_dt.replace("Z", "+00:00"))
            query = query.filter(reading_model.Reading.timestamp >= from_date)
        except Exception:
            pass
    
    if to_dt:
        try:
            to_date = datetime.fromisoformat(to_dt.replace("Z", "+00:00"))
            query = query.filter(reading_model.Reading.timestamp <= to_date)
        except Exception:
            pass
    
    if device_ids:
        query = query.filter(reading_model.Reading.device_id.in_(device_ids))
    
    query = query.order_by(reading_model.Reading.timestamp)
    rows = query.all()
    
    # Group by device_id
    series = {}
    for row in rows:
        if row.temperature_c is None:
            continue
        key = str(row.device_id)
        if key not in series:
            series[key] = {
                "device_id": row.device_id,
                "device_name": row.device_name or f"Device {row.device_id}",
                "points": [],
            }
        series[key]["points"].append({
            "t": row.timestamp.isoformat(),
            "v": round(row.temperature_c, 2),
        })
    
    # Downsample each series
    result = []
    for key, data in series.items():
        if len(data["points"]) > max_points:
            data["points"] = _downsample_readings(data["points"], max_points)
        result.append({
            "device_id": data["device_id"],
            "device_name": data["device_name"],
            "points": data["points"],
        })
    
    return result

