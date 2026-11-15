import os

os.environ["DATABASE_URL"] = "sqlite://"  # in-memory, must be set before app import
os.environ.pop("ANTHROPIC_API_KEY", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_advisor, get_geocoder, get_weather  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas import PlaceSuggestion  # noqa: E402
from app.services.ai_advisor import RuleBasedAdvisor  # noqa: E402
from app.services.weather import build_weather  # noqa: E402

WROCLAW = {"name": "Wrocław", "lat": 51.1079, "lon": 17.0385}
WROCLAW_RYNEK_NEAR = {"name": "Wrocław Krzyki", "lat": 51.0820, "lon": 17.0270}
KRAKOW = {"name": "Kraków", "lat": 50.0647, "lon": 19.9450}


class FakeWeather:
    def __init__(self) -> None:
        self.value = build_weather(temp=18, prob=10, mm=0, wind=8, code=1)

    async def forecast(self, lat, lon, at):
        return self.value


class FakeGeocoder:
    async def search(self, query, limit=6):
        return [PlaceSuggestion(**WROCLAW, country="Polska", region="Dolnośląskie")]


@pytest.fixture
def weather() -> FakeWeather:
    return FakeWeather()


@pytest.fixture
def client(weather):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_weather] = lambda: weather
    app.dependency_overrides[get_geocoder] = lambda: FakeGeocoder()
    app.dependency_overrides[get_advisor] = lambda: RuleBasedAdvisor()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def trip_payload(**overrides):
    data = {
        "title": "Na uczelnię",
        "origin": WROCLAW,
        "destination": WROCLAW_RYNEK_NEAR,
        "departure_at": "2030-05-10T08:00:00Z",
        "passengers": 1,
        "priority": "balanced",
    }
    data.update(overrides)
    return data
