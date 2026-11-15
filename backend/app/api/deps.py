"""FastAPI dependency providers — overridable in tests."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.trip_repository import TripRepository
from app.services.ai_advisor import Advisor, make_advisor
from app.services.geocoding import FallbackGeocoder, Geocoder, OfflineGeocoder, OpenMeteoGeocoder
from app.services.trip_service import TripService
from app.services.weather import OpenMeteoWeather, WeatherProvider


@lru_cache
def get_weather() -> WeatherProvider:
    return OpenMeteoWeather()


@lru_cache
def get_geocoder() -> Geocoder:
    return FallbackGeocoder(OpenMeteoGeocoder(), OfflineGeocoder())


@lru_cache
def get_advisor() -> Advisor:
    return make_advisor()


def get_trip_service(
    db: Session = Depends(get_db),
    weather: WeatherProvider = Depends(get_weather),
) -> TripService:
    return TripService(TripRepository(db), weather)
