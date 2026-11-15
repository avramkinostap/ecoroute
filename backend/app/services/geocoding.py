"""City / place search via the free Open-Meteo geocoding API."""

import logging
import unicodedata
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.schemas import PlaceSuggestion

log = logging.getLogger(__name__)


class Geocoder(Protocol):
    async def search(self, query: str, limit: int = 6) -> list[PlaceSuggestion]: ...


class OpenMeteoGeocoder:
    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        settings = get_settings()
        self._url = base_url or settings.geocoding_url
        self._timeout = timeout or settings.http_timeout_s

    async def search(self, query: str, limit: int = 6) -> list[PlaceSuggestion]:
        params = {"name": query, "count": limit, "language": "pl", "format": "json"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._url, params=params)
                resp.raise_for_status()
                results = resp.json().get("results") or []
        except httpx.HTTPError as exc:
            log.warning("Geocoding unavailable: %s", exc)
            raise
        return [
            PlaceSuggestion(
                name=r["name"],
                lat=r["latitude"],
                lon=r["longitude"],
                country=r.get("country"),
                region=r.get("admin1"),
            )
            for r in results
        ]


# Offline gazetteer — keeps the app usable without internet access.
_OFFLINE: list[tuple[str, float, float, str]] = [
    ("Warszawa", 52.2297, 21.0122, "Mazowieckie"),
    ("Kraków", 50.0647, 19.9450, "Małopolskie"),
    ("Wrocław", 51.1079, 17.0385, "Dolnośląskie"),
    ("Poznań", 52.4064, 16.9252, "Wielkopolskie"),
    ("Gdańsk", 54.3520, 18.6466, "Pomorskie"),
    ("Gdynia", 54.5189, 18.5305, "Pomorskie"),
    ("Łódź", 51.7592, 19.4560, "Łódzkie"),
    ("Szczecin", 53.4285, 14.5528, "Zachodniopomorskie"),
    ("Katowice", 50.2649, 19.0238, "Śląskie"),
    ("Lublin", 51.2465, 22.5684, "Lubelskie"),
    ("Białystok", 53.1325, 23.1688, "Podlaskie"),
    ("Bydgoszcz", 53.1235, 18.0084, "Kujawsko-pomorskie"),
    ("Toruń", 53.0138, 18.5984, "Kujawsko-pomorskie"),
    ("Rzeszów", 50.0412, 21.9991, "Podkarpackie"),
    ("Opole", 50.6751, 17.9213, "Opolskie"),
    ("Zielona Góra", 51.9356, 15.5062, "Lubuskie"),
    ("Olsztyn", 53.7784, 20.4801, "Warmińsko-mazurskie"),
    ("Kielce", 50.8661, 20.6286, "Świętokrzyskie"),
    ("Legnica", 51.2070, 16.1553, "Dolnośląskie"),
    ("Jelenia Góra", 50.9044, 15.7194, "Dolnośląskie"),
    ("Wałbrzych", 50.7714, 16.2843, "Dolnośląskie"),
    ("Oleśnica", 51.2097, 17.3803, "Dolnośląskie"),
    ("Wrocław Dworzec Główny", 51.0983, 17.0367, "Dolnośląskie"),
    ("Wrocław Rynek", 51.1100, 17.0320, "Dolnośląskie"),
    ("Wrocław Port Lotniczy", 51.1027, 16.8858, "Dolnośląskie"),
    ("Wrocław Krzyki", 51.0820, 17.0270, "Dolnośląskie"),
    ("Wrocław Psie Pole", 51.1467, 17.1148, "Dolnośląskie"),
    ("Berlin", 52.5200, 13.4050, "Niemcy"),
    ("Praga", 50.0755, 14.4378, "Czechy"),
    ("Lwów", 49.8397, 24.0297, "Ukraina"),
]


def _fold(text: str) -> str:
    text = text.lower().replace("ł", "l")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


class OfflineGeocoder:
    async def search(self, query: str, limit: int = 6) -> list[PlaceSuggestion]:
        q = _fold(query.strip())
        hits = [p for p in _OFFLINE if _fold(p[0]).startswith(q) or f" {q}" in _fold(p[0])]
        return [PlaceSuggestion(name=n, lat=la, lon=lo, region=r) for n, la, lo, r in hits[:limit]]


class FallbackGeocoder:
    """Online first, offline list when the network is unavailable."""

    def __init__(self, primary: Geocoder, fallback: Geocoder) -> None:
        self._primary, self._fallback = primary, fallback

    async def search(self, query: str, limit: int = 6) -> list[PlaceSuggestion]:
        try:
            results = await self._primary.search(query, limit)
            if results:
                return results
        except httpx.HTTPError:
            pass
        return await self._fallback.search(query, limit)
