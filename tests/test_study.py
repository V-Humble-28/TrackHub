
import pytest
from trackers.study import app as study_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_study.db"
    monkeypatch.setattr(study_module, "DB", test_db)
    study_module.init_db()

    study_module.app.config["TESTING"] = True
    with study_module.app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/api/study/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_subject(client):
    response = client.post(
        "/api/study/subjects",
        json={"name": "Data Structures"}
    )
    assert response.status_code == 201
    assert response.get_json()["name"] == "Data Structures"


def test_add_session_and_dashboard(client):
    subject = client.post(
        "/api/study/subjects",
        json={"name": "Algorithms"}
    ).get_json()

    response = client.post(
        "/api/study/sessions",
        json={
            "subject_id": subject["id"],
            "duration_minutes": 45,
            "notes": "Practised sorting"
        }
    )
    assert response.status_code == 201

    dashboard = client.get("/api/study/dashboard").get_json()
    assert dashboard["today_minutes"] == 45
    assert dashboard["weekly_total_minutes"] == 45


def test_add_assignment(client):
    subject = client.post(
        "/api/study/subjects",
        json={"name": "Networks"}
    ).get_json()

    response = client.post(
        "/api/study/tasks",
        json={
            "title": "Finish lab",
            "type": "assignment",
            "subject_id": subject["id"],
            "due_date": "2026-10-25"
        }
    )
    assert response.status_code == 201
    assert response.get_json()["title"] == "Finish lab"


def test_reject_invalid_session(client):
    response = client.post(
        "/api/study/sessions",
        json={"subject_id": 999, "duration_minutes": 30}
    )
    assert response.status_code == 404
