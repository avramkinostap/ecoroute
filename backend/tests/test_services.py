import asyncio

from app.services.ai_advisor import parse_model_json
from app.services.geocoding import OfflineGeocoder
from app.services.eco_points import level_for, points_for
from app.services.transport import MODES, estimate, haversine_km


def test_haversine_wroclaw_krakow():
    assert 230 < haversine_km(51.1079, 17.0385, 50.0647, 19.9450) < 240


def test_carpool_splits_cost_and_emissions():
    car = estimate(MODES["car"], 100, 1)
    pool = estimate(MODES["carpool"], 100, 1)
    assert pool.cost_pln < car.cost_pln
    assert pool.co2_kg < car.co2_kg


def test_car_emissions_do_not_grow_with_passengers_in_one_car():
    assert estimate(MODES["car"], 50, 1).co2_kg == estimate(MODES["car"], 50, 4).co2_kg


def test_eco_points_and_levels():
    assert points_for(0, 1.0) == 6  # 1 for 1 kg saved + 5 zero-emission bonus
    assert points_for(2.0, 1.0) == 0
    assert level_for(0) == ("🌱 Nowicjusz", 50)
    assert level_for(500)[1] is None


def test_parse_model_json_tolerates_fences():
    text = 'Oto odpowiedź:\n```json\n{"summary": "OK", "tips": ["a"]}\n```'
    assert parse_model_json(text)["summary"] == "OK"


def test_offline_geocoder_ignores_diacritics():
    names = [p.name for p in asyncio.run(OfflineGeocoder().search("wroc"))]
    assert "Wrocław" in names
    assert asyncio.run(OfflineGeocoder().search("lodz"))[0].name == "Łódź"
