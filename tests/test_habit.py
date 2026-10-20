
import pytest
from trackers.habit import app as habit_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_habit.db"
    monkeypatch.setattr(habit_module, "DB", test_db)
    habit_module.init_db()

    habit_module.app.config["TESTING"] = True
    with habit_module.app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/api/habit/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_habit(client):
    response = client.post(
        "/api/habit/habits",
        json={
            "name": "Practise Python",
            "description": "Solve one coding problem",
            "frequency": "daily",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["name"] == "Practise Python"


def test_complete_habit(client):
    habit = client.post(
        "/api/habit/habits",
        json={"name": "Read", "frequency": "daily"},
    ).get_json()

    response = client.post(
        f"/api/habit/habits/{habit['id']}/complete",
        json={"date": "2026-10-21"},
    )
    assert response.status_code == 201

    habits = client.get("/api/habit/habits").get_json()
    assert habits[0]["completed_today"] is True


def test_prevent_duplicate_completion(client):
    habit = client.post(
        "/api/habit/habits",
        json={"name": "Exercise"},
    ).get_json()

    url = f"/api/habit/habits/{habit['id']}/complete"
    client.post(url, json={"date": "2026-10-21"})
    response = client.post(url, json={"date": "2026-10-21"})

    assert response.status_code == 200
    assert "already completed" in response.get_json()["message"]


def test_reject_invalid_frequency(client):
    response = client.post(
        "/api/habit/habits",
        json={"name": "Invalid habit", "frequency": "hourly"},
    )
    assert response.status_code == 400
