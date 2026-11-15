"""Transport mode catalogue and the per-mode estimation engine.

All figures are rough averages for Poland (2025/26) — good enough to compare
options against each other, not to sell tickets. Emission factors are
per passenger-km (public transport) or per vehicle-km (car), based on typical
values published by the EEA / UK DESNZ conversion factors.
"""

import math
from dataclasses import dataclass

from app.schemas import ModeOption

# Straight-line distance is shorter than the real route; this is a common
# rule-of-thumb detour factor for road/rail networks.
ROUTE_DETOUR_FACTOR = 1.25

CAR_CO2_KG_PER_KM = 0.170  # per vehicle
CAR_COST_PLN_PER_KM = 0.80  # fuel + wear, per vehicle
CARPOOL_SEATS = 3  # realistic average occupancy of a shared ride


@dataclass(frozen=True)
class TransportMode:
    key: str
    label: str
    icon: str
    min_km: float
    max_km: float
    overhead_min: int  # waiting, walking to the stop, parking, airport security...
    co2_kg_per_km: float  # per passenger
    active: bool = False  # human-powered / open-air -> sensitive to weather

    def speed_kmh(self, distance_km: float) -> float:
        return _SPEEDS[self.key](distance_km)

    def cost_pln(self, distance_km: float, passengers: int) -> float:
        return _COSTS[self.key](distance_km, passengers)


_SPEEDS = {
    "walk": lambda d: 5,
    "bike": lambda d: 15,
    "scooter": lambda d: 16,
    "city_transit": lambda d: 18,
    "train": lambda d: 55 if d < 60 else 85,
    "coach": lambda d: 60,
    "car": lambda d: 30 if d < 15 else (55 if d < 60 else 85),
    "carpool": lambda d: 30 if d < 15 else (55 if d < 60 else 85),
    "plane": lambda d: 650,
}

_COSTS = {
    "walk": lambda d, p: 0.0,
    "bike": lambda d, p: 0.0,
    # Rental scooter: unlock + per-minute fee, every passenger rents their own.
    "scooter": lambda d, p: (1.0 + 0.89 * d / 16 * 60) * p,
    # Flat urban ticket (time ticket for longer rides).
    "city_transit": lambda d, p: (4.6 if d < 12 else 6.0) * p,
    "train": lambda d, p: max(6.0, 0.32 * d) * p,
    "coach": lambda d, p: max(15.0, 0.22 * d) * p,
    # The whole car costs the same no matter how many people sit inside.
    "car": lambda d, p: CAR_COST_PLN_PER_KM * d,
    # Shared ride: the driver's cost is split between all seats.
    "carpool": lambda d, p: CAR_COST_PLN_PER_KM * d / CARPOOL_SEATS * p,
    "plane": lambda d, p: max(180.0, 0.55 * d) * p,
}

MODES: dict[str, TransportMode] = {
    m.key: m
    for m in (
        TransportMode("walk", "Pieszo", "🚶", 0, 6, 0, 0.0, active=True),
        TransportMode("bike", "Rower", "🚲", 0, 25, 2, 0.0, active=True),
        TransportMode("scooter", "Hulajnoga", "🛴", 0, 8, 3, 0.035, active=True),
        TransportMode("city_transit", "Komunikacja miejska", "🚋", 1, 35, 8, 0.055),
        TransportMode("train", "Pociąg", "🚆", 15, 1200, 20, 0.035),
        TransportMode("coach", "Autokar", "🚌", 30, 1200, 15, 0.027),
        TransportMode("car", "Samochód", "🚗", 0, 2000, 7, CAR_CO2_KG_PER_KM),
        TransportMode("carpool", "Wspólny przejazd", "🤝", 20, 2000, 15, CAR_CO2_KG_PER_KM / CARPOOL_SEATS),
        TransportMode("plane", "Samolot", "✈️", 300, 20000, 150, 0.245),
    )
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def route_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return round(haversine_km(lat1, lon1, lat2, lon2) * ROUTE_DETOUR_FACTOR, 1)


def co2_for_mode(mode: TransportMode, distance_km: float, passengers: int) -> float:
    """Total CO2 (kg) for the whole group travelling with this mode."""
    if mode.key == "car":
        # One car carries up to 5 people — emissions are per vehicle.
        cars = math.ceil(passengers / 5)
        return round(CAR_CO2_KG_PER_KM * distance_km * cars, 2)
    return round(mode.co2_kg_per_km * distance_km * passengers, 2)


def car_baseline_co2(distance_km: float, passengers: int) -> float:
    """What the group would emit if everybody drove alone — the eco-points baseline."""
    return round(CAR_CO2_KG_PER_KM * distance_km * passengers, 2)


def estimate(mode: TransportMode, distance_km: float, passengers: int) -> ModeOption:
    if not (mode.min_km <= distance_km <= mode.max_km):
        reason = "za krótka trasa" if distance_km < mode.min_km else "za długa trasa"
        return ModeOption(mode=mode.key, label=mode.label, icon=mode.icon, feasible=False, note=reason)

    duration = mode.overhead_min + distance_km / mode.speed_kmh(distance_km) * 60
    return ModeOption(
        mode=mode.key,
        label=mode.label,
        icon=mode.icon,
        feasible=True,
        duration_min=max(1, round(duration)),
        cost_pln=round(mode.cost_pln(distance_km, passengers), 2),
        co2_kg=co2_for_mode(mode, distance_km, passengers),
    )


def estimate_all(distance_km: float, passengers: int) -> list[ModeOption]:
    return [estimate(m, distance_km, passengers) for m in MODES.values()]
