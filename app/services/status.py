# api/app/services/status.py
"""
Status computation for irrigation alerts.

Implements Mode 1 (texture-aware) and Mode 2 (fallback) logic.
Priority: RED > AMBER > STALE > OFFLINE > BLUE > GREEN
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Literal, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from statistics import median

from app.settings import settings
from app.models import Device, DeviceConfig, Reading


StatusType = Literal["red", "amber", "green", "blue", "stale", "offline", "gray"]


def severity_order(status: StatusType) -> int:
    """Return numeric order for sorting (lower = higher priority)."""
    order = {
        "red": 0,
        "amber": 1,
        "stale": 2,
        "offline": 3,
        "blue": 4,
        "green": 5,
        "gray": 6,
    }
    return order.get(status, 99)


# Backward compatibility alias
_severity_order = severity_order


def _compute_mode2_status(vwc: float) -> StatusType:
    """Mode 2 (fallback): texture-agnostic bands."""
    if not settings.ALERTS_ENABLED:
        return "gray"
    if vwc <= settings.MOISTURE_RED_MAX:
        return "red"
    if vwc <= settings.MOISTURE_AMBER_MAX:
        return "amber"
    if vwc <= settings.MOISTURE_GREEN_MAX:
        return "green"
    if vwc >= settings.MOISTURE_BLUE_MIN:
        return "blue"
    return "green"  # between GREEN_MAX and BLUE_MIN (shouldn't happen with defaults)


def _compute_mode1_status(vwc: float, fc: float, pwp: float) -> StatusType:
    """Mode 1 (texture-aware): FC/PWP + MAD logic."""
    if not settings.ALERTS_ENABLED:
        return "gray"
    
    taw = fc - pwp  # Total available water
    if taw <= 0:
        return "gray"  # Invalid config
    
    depletion = max(0, min(taw, fc - vwc))  # Clamp to [0, TAW]
    depletion_pct = (depletion / taw * 100) if taw > 0 else 0
    
    # BLUE (saturated): VWC >= FC + 5 percentage points
    if vwc >= fc + 5.0:
        return "blue"
    
    # RED: Depletion >= 60% TAW
    if depletion_pct >= 60.0:
        return "red"
    
    # AMBER: 40-60% TAW depletion
    if depletion_pct >= 40.0:
        return "amber"
    
    # GREEN: 10-40% TAW depletion
    if depletion_pct >= 10.0:
        return "green"
    
    # Very low depletion (< 10%) - still green
    return "green"


def _get_rolling_window_vwc(
    db: Session, device_id: int, depth_cm: float, limit: int = 3
) -> Optional[float]:
    """Get median VWC from last N readings at this depth."""
    readings = (
        db.query(Reading.moisture_pct)
        .filter(
            Reading.device_id == device_id,
            Reading.depth_cm == depth_cm,
            Reading.moisture_pct.isnot(None),
        )
        .order_by(desc(Reading.timestamp))
        .limit(limit)
        .all()
    )
    
    if not readings:
        return None
    
    values = [r[0] for r in readings if r[0] is not None]
    if not values:
        return None
    
    return float(median(values))


def _get_last_seen(db: Session, device_id: int) -> Optional[datetime]:
    """Get timestamp of most recent reading for device."""
    result = (
        db.query(func.max(Reading.timestamp))
        .filter(Reading.device_id == device_id)
        .scalar()
    )
    return result


def _check_stale_offline(
    last_seen: Optional[datetime], expected_interval_min: int
) -> tuple[StatusType, bool]:
    """
    Check if device is STALE or OFFLINE.
    Returns (status, is_stale_or_offline).
    """
    if last_seen is None:
        # No readings ever
        hours_ago = float("inf")
    else:
        hours_ago = (datetime.utcnow() - last_seen).total_seconds() / 3600
    
    stale_threshold_hours = (expected_interval_min * settings.STALE_FACTOR) / 60.0
    
    if hours_ago > settings.OFFLINE_HOURS:
        return ("offline", True)
    if hours_ago > stale_threshold_hours:
        return ("stale", True)
    
    return ("green", False)  # Default, will be overridden by moisture status


def _check_spike(
    db: Session, device_id: int, depth_cm: float, current_vwc: float
) -> bool:
    """
    Check for rate-of-change spike (diagnostic only, doesn't change status).
    Returns True if spike detected.
    """
    # Get previous reading within ROC_WINDOW_MIN
    window_start = datetime.utcnow() - timedelta(minutes=settings.ROC_WINDOW_MIN)
    prev = (
        db.query(Reading.moisture_pct)
        .filter(
            Reading.device_id == device_id,
            Reading.depth_cm == depth_cm,
            Reading.moisture_pct.isnot(None),
            Reading.timestamp >= window_start,
            Reading.timestamp < datetime.utcnow(),
        )
        .order_by(desc(Reading.timestamp))
        .limit(2)
        .all()
    )
    
    if len(prev) < 2:
        return False  # Not enough data
    
    prev_vwc = prev[1][0]  # Second most recent
    if prev_vwc is None:
        return False
    
    change = abs(current_vwc - prev_vwc)
    return change > settings.ROC_SPIKE_PCT


def compute_device_status(
    db: Session, device: Device, device_config: Optional[DeviceConfig] = None
) -> dict:
    """
    Compute device status with worst-depth logic.
    
    Returns:
        {
            "status": "red" | "amber" | "green" | "blue" | "stale" | "offline" | "gray",
            "worst_depth_cm": float | None,
            "last_seen": datetime | None,
            "battery_hint": "ok" | "low" | "critical" | "unknown",
            "spike_detected": bool,
        }
    """
    # Get device config (or use defaults)
    if device_config is None:
        device_config = db.query(DeviceConfig).filter(DeviceConfig.device_id == device.id).first()
    
    expected_interval = (
        device_config.expected_interval_min if device_config else None
    ) or settings.EXPECTED_INTERVAL_MIN
    
    # Check last seen
    last_seen = _get_last_seen(db, device.id)
    stale_status, is_stale_or_offline = _check_stale_offline(last_seen, expected_interval)
    
    # If stale/offline, return early (these take priority over moisture)
    if is_stale_or_offline:
        return {
            "status": stale_status,
            "worst_depth_cm": None,
            "last_seen": last_seen,
            "battery_hint": "unknown",  # TODO: implement when battery data available
            "spike_detected": False,
        }
    
    # Get config for moisture status
    mode = device_config.mode if device_config else "fallback"
    fc = device_config.fc_vwc_pct if device_config else None
    pwp = device_config.pwp_vwc_pct if device_config else None
    
    use_mode1 = (
        mode == "texture_aware"
        and fc is not None
        and pwp is not None
        and fc > pwp
    )
    
    # Check all depths (10, 20, 30, 40, 50, 60 cm)
    depths = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    depth_statuses: dict[float, StatusType] = {}
    spike_detected = False
    
    for depth in depths:
        vwc = _get_rolling_window_vwc(db, device.id, depth)
        if vwc is None:
            continue
        
        # Check for spike (diagnostic only)
        if _check_spike(db, device.id, depth, vwc):
            spike_detected = True
        
        # Compute status for this depth
        if use_mode1:
            status = _compute_mode1_status(vwc, fc, pwp)
        else:
            status = _compute_mode2_status(vwc)
        
        depth_statuses[depth] = status
    
    if not depth_statuses:
        # No readings at any depth
        return {
            "status": "gray",
            "worst_depth_cm": None,
            "last_seen": last_seen,
            "battery_hint": "unknown",
            "spike_detected": False,
        }
    
    # Find worst depth (highest priority status)
    worst_depth = min(depth_statuses.items(), key=lambda x: _severity_order(x[1]))
    worst_status = worst_depth[1]
    worst_depth_cm = worst_depth[0]
    
    return {
        "status": worst_status,
        "worst_depth_cm": worst_depth_cm,
        "last_seen": last_seen,
        "battery_hint": "unknown",  # TODO: implement when battery data available
        "spike_detected": spike_detected,
    }

