import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"TrackHub" in response.data or b"Track Hub" in response.data
    assert b'href="habit.html"' in response.data
    assert b'href="study.html"' in response.data


def test_tracker_pages(client):
    res_cal = client.get("/calorie")
    assert res_cal.status_code == 200
    assert b"Calorie Tracker" in res_cal.data

    res_exp = client.get("/expense")
    assert res_exp.status_code == 200
    assert b"Expense Tracker" in res_exp.data

    res_hab = client.get("/habit")
    assert res_hab.status_code == 200
    assert b"Habit Tracker" in res_hab.data

    res_stu = client.get("/study")
    assert res_stu.status_code == 200
    assert b"Study Tracker" in res_stu.data


def test_static_assets(client):
    for asset in ["habit.html", "study.html", "habit.js", "study.js", "tracker.css"]:
        res = client.get(f"/{asset}")
        assert res.status_code == 200


def test_mounted_api_endpoints(client):
    # Calorie health check mounted
    res = client.get("/api/health")
    assert res.status_code == 200

    # Expense health check mounted
    res = client.get("/api/expense/health")
    assert res.status_code == 200

    # Expense entries endpoint mounted
    res = client.get("/api/expense/entries")
    assert res.status_code == 200

    # Habit health & dashboard mounted
    res_habit_health = client.get("/api/habit/health")
    assert res_habit_health.status_code == 200
    res_habit_dash = client.get("/api/habit/dashboard")
    assert res_habit_dash.status_code == 200

    # Study health & dashboard mounted
    res_study_health = client.get("/api/study/health")
    assert res_study_health.status_code == 200
    res_study_dash = client.get("/api/study/dashboard")
    assert res_study_dash.status_code == 200
