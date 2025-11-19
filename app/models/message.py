# api/app/models/message.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Message(Base):
    """One incoming Globalstar envelope or push message."""

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[str] = mapped_column(String(64), index=True)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    device = relationship("Device", backref="messages")
