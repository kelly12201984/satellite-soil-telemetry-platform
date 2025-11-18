# api/app/schemas/device.py
from datetime import datetime
from pydantic import BaseModel


class DeviceBase(BaseModel):
    esn: str
    name: str | None = None
    location: str | None = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating device name and/or location"""
    name: str | None = None
    location: str | None = None


class DeviceRead(DeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # replaces orm_mode in Pydantic v2
