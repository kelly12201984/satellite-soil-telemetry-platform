# api/app/schemas/message.py
from datetime import datetime
from pydantic import BaseModel


class MessageBase(BaseModel):
    device_id: int
    message_id: str | None = None
    raw_payload: str | None = None


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: int
    received_at: datetime

    class Config:
        from_attributes = True
