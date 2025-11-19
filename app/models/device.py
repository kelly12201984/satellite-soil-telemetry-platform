# api/app/models/device.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Device(Base):
    """Represents one physical soil probe unit (linked to Globalstar ESN)."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    esn: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=True)
    location: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    config: Mapped["DeviceConfig"] = relationship("DeviceConfig", back_populates="device", uselist=False)
