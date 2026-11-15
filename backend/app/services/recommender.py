"""Scores transport options and picks the best one for the traveller.

Each feasible option gets a weighted, min-max-normalised cost over three
criteria (time, money, CO2). Weights depend on the trip priority. Open-air
modes (walk, bike, scooter) get a penalty when the forecast is bad — this is
the "weather-aware" part of the recommendation.
"""

import math
from dataclasses import dataclass

from app.models import Priority
from app.schemas import ModeOption, Weather
from app.services.transport import MODES

WEIGHTS: dict[Priority, tuple[float, float, float]] = {
    #                   time  cost  co2
    Priority.BALANCED: (0.40, 0.30, 0.30),
    Priority.ECO: (0.20, 0.15, 0.65),
    Priority.FAST: (0.70, 0.15, 0.15),
    Priority.CHEAP: (0.20, 0.65, 0.15),
}

BAD_WEATHER_PENALTY = 0.6

PRIORITY_LABELS = {
    Priority.BALANCED: "zrównoważony",
    Priority.ECO: "ekologiczny",
    Priority.FAST: "najszybszy",
    Priority.CHEAP: "najtańszy",
}


@dataclass
class Recommendation:
    options: list[ModeOption]
    recommended_mode: str | None
    reasons: list[str]


def _normalise(values: list[float]) -> list[float]:
    """Min-max on a log scale, so one extreme option (e.g. a plane's CO2)
    does not squash the differences between all the others."""
    values = [math.log1p(v) for v in values]
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def recommend(
    options: list[ModeOption],
    priority: Priority,
    weather: Weather | None,
    car_baseline_co2_kg: float,
) -> Recommendation:
    feasible = [o for o in options if o.feasible]
    if not feasible:
        return Recommendation(options, None, ["Brak dostępnych środków transportu dla tej trasy."])

    w_time, w_cost, w_co2 = WEIGHTS[priority]
    times = _normalise([float(o.duration_min) for o in feasible])
    costs = _normalise([o.cost_pln for o in feasible])
    co2s = _normalise([o.co2_kg for o in feasible])
    bad_weather = bool(weather and weather.bad_for_active_modes)

    for opt, t, c, e in zip(feasible, times, costs, co2s):
        raw = w_time * t + w_cost * c + w_co2 * e
        if bad_weather and MODES[opt.mode].active:
            raw += BAD_WEATHER_PENALTY
            opt.note = "niekorzystna pogoda"
        # Present as a 0–100 "match" score where higher is better.
        opt.score = round(max(0.0, 1.0 - raw) * 100, 1)

    best = max(feasible, key=lambda o: o.score)
    reasons = _explain(best, feasible, priority, weather, car_baseline_co2_kg)
    return Recommendation(options, best.mode, reasons)


def _explain(
    best: ModeOption,
    feasible: list[ModeOption],
    priority: Priority,
    weather: Weather | None,
    baseline: float,
) -> list[str]:
    reasons = [f"Priorytet podróży: {PRIORITY_LABELS[priority]}."]
    if best.duration_min == min(o.duration_min for o in feasible):
        reasons.append("To najszybsza z dostępnych opcji.")
    if best.cost_pln == min(o.cost_pln for o in feasible):
        reasons.append("To najtańsza z dostępnych opcji.")
    if best.co2_kg == 0:
        reasons.append("Zero emisji CO₂ — maksimum eko-punktów.")
    saved = round(baseline - best.co2_kg, 2)
    if saved > 0:
        reasons.append(f"Oszczędzasz {saved} kg CO₂ względem jazdy samochodem w pojedynkę.")
    if weather:
        if weather.bad_for_active_modes:
            reasons.append(
                f"Prognoza: {weather.description.lower()}, {weather.temperature_c}°C — "
                "rower, hulajnoga i spacer zostały ocenione niżej."
            )
        elif MODES[best.mode].active:
            reasons.append(f"Prognoza sprzyja: {weather.description.lower()}, {weather.temperature_c}°C.")
    return reasons
