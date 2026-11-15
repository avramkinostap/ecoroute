"""/api/trips — CRUD plus domain actions (comparison, completion, AI advice)."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_advisor, get_trip_service
from app.models import TripStatus
from app.schemas import AiAdvice, CompleteTripRequest, Comparison, TripCreate, TripRead, TripUpdate
from app.services.ai_advisor import Advisor
from app.services.trip_service import TripService, to_read

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.get("", response_model=list[TripRead])
def list_trips(
    status_filter: TripStatus | None = Query(default=None, alias="status"),
    service: TripService = Depends(get_trip_service),
):
    return [to_read(t) for t in service.list(status_filter)]


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(data: TripCreate, response: Response, service: TripService = Depends(get_trip_service)):
    trip = service.create(data)
    response.headers["Location"] = f"/api/trips/{trip.id}"
    return to_read(trip)


@router.get("/{trip_id}", response_model=TripRead)
def get_trip(trip_id: int, service: TripService = Depends(get_trip_service)):
    return to_read(service.get(trip_id))


@router.patch("/{trip_id}", response_model=TripRead)
def update_trip(trip_id: int, data: TripUpdate, service: TripService = Depends(get_trip_service)):
    return to_read(service.update(trip_id, data))


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, service: TripService = Depends(get_trip_service)):
    service.delete(trip_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{trip_id}/comparison", response_model=Comparison)
async def compare_trip(trip_id: int, service: TripService = Depends(get_trip_service)):
    return await service.compare(trip_id)


@router.post("/{trip_id}/complete", response_model=TripRead)
def complete_trip(
    trip_id: int, body: CompleteTripRequest, service: TripService = Depends(get_trip_service)
):
    return to_read(service.complete(trip_id, body.mode))


@router.post("/{trip_id}/advice", response_model=AiAdvice)
async def advise_trip(
    trip_id: int,
    service: TripService = Depends(get_trip_service),
    advisor: Advisor = Depends(get_advisor),
):
    comparison = await service.compare(trip_id)
    return await advisor.advise(service.get(trip_id), comparison)
