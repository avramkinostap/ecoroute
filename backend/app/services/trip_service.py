"""Business logic for trips — orchestrates repository and domain services."""

from app.models import Priority, Trip, TripStatus
from app.repositories.trip_repository import TripRepository
from app.schemas import Comparison, Place, Stats, TripCreate, TripRead, TripUpdate
from app.services import eco_points
from app.services.recommender import recommend
from app.services.transport import MODES, car_baseline_co2, estimate, estimate_all, route_distance_km
from app.services.weather import WeatherProvider


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class DomainValidationError(Exception):
    pass


def to_read(trip: Trip) -> TripRead:
    return TripRead(
        id=trip.id,
        title=trip.title,
        origin=Place(name=trip.origin_name, lat=trip.origin_lat, lon=trip.origin_lon),
        destination=Place(name=trip.destination_name, lat=trip.destination_lat, lon=trip.destination_lon),
        distance_km=trip.distance_km,
        departure_at=trip.departure_at,
        passengers=trip.passengers,
        priority=trip.priority,
        notes=trip.notes,
        status=trip.status,
        chosen_mode=trip.chosen_mode,
        co2_kg=trip.co2_kg,
        co2_saved_kg=trip.co2_saved_kg,
        eco_points=trip.eco_points,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
    )


def _apply_places(trip: Trip, origin: Place, destination: Place) -> None:
    trip.origin_name, trip.origin_lat, trip.origin_lon = origin.name, origin.lat, origin.lon
    trip.destination_name, trip.destination_lat, trip.destination_lon = (
        destination.name,
        destination.lat,
        destination.lon,
    )
    trip.distance_km = route_distance_km(origin.lat, origin.lon, destination.lat, destination.lon)
    if trip.distance_km <= 0:
        raise DomainValidationError("Punkt startowy i docelowy muszą się różnić.")


class TripService:
    def __init__(self, repo: TripRepository, weather: WeatherProvider) -> None:
        self._repo = repo
        self._weather = weather

    # ----- CRUD -----

    def list(self, status: TripStatus | None = None) -> list[Trip]:
        return self._repo.list(status)

    def get(self, trip_id: int) -> Trip:
        trip = self._repo.get(trip_id)
        if trip is None:
            raise NotFoundError(f"Podróż {trip_id} nie istnieje.")
        return trip

    def create(self, data: TripCreate) -> Trip:
        trip = Trip(
            title=data.title.strip(),
            departure_at=data.departure_at,
            passengers=data.passengers,
            priority=data.priority,
            notes=data.notes,
            status=TripStatus.PLANNED,
        )
        _apply_places(trip, data.origin, data.destination)
        return self._repo.add(trip)

    def update(self, trip_id: int, data: TripUpdate) -> Trip:
        trip = self.get(trip_id)
        if trip.status == TripStatus.COMPLETED:
            raise ConflictError("Zakończonej podróży nie można edytować.")

        changes = data.model_dump(exclude_unset=True)
        for field in ("title", "departure_at", "passengers", "priority", "notes"):
            if field in changes and changes[field] is not None:
                setattr(trip, field, changes[field])
        if data.origin or data.destination:
            origin = data.origin or Place(name=trip.origin_name, lat=trip.origin_lat, lon=trip.origin_lon)
            destination = data.destination or Place(
                name=trip.destination_name, lat=trip.destination_lat, lon=trip.destination_lon
            )
            _apply_places(trip, origin, destination)
        return self._repo.save(trip)

    def delete(self, trip_id: int) -> None:
        self._repo.delete(self.get(trip_id))

    # ----- Domain actions -----

    async def compare(self, trip_id: int) -> Comparison:
        trip = self.get(trip_id)
        weather = await self._weather.forecast(trip.origin_lat, trip.origin_lon, trip.departure_at)
        baseline = car_baseline_co2(trip.distance_km, trip.passengers)
        result = recommend(
            estimate_all(trip.distance_km, trip.passengers),
            Priority(trip.priority),
            weather,
            baseline,
        )
        return Comparison(
            trip_id=trip.id,
            distance_km=trip.distance_km,
            weather=weather,
            options=result.options,
            recommended_mode=result.recommended_mode,
            reasons=result.reasons,
            car_baseline_co2_kg=baseline,
        )

    def complete(self, trip_id: int, mode_key: str) -> Trip:
        trip = self.get(trip_id)
        if trip.status == TripStatus.COMPLETED:
            raise ConflictError("Ta podróż jest już zakończona.")
        mode = MODES.get(mode_key)
        if mode is None:
            raise DomainValidationError(f"Nieznany środek transportu: {mode_key}.")
        option = estimate(mode, trip.distance_km, trip.passengers)
        if not option.feasible:
            raise DomainValidationError(f"{mode.label}: {option.note}.")

        baseline = car_baseline_co2(trip.distance_km, trip.passengers)
        trip.status = TripStatus.COMPLETED
        trip.chosen_mode = mode.key
        trip.co2_kg = option.co2_kg
        trip.co2_saved_kg = round(max(0.0, baseline - option.co2_kg), 2)
        trip.eco_points = eco_points.points_for(option.co2_kg, baseline)
        return self._repo.save(trip)

    def stats(self) -> Stats:
        total, completed, points, saved = self._repo.totals()
        level, next_at = eco_points.level_for(points)
        return Stats(
            total_trips=total,
            completed_trips=completed,
            eco_points=points,
            co2_saved_kg=round(saved, 2),
            level=level,
            next_level_at=next_at,
            favourite_mode=self._repo.favourite_mode(),
        )
