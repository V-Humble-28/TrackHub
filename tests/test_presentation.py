"""Unit tests for the DevOps Presentation & Live Demo Module."""

import pytest
from trackers.presentation.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_presentation_health(client):
    response = client.get("/api/presentation/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "DevOps Presentation" in data["app"]


def test_system_overview(client):
    response = client.get("/api/presentation/system-overview")
    assert response.status_code == 200
    data = response.get_json()
    assert data["gateway"]["port"] == 5001
    assert data["total_services"] >= 4
    services = [s["service"] for s in data["services"]]
    assert "Calorie Tracker" in services
    assert "Expense Tracker" in services
    assert "Habit Tracker" in services
    assert "Study Tracker" in services


def test_ci_status(client):
    response = client.get("/api/presentation/ci-status")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["ci_workflows"]) >= 2
    assert data["git_hooks"]["local_hook_script"] is True
