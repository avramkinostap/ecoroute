"""Gamification: eco-points for CO2 saved versus everyone driving alone."""

POINTS_PER_KG_SAVED = 1
ZERO_EMISSION_BONUS = 5

# (threshold, level name) — ascending.
LEVELS: list[tuple[int, str]] = [
    (0, "🌱 Nowicjusz"),
    (50, "🌿 Świadomy podróżnik"),
    (150, "🌳 Eko-odkrywca"),
    (400, "🌍 Strażnik klimatu"),
]


def points_for(co2_kg: float, baseline_kg: float) -> int:
    saved = max(0.0, baseline_kg - co2_kg)
    bonus = ZERO_EMISSION_BONUS if co2_kg == 0 else 0
    return round(saved * POINTS_PER_KG_SAVED) + bonus


def level_for(points: int) -> tuple[str, int | None]:
    """Return (current level name, points needed for the next level or None)."""
    current = LEVELS[0][1]
    next_at: int | None = None
    for threshold, name in LEVELS:
        if points >= threshold:
            current = name
        else:
            next_at = threshold
            break
    return current, next_at
