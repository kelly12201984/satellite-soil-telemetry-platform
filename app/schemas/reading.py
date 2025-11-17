# api/app/schemas/reading.py
from datetime import datetime
from pydantic import BaseModel


class ReadingBase(BaseModel):
    device_id: int
    message_id: int
    depth_cm: float
    moisture_pct: float | None = None
    temperature_c: float | None = None
    timestamp: datetime | None = None


class ReadingCreate(ReadingBase):
    pass


class ReadingRead(ReadingBase):
    id: int

    class Config:
        from_attributes = True
