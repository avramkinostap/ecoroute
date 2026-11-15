"""AI travel advisor.

Turns the already-computed comparison into a short, human, practical advice
(what to take, what to watch out for). The LLM gets *only* our computed data
and is told not to invent numbers — the deterministic engine decides, the
model explains. Without an API key (or on any error) a rule-based advisor
produces the same shape of answer, so the feature always works.
"""

import json
import logging
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.models import Trip
from app.schemas import AiAdvice, Comparison
from app.services.transport import MODES

log = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """Jesteś „EcoRoute Doradcą” — zwięzłym, życzliwym asystentem mobilności.
Dostajesz dane JSON o planowanej podróży: trasę, liczbę osób, priorytet, prognozę
pogody oraz porównanie środków transportu wyliczone przez system (czas, koszt, CO₂,
wynik dopasowania) i rekomendację systemu.

Zasady:
1. Opieraj się WYŁĄCZNIE na przekazanych danych. Nie wymyślaj liczb, linii, rozkładów
   ani cen. Jeśli podajesz liczbę, musi pochodzić z danych.
2. Nie zmieniaj rekomendacji systemu — wyjaśnij ją. Możesz wskazać jedną alternatywę,
   jeśli ma wyraźną przewagę w jakimś kryterium.
3. Uwzględnij pogodę (ubiór, parasol, ryzyko opóźnień) i porę wyjazdu.
4. Pisz po polsku, w drugiej osobie, rzeczowo, bez lania wody.
5. Odpowiedz WYŁĄCZNIE poprawnym JSON-em, bez markdownu, w formacie:
   {"summary": "1–2 zdania", "tips": ["krótka wskazówka", "..."]}
   Maksymalnie 3 wskazówki, każda do 140 znaków."""


class Advisor(Protocol):
    async def advise(self, trip: Trip, comparison: Comparison) -> AiAdvice: ...


def build_context(trip: Trip, comparison: Comparison) -> dict:
    """The exact payload the model sees — small, structured and factual."""
    return {
        "trasa": {
            "z": trip.origin_name,
            "do": trip.destination_name,
            "dystans_km": trip.distance_km,
            "wyjazd": trip.departure_at.isoformat(),
            "osoby": trip.passengers,
            "priorytet": trip.priority,
            "notatki": trip.notes,
        },
        "pogoda": comparison.weather.model_dump() if comparison.weather else None,
        "opcje": [
            {
                "srodek": o.label,
                "czas_min": o.duration_min,
                "koszt_pln": o.cost_pln,
                "co2_kg": o.co2_kg,
                "dopasowanie": o.score,
                "uwaga": o.note,
            }
            for o in comparison.options
            if o.feasible
        ],
        "rekomendacja_systemu": MODES[comparison.recommended_mode].label if comparison.recommended_mode else None,
        "uzasadnienie_systemu": comparison.reasons,
    }


class RuleBasedAdvisor:
    """Deterministic fallback — no network, no key."""

    async def advise(self, trip: Trip, comparison: Comparison) -> AiAdvice:
        if not comparison.recommended_mode:
            return AiAdvice(source="rules", summary="Nie znaleziono pasującego środka transportu.", tips=[])

        best = next(o for o in comparison.options if o.mode == comparison.recommended_mode)
        cost = "bez kosztów" if best.cost_pln == 0 else f"{best.cost_pln:.2f} zł".replace(".", ",")
        summary = (
            f"Na trasie {trip.origin_name} → {trip.destination_name} ({trip.distance_km} km) "
            f"najlepiej wypada: {best.label.lower()} — ok. {best.duration_min} min, {cost}, "
            f"{best.co2_kg:g} kg CO₂."
        )
        buffer = 10 if best.duration_min < 60 else 30
        tips: list[str] = [
            f"Zaplanuj ok. {best.duration_min + buffer} min na całą drogę ({buffer} min zapasu na nieprzewidziane)."
        ]
        w = comparison.weather
        if w:
            if w.precipitation_probability >= 50:
                tips.append(f"Szansa opadów {w.precipitation_probability}% — weź parasol lub kurtkę przeciwdeszczową.")
            if w.temperature_c <= 3:
                tips.append(f"Będzie zimno ({w.temperature_c}°C) — ubierz się warstwowo.")
            if w.wind_kmh >= 30:
                tips.append(f"Silny wiatr ({w.wind_kmh} km/h) — na rowerze licz się z wolniejszą jazdą.")
        if best.mode in {"train", "coach", "plane"}:
            tips.append("Kup bilet z wyprzedzeniem — zwykle wychodzi taniej.")
        if best.mode == "carpool":
            tips.append("Ustal z kierowcą punkt odbioru i podział kosztów przed wyjazdem.")
        if best.mode == "city_transit":
            tips.append("Sprawdź aktualny rozkład w aplikacji przewoźnika tuż przed wyjściem.")
        if MODES[best.mode].active and w and not w.bad_for_active_modes:
            tips.append("Dobry dzień na aktywny transport — zabierz wodę.")
        return AiAdvice(source="rules", summary=summary, tips=tips[:3])


class ClaudeAdvisor:
    def __init__(self, api_key: str, model: str, fallback: Advisor, timeout: float = 20.0) -> None:
        self._api_key = api_key
        self._model = model
        self._fallback = fallback
        self._timeout = timeout

    async def advise(self, trip: Trip, comparison: Comparison) -> AiAdvice:
        payload = {
            "model": self._model,
            "max_tokens": 400,
            "temperature": 0.4,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": json.dumps(build_context(trip, comparison), ensure_ascii=False)}
            ],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(ANTHROPIC_URL, json=payload, headers=headers)
                resp.raise_for_status()
            text = "".join(b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text")
            data = parse_model_json(text)
            return AiAdvice(
                source="ai",
                summary=str(data["summary"]).strip(),
                tips=[str(t).strip() for t in data.get("tips", [])][:3],
                model=self._model,
            )
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            log.warning("AI advisor failed, using rules: %s", exc)
            return await self._fallback.advise(trip, comparison)


def parse_model_json(text: str) -> dict:
    """Extract the JSON object even if the model wrapped it in prose or ``` fences."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object in model output")
    data = json.loads(text[start : end + 1])
    if not isinstance(data, dict) or "summary" not in data:
        raise ValueError("Unexpected JSON shape")
    return data


def make_advisor() -> Advisor:
    settings = get_settings()
    rules = RuleBasedAdvisor()
    if settings.anthropic_api_key:
        return ClaudeAdvisor(settings.anthropic_api_key, settings.ai_model, fallback=rules)
    return rules
