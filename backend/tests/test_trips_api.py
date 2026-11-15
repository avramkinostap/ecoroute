from tests.conftest import KRAKOW, WROCLAW, trip_payload


def test_crud_lifecycle(client):
    created = client.post("/api/trips", json=trip_payload())
    assert created.status_code == 201
    trip = created.json()
    assert created.headers["Location"] == f"/api/trips/{trip['id']}"
    assert trip["status"] == "planned"
    assert 2 < trip["distance_km"] < 6

    assert client.get(f"/api/trips/{trip['id']}").json()["title"] == "Na uczelnię"
    assert len(client.get("/api/trips").json()) == 1

    patched = client.patch(f"/api/trips/{trip['id']}", json={"title": "Do pracy", "passengers": 2})
    assert patched.status_code == 200
    assert patched.json()["title"] == "Do pracy"
    assert patched.json()["passengers"] == 2

    assert client.delete(f"/api/trips/{trip['id']}").status_code == 204
    assert client.get(f"/api/trips/{trip['id']}").status_code == 404


def test_changing_destination_recalculates_distance(client):
    trip = client.post("/api/trips", json=trip_payload()).json()
    patched = client.patch(f"/api/trips/{trip['id']}", json={"destination": KRAKOW}).json()
    assert patched["destination"]["name"] == "Kraków"
    assert patched["distance_km"] > 250


def test_validation_errors(client):
    assert client.post("/api/trips", json=trip_payload(destination=WROCLAW)).status_code == 422
    assert client.post("/api/trips", json=trip_payload(passengers=0)).status_code == 422
    assert client.post("/api/trips", json=trip_payload(title="")).status_code == 422


def test_filter_by_status(client):
    a = client.post("/api/trips", json=trip_payload()).json()
    client.post("/api/trips", json=trip_payload(title="Drugi"))
    client.post(f"/api/trips/{a['id']}/complete", json={"mode": "bike"})
    assert [t["id"] for t in client.get("/api/trips?status=completed").json()] == [a["id"]]
    assert len(client.get("/api/trips?status=planned").json()) == 1


def test_comparison_short_trip_good_weather_prefers_active_mode(client):
    trip = client.post("/api/trips", json=trip_payload(priority="eco")).json()
    comp = client.get(f"/api/trips/{trip['id']}/comparison").json()
    by_mode = {o["mode"]: o for o in comp["options"]}
    assert by_mode["plane"]["feasible"] is False
    assert by_mode["train"]["feasible"] is False
    assert comp["recommended_mode"] in {"bike", "walk"}
    assert comp["weather"]["bad_for_active_modes"] is False


def test_bad_weather_pushes_away_from_bike(client, weather):
    from app.services.weather import build_weather

    weather.value = build_weather(temp=4, prob=90, mm=3.2, wind=20, code=63)
    trip = client.post("/api/trips", json=trip_payload(priority="eco")).json()
    comp = client.get(f"/api/trips/{trip['id']}/comparison").json()
    assert comp["recommended_mode"] not in {"bike", "walk", "scooter"}
    assert any("Prognoza" in r for r in comp["reasons"])


def test_long_trip_offers_train_and_plane(client):
    trip = client.post("/api/trips", json=trip_payload(destination=KRAKOW)).json()
    comp = client.get(f"/api/trips/{trip['id']}/comparison").json()
    feasible = {o["mode"] for o in comp["options"] if o["feasible"]}
    assert {"train", "coach", "car", "carpool"} <= feasible
    assert "bike" not in feasible


def test_complete_awards_points_and_updates_stats(client):
    trip = client.post("/api/trips", json=trip_payload(destination=KRAKOW)).json()
    done = client.post(f"/api/trips/{trip['id']}/complete", json={"mode": "train"})
    assert done.status_code == 200
    body = done.json()
    assert body["status"] == "completed"
    assert body["co2_saved_kg"] > 0
    assert body["eco_points"] > 0

    stats = client.get("/api/stats").json()
    assert stats["completed_trips"] == 1
    assert stats["eco_points"] == body["eco_points"]
    assert stats["favourite_mode"] == "train"

    # Completed trips are immutable.
    assert client.post(f"/api/trips/{trip['id']}/complete", json={"mode": "train"}).status_code == 409
    assert client.patch(f"/api/trips/{trip['id']}", json={"title": "x"}).status_code == 409


def test_complete_rejects_infeasible_or_unknown_mode(client):
    trip = client.post("/api/trips", json=trip_payload()).json()
    assert client.post(f"/api/trips/{trip['id']}/complete", json={"mode": "plane"}).status_code == 422
    assert client.post(f"/api/trips/{trip['id']}/complete", json={"mode": "rocket"}).status_code == 422


def test_advice_falls_back_to_rules(client):
    trip = client.post("/api/trips", json=trip_payload()).json()
    advice = client.post(f"/api/trips/{trip['id']}/advice").json()
    assert advice["source"] == "rules"
    assert "Wrocław" in advice["summary"]


def test_places_and_cors(client):
    assert client.get("/api/places?q=Wro").json()[0]["name"] == "Wrocław"
    preflight = client.options(
        "/api/trips",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
