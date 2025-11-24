# app/routers/farms.py
"""
Farms API endpoint - aggregates devices by location to create farm groups.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models import device as device_model
from app.models import device_config as device_config_model
from app.models import reading as reading_model
from app.services.status import compute_device_status, severity_order

router = APIRouter(prefix="/v1/farms", tags=["farms"])


def _get_worst_status(statuses: list[str]) -> str:
    """Get the worst status from a list of statuses."""
    priority = {'red': 0, 'amber': 1, 'stale': 2, 'offline': 3, 'gray': 4, 'blue': 5, 'green': 6}
    if not statuses:
        return 'gray'
    return min(statuses, key=lambda s: priority.get(s, 99))


@router.get("")
def farms_list(db: Session = Depends(get_db)):
    """
    Get list of farms (grouped by device location/field).
    Returns farm name, status, device count, last reading, and centroid coordinates.
    """
    devices = db.query(device_model.Device).all()

    # Group devices by location (field name)
    farms_dict: dict[str, dict] = {}

    for device in devices:
        # Get device config (for lat/lon and farm_id)
        config = (
            db.query(device_config_model.DeviceConfig)
            .filter(device_config_model.DeviceConfig.device_id == device.id)
            .first()
        )

        # Use location field for grouping, fall back to "Unassigned"
        farm_name = device.location or "Unassigned"

        # Initialize farm entry if needed
        if farm_name not in farms_dict:
            farms_dict[farm_name] = {
                "id": farm_name.lower().replace(" ", "-"),
                "name": farm_name,
                "device_count": 0,
                "statuses": [],
                "last_reading": None,
                "lats": [],
                "lons": [],
            }

        farm = farms_dict[farm_name]
        farm["device_count"] += 1

        # Compute status
        status_info = compute_device_status(db, device, config)
        farm["statuses"].append(status_info["status"])

        # Track last reading
        if status_info["last_seen"] is not None:
            if farm["last_reading"] is None or status_info["last_seen"] > farm["last_reading"]:
                farm["last_reading"] = status_info["last_seen"]

        # Collect coordinates for centroid
        if config and config.lat is not None and config.lon is not None:
            farm["lats"].append(config.lat)
            farm["lons"].append(config.lon)

    # Format output
    result = []
    for farm_name, farm in farms_dict.items():
        # Calculate centroid
        lat = sum(farm["lats"]) / len(farm["lats"]) if farm["lats"] else None
        lon = sum(farm["lons"]) / len(farm["lons"]) if farm["lons"] else None

        # Determine overall status (worst case)
        overall_status = _get_worst_status(farm["statuses"])

        # Count devices needing attention
        attention_count = sum(1 for s in farm["statuses"] if s in ['red', 'amber', 'stale', 'offline'])

        # Format last reading
        last_reading_str = None
        if farm["last_reading"]:
            delta = datetime.utcnow() - farm["last_reading"]
            minutes = int(delta.total_seconds() / 60)
            if minutes < 60:
                last_reading_str = f"{minutes}m ago"
            elif minutes < 1440:
                last_reading_str = f"{minutes // 60}h ago"
            else:
                last_reading_str = f"{minutes // 1440}d ago"

        result.append({
            "id": farm["id"],
            "name": farm["name"],
            "device_count": farm["device_count"],
            "status": overall_status,
            "attention_count": attention_count,
            "last_reading": last_reading_str,
            "last_reading_at": farm["last_reading"].isoformat() if farm["last_reading"] else None,
            "lat": lat,
            "lon": lon,
        })

    # Sort: farms with attention first, then by name
    result.sort(key=lambda f: (
        0 if f["status"] in ['red', 'amber'] else 1,
        f["name"]
    ))

    return result


@router.get("/{farm_id}")
def farm_detail(farm_id: str, db: Session = Depends(get_db)):
    """
    Get detailed info for a specific farm including all its devices.
    """
    devices = db.query(device_model.Device).all()

    # Find devices belonging to this farm
    farm_devices = []
    farm_name = None

    for device in devices:
        location = device.location or "Unassigned"
        location_id = location.lower().replace(" ", "-")

        if location_id == farm_id:
            farm_name = location

            # Get device config
            config = (
                db.query(device_config_model.DeviceConfig)
                .filter(device_config_model.DeviceConfig.device_id == device.id)
                .first()
            )

            # Compute status
            status_info = compute_device_status(db, device, config)

            # Get latest 30cm moisture
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

            farm_devices.append({
                "id": device.id,
                "alias": device.name or device.esn or f"Device {device.id}",
                "status": status_info["status"],
                "lat": config.lat if config else None,
                "lon": config.lon if config else None,
                "last_seen": status_info["last_seen"],
                "moisture30": round(latest_30cm, 1) if latest_30cm is not None else None,
                "battery_hint": status_info["battery_hint"],
            })

    if not farm_devices:
        return {"error": "Farm not found", "id": farm_id}

    # Sort devices by status priority
    farm_devices.sort(key=lambda d: severity_order(d["status"]))

    # Calculate farm-level stats
    lats = [d["lat"] for d in farm_devices if d["lat"] is not None]
    lons = [d["lon"] for d in farm_devices if d["lon"] is not None]

    return {
        "id": farm_id,
        "name": farm_name,
        "device_count": len(farm_devices),
        "devices": farm_devices,
        "lat": sum(lats) / len(lats) if lats else None,
        "lon": sum(lons) / len(lons) if lons else None,
    }
