import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.db import init_db, SessionLocal
from backend.database.seed import seed_database

@pytest.fixture(autouse=True, scope="module")
def setup_api_test_environment():
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

client = TestClient(app)


def test_api_health_and_index():
    response = client.get("/")
    assert response.status_code == 200


def test_api_list_workflows():
    response = client.get("/api/workflows")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_api_workflow_stats():
    response = client.get("/api/workflows/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_workflows" in data
    assert "active_workflows" in data
    assert "recovery_success_rate" in data


def test_api_list_approvals():
    response = client.get("/api/approvals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_services_health():
    response = client.get("/api/services/health")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_api_demo_scenario_execution():
    response = client.post("/api/demo/run-scenario", json={
        "scenario_id": "payment_timeout",
        "auto_approve": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "workflow_id" in data and len(data["workflow_id"]) > 0
    assert data["status"] in ["COMPLETED", "RECOVERING", "WAITING_FOR_APPROVAL", "RUNNING", "FAILED"]
