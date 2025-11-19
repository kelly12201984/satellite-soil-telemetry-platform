# api/app/routers/readings.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import reading as reading_model
from app.models import device as device_model
from app.models import message as message_model

router = APIRouter(prefix="/v1/readings", tags=["readings"])

@router.get("/latest")
def latest_readings(limit: int = 50, db: Session = Depends(get_db)):
    """
    Return the most recent readings with device + message context.
    """
    q = (
        db.query(
            reading_model.Reading.id.label("reading_id"),
            reading_model.Reading.timestamp,
            reading_model.Reading.depth_cm,
            reading_model.Reading.moisture_pct,
            reading_model.Reading.temperature_c,
            device_model.Device.id.label("device_id"),
            device_model.Device.esn,
            device_model.Device.name.label("device_name"),
            message_model.Message.message_id.label("message_external_id"),
        )
        .join(device_model.Device, device_model.Device.id == reading_model.Reading.device_id)
        .join(message_model.Message, message_model.Message.id == reading_model.Reading.message_id)
        .order_by(reading_model.Reading.timestamp.desc())
        .limit(limit)
    )
    rows = [dict(r._mapping) for r in q.all()]
    return {"count": len(rows), "items": rows}
