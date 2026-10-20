
import pytest

from trackers.calorie.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_add_food(client):
    response = client.post(
        "/api/calorie/entries",
        json={
            "food_name": "Test Rice",
            "weight": 150,
            "calories_per_100g": 130,
            "meal": "lunch",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["food_name"] == "Test Rice"
    assert data["calories"] == 195.0


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
