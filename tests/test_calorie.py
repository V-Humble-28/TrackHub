
import pytest

from trackers.calorie.app import app, get_connection


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_database = tmp_path / "test_calorie.db"
    monkeypatch.setattr(
        "trackers.calorie.app.DATABASE",
        test_database,
    )

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE food_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_name TEXT NOT NULL,
                weight REAL NOT NULL,
                calories_per_100g REAL NOT NULL,
                meal TEXT NOT NULL,
                entry_date TEXT NOT NULL
            )
        """)

    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_search_foods(client):
    response = client.get("/api/calorie/foods?q=rice")

    assert response.status_code == 200
    data = response.get_json()

    assert data["count"] > 0
    assert any("rice" in food["name"].lower() for food in data["foods"])


def test_add_dataset_food(client):
    response = client.post(
        "/api/calorie/entries",
        json={"food_id": 15, "weight": 150, "meal": "lunch"},
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["food_name"] == "Rice, raw, milled"
    assert data["calories"] == 534.0
    assert data["source"] == "dataset"


def test_reject_invalid_meal(client):
    response = client.post(
        "/api/calorie/entries",
        json={
            "food_name": "Rice",
            "weight": 150,
            "calories_per_100g": 130,
            "meal": "invalid",
        },
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_delete_entry(client):
    response = client.post(
        "/api/calorie/entries",
        json={"food_id": 15, "weight": 100, "meal": "lunch"},
    )
    entry_id = response.get_json()["id"]

    response = client.delete(f"/api/calorie/entries/{entry_id}")

    assert response.status_code == 200

    summary = client.get("/api/calorie/entries").get_json()
    assert summary["entry_count"] == 0
