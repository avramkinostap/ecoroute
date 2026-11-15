"""Supporting endpoints: health, stats, transport modes, place search."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_geocoder, get_trip_service
from app.core.config import get_settings
from app.schemas import PlaceSuggestion, Stats
from app.services.geocoding import Geocoder
from app.services.transport import MODES
from app.services.trip_service import TripService

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    return {"status": "ok", "ai_enabled": bool(get_settings().anthropic_api_key)}


@router.get("/stats", response_model=Stats)
def stats(service: TripService = Depends(get_trip_service)):
    return service.stats()


@router.get("/modes")
def modes():
    return [
        {"mode": m.key, "label": m.label, "icon": m.icon, "min_km": m.min_km, "max_km": m.max_km}
        for m in MODES.values()
    ]


@router.get("/places", response_model=list[PlaceSuggestion])
async def search_places(
    q: str = Query(min_length=2, max_length=80),
    geocoder: Geocoder = Depends(get_geocoder),
):
    try:
        return await geocoder.search(q)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Wyszukiwarka miejsc jest chwilowo niedostępna.")
