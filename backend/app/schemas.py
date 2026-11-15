"""Pydantic schemas — the public contract of the REST API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import Priority, TripStatus


class Place(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class PlaceSuggestion(Place):
    country: str | None = None
    region: str | None = None


# ---------- Trips ----------


class TripBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    origin: Place
    destination: Place
    departure_at: datetime
    passengers: int = Field(default=1, ge=1, le=8)
    priority: Priority = Priority.BALANCED
    notes: str | None = Field(default=None, max_length=1000)


class TripCreate(TripBase):
    @model_validator(mode="after")
    def _different_places(self) -> "TripCreate":
        same = (
            abs(self.origin.lat - self.destination.lat) < 1e-6
            and abs(self.origin.lon - self.destination.lon) < 1e-6
        )
        if same:
            raise ValueError("Punkt startowy i docelowy muszą się różnić.")
        return self


class TripUpdate(BaseModel):
    """Partial update — every field is optional (PATCH semantics)."""

    title: str | None = Field(default=None, min_length=1, max_length=120)
    origin: Place | None = None
    destination: Place | None = None
    departure_at: datetime | None = None
    passengers: int | None = Field(default=None, ge=1, le=8)
    priority: Priority | None = None
    notes: str | None = Field(default=None, max_length=1000)


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    origin: Place
    destination: Place
    distance_km: float
    departure_at: datetime
    passengers: int
    priority: Priority
    notes: str | None
    status: TripStatus
    chosen_mode: str | None
    co2_kg: float | None
    co2_saved_kg: float | None
    eco_points: int
    created_at: datetime
    updated_at: datetime


class CompleteTripRequest(BaseModel):
    mode: str


# ---------- Comparison ----------


class Weather(BaseModel):
    temperature_c: float
    precipitation_probability: int
    precipitation_mm: float
    wind_kmh: float
    weather_code: int
    description: str
    icon: str
    bad_for_active_modes: bool


class ModeOption(BaseModel):
    mode: str
    label: str
    icon: str
    feasible: bool
    duration_min: int | None = None
    cost_pln: float | None = None
    co2_kg: float | None = None
    score: float | None = None
    note: str | None = None


class Comparison(BaseModel):
    trip_id: int
    distance_km: float
    weather: Weather | None
    options: list[ModeOption]
    recommended_mode: str | None
    reasons: list[str]
    car_baseline_co2_kg: float


class AiAdvice(BaseModel):
    source: str  # "ai" | "rules"
    summary: str
    tips: list[str]
    model: str | None = None


# ---------- Stats ----------


class Stats(BaseModel):
    total_trips: int
    completed_trips: int
    eco_points: int
    co2_saved_kg: float
    level: str
    next_level_at: int | None
    favourite_mode: str | None
