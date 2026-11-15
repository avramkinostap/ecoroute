"""Data-access layer for trips — the only place that talks SQL."""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Trip, TripStatus


class TripRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self, status: TripStatus | None = None) -> list[Trip]:
        # Upcoming (planned) trips first, then history; chronological within each group.
        planned_first = case((Trip.status == TripStatus.PLANNED, 0), else_=1)
        stmt = select(Trip).order_by(planned_first, Trip.departure_at.asc())
        if status:
            stmt = stmt.where(Trip.status == status)
        return list(self._db.scalars(stmt))

    def get(self, trip_id: int) -> Trip | None:
        return self._db.get(Trip, trip_id)

    def add(self, trip: Trip) -> Trip:
        self._db.add(trip)
        self._db.commit()
        self._db.refresh(trip)
        return trip

    def save(self, trip: Trip) -> Trip:
        self._db.commit()
        self._db.refresh(trip)
        return trip

    def delete(self, trip: Trip) -> None:
        self._db.delete(trip)
        self._db.commit()

    def totals(self) -> tuple[int, int, int, float]:
        """(all trips, completed trips, eco points, CO2 saved kg)."""
        total = self._db.scalar(select(func.count(Trip.id))) or 0
        completed, points, saved = self._db.execute(
            select(
                func.count(Trip.id),
                func.coalesce(func.sum(Trip.eco_points), 0),
                func.coalesce(func.sum(Trip.co2_saved_kg), 0.0),
            ).where(Trip.status == TripStatus.COMPLETED)
        ).one()
        return total, completed, int(points), float(saved)

    def favourite_mode(self) -> str | None:
        stmt = (
            select(Trip.chosen_mode, func.count(Trip.id).label("n"))
            .where(Trip.status == TripStatus.COMPLETED)
            .group_by(Trip.chosen_mode)
            .order_by(func.count(Trip.id).desc())
            .limit(1)
        )
        row = self._db.execute(stmt).first()
        return row[0] if row else None
