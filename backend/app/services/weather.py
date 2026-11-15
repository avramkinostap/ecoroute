"""Weather forecast for the departure time, via the free Open-Meteo API.

The service never raises on network problems — a missing forecast simply
means the recommendation ignores the weather.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.schemas import Weather

log = logging.getLogger(__name__)

FORECAST_HORIZON_DAYS = 15

# WMO weather interpretation codes -> (description, icon)
_WMO: dict[int, tuple[str, str]] = {
    0: ("Bezchmurnie", "☀️"),
    1: ("Przeważnie słonecznie", "🌤️"),
    2: ("Częściowe zachmurzenie", "⛅"),
    3: ("Pochmurno", "☁️"),
    45: ("Mgła", "🌫️"),
    48: ("Mgła osadzająca szadź", "🌫️"),
    51: ("Lekka mżawka", "🌦️"),
    53: ("Mżawka", "🌦️"),
    55: ("Gęsta mżawka", "🌧️"),
    61: ("Słaby deszcz", "🌦️"),
    63: ("Deszcz", "🌧️"),
    65: ("Ulewa", "🌧️"),
    66: ("Marznący deszcz", "🌧️"),
    67: ("Silny marznący deszcz", "🌧️"),
    71: ("Słaby śnieg", "🌨️"),
    73: ("Śnieg", "🌨️"),
    75: ("Intensywny śnieg", "❄️"),
    77: ("Ziarna śniegu", "🌨️"),
    80: ("Przelotny deszcz", "🌦️"),
    81: ("Przelotne opady", "🌧️"),
    82: ("Gwałtowne ulewy", "⛈️"),
    85: ("Przelotny śnieg", "🌨️"),
    86: ("Intensywne opady śniegu", "❄️"),
    95: ("Burza", "⛈️"),
    96: ("Burza z gradem", "⛈️"),
    99: ("Silna burza z gradem", "⛈️"),
}


def is_bad_for_active_modes(w_temp: float, w_prob: int, w_mm: float, w_wind: float, code: int) -> bool:
    return (
        w_prob >= 60
        or w_mm >= 0.5
        or w_temp <= 0
        or w_temp >= 32
        or w_wind >= 35
        or code >= 95
    )


def build_weather(temp: float, prob: int, mm: float, wind: float, code: int) -> Weather:
    description, icon = _WMO.get(code, ("Brak opisu", "🌡️"))
    return Weather(
        temperature_c=round(temp, 1),
        precipitation_probability=int(prob),
        precipitation_mm=round(mm, 1),
        wind_kmh=round(wind, 1),
        weather_code=code,
        description=description,
        icon=icon,
        bad_for_active_modes=is_bad_for_active_modes(temp, prob, mm, wind, code),
    )


class WeatherProvider(Protocol):
    async def forecast(self, lat: float, lon: float, at: datetime) -> Weather | None: ...


class OpenMeteoWeather:
    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        settings = get_settings()
        self._url = base_url or settings.weather_url
        self._timeout = timeout or settings.http_timeout_s

    async def forecast(self, lat: float, lon: float, at: datetime) -> Weather | None:
        at_utc = at.astimezone(timezone.utc) if at.tzinfo else at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if not (now - timedelta(days=1) <= at_utc <= now + timedelta(days=FORECAST_HORIZON_DAYS)):
            return None  # outside the forecast window

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability,precipitation,wind_speed_10m,weather_code",
            "timezone": "UTC",
            "start_date": at_utc.date().isoformat(),
            "end_date": at_utc.date().isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._url, params=params)
                resp.raise_for_status()
                hourly = resp.json()["hourly"]
            idx = min(at_utc.hour, len(hourly["time"]) - 1)
            return build_weather(
                temp=hourly["temperature_2m"][idx],
                prob=hourly["precipitation_probability"][idx] or 0,
                mm=hourly["precipitation"][idx] or 0.0,
                wind=hourly["wind_speed_10m"][idx],
                code=hourly["weather_code"][idx],
            )
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            log.warning("Weather unavailable: %s", exc)
            return None
