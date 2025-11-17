# api/app/models/reading.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.app.db.base import Base


class Reading(Base):
    """Parsed measurement from a probe (per sensor depth)."""

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id", ondelete="CASCADE"), nullable=False)
    depth_cm: Mapped[float] = mapped_column(Float, nullable=False)
    moisture_pct: Mapped[float] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    message = relationship("Message", backref="readings")
    device = relationship("Device", backref="readings")
