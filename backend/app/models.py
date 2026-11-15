"""ORM models."""

from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Priority(StrEnum):
    BALANCED = "balanced"
    ECO = "eco"
    FAST = "fast"
    CHEAP = "cheap"


class TripStatus(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120))

    origin_name: Mapped[str] = mapped_column(String(120))
    origin_lat: Mapped[float] = mapped_column(Float)
    origin_lon: Mapped[float] = mapped_column(Float)
    destination_name: Mapped[str] = mapped_column(String(120))
    destination_lat: Mapped[float] = mapped_column(Float)
    destination_lon: Mapped[float] = mapped_column(Float)
    distance_km: Mapped[float] = mapped_column(Float)

    departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    passengers: Mapped[int] = mapped_column(Integer, default=1)
    priority: Mapped[str] = mapped_column(String(16), default=Priority.BALANCED)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(16), default=TripStatus.PLANNED, index=True)
    # Filled in when the trip is completed — persisted so stats stay stable
    # even if the emission factors change later.
    chosen_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    co2_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    co2_saved_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    eco_points: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
