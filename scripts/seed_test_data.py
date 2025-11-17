#!/usr/bin/env python3
"""
Seed realistic test data for soil probe readings.
Generates 30 days of data across multiple devices and depths.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, timezone
import random
from sqlalchemy.orm import Session

from api.app.db.session import SessionLocal
from api.app.models import device as device_model
from api.app.models import message as message_model
from api.app.models import reading as reading_model

# Realistic soil probe configurations
DEVICES = [
    {"esn": "0-5024242", "name": "Field A - North", "location": "Field A, North Section"},
    {"esn": "0-5024243", "name": "Field A - South", "location": "Field A, South Section"},
    {"esn": "0-5024244", "name": "Field B - Center", "location": "Field B, Center"},
]

# Sensor depths (cm) - typical multi-depth probe
DEPTHS = [10, 30, 60, 90]  # 10cm, 30cm, 60cm, 90cm

# Generate data for last N days
DAYS_BACK = 30
READINGS_PER_DAY = 6  # Every 4 hours


def generate_realistic_moisture(base_moisture: float, depth: int, time_of_day: int) -> float:
    """Generate realistic soil moisture based on depth and time."""
    # Deeper = more moisture (typically)
    depth_factor = 1.0 + (depth / 100.0) * 0.15
    
    # Morning/evening slightly higher (dew)
    time_factor = 1.0 + 0.05 * abs(time_of_day - 12) / 12.0
    
    # Add some realistic variation
    variation = random.uniform(-0.08, 0.08)
    
    moisture = base_moisture * depth_factor * time_factor + variation
    return max(10.0, min(45.0, moisture))  # Clamp to realistic range


def generate_realistic_temperature(base_temp: float, depth: int, hour: int) -> float:
    """Generate realistic soil temperature based on depth and time."""
    # Deeper = more stable (less daily variation)
    depth_stability = depth / 100.0  # Deeper = less variation
    
    # Daily cycle (warmer midday, cooler night)
    daily_cycle = 5.0 * (1.0 - depth_stability) * abs(hour - 12) / 12.0
    
    # Deeper = cooler (typically)
    depth_offset = -depth * 0.1
    
    temp = base_temp + depth_offset - daily_cycle + random.uniform(-1.5, 1.5)
    return max(15.0, min(35.0, temp))  # Clamp to realistic range


def seed_data(db: Session):
    """Seed the database with realistic test data."""
    print("🌱 Seeding test data...")
    
    # Create devices
    devices = {}
    for dev_config in DEVICES:
        dev = db.query(device_model.Device).filter_by(esn=dev_config["esn"]).first()
        if not dev:
            dev = device_model.Device(
                esn=dev_config["esn"],
                name=dev_config["name"],
                location=dev_config["location"],
            )
            db.add(dev)
            db.flush()
        devices[dev_config["esn"]] = dev
        print(f"  ✓ Device: {dev.name} ({dev.esn})")
    
    # Generate readings
    now = datetime.now(timezone.utc)
    base_moistures = {esn: random.uniform(18.0, 28.0) for esn in devices.keys()}
    base_temps = {esn: random.uniform(22.0, 26.0) for esn in devices.keys()}
    
    total_readings = 0
    start_date = now - timedelta(days=DAYS_BACK)
    
    for day_offset in range(DAYS_BACK):
        for reading_num in range(READINGS_PER_DAY):
            # Every 4 hours
            hour = (reading_num * 4) % 24
            timestamp = start_date + timedelta(days=day_offset, hours=hour)
            
            for esn, device in devices.items():
                # Create message for this reading batch
                msg = message_model.Message(
                    device_id=device.id,
                    message_id=f"seed-{day_offset}-{reading_num}-{esn}",
                    raw_payload=f"Generated test data for {timestamp.isoformat()}",
                    received_at=timestamp.replace(tzinfo=None),
                )
                db.add(msg)
                db.flush()
                
                # Create readings for each depth
                for depth in DEPTHS:
                    moisture = generate_realistic_moisture(
                        base_moistures[esn], depth, hour
                    )
                    temp = generate_realistic_temperature(
                        base_temps[esn], depth, hour
                    )
                    
                    reading = reading_model.Reading(
                        device_id=device.id,
                        message_id=msg.id,
                        depth_cm=float(depth),
                        moisture_pct=round(moisture, 2),
                        temperature_c=round(temp, 2),
                        timestamp=timestamp.replace(tzinfo=None),
                    )
                    db.add(reading)
                    total_readings += 1
    
    db.commit()
    print(f"\n✅ Seeded {len(devices)} devices, {total_readings} readings over {DAYS_BACK} days")
    print(f"   ({total_readings / len(devices) / DAYS_BACK:.1f} readings per device per day)")
    return len(devices), total_readings


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_data(db)
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

