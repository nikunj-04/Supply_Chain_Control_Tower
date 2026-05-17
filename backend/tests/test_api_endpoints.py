"""Integration-style tests for the FastAPI application endpoints."""

import sys
from pathlib import Path
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main as main_module


@pytest.fixture
def client():
    return TestClient(main_module.app)


def test_root_endpoint_returns_application_metadata(client):
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == main_module.settings.app_name
    assert payload["version"] == main_module.settings.app_version
    assert payload["status"] == "operational"
    assert payload["endpoints"]["health"] == "/api/v1/health"
    assert payload["endpoints"]["docs"] == "/api/docs"


def test_health_check_reports_all_systems_connected(monkeypatch, client):
    monkeypatch.setattr(main_module.os.path, "exists", lambda path: True)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == main_module.settings.app_version
    assert set(payload["systems_connected"].values()) == {True}
    assert set(payload["systems_connected"].keys()) == {"WMS", "OMS", "TMS", "Billing", "Returns", "Yard"}


def test_operational_scorecard_uses_dashboard_service(monkeypatch, client):
    captured_user = {}

    def fake_set_current_user(user):
        captured_user["value"] = user

    fake_scorecard = {
        "timestamp": datetime(2026, 1, 15, 12, 0, 0),
        "systems": [
            {
                "system_name": "OMS",
                "metrics": [
                    {
                        "name": "orders",
                        "value": 12.0,
                        "unit": "count",
                        "trend": "stable",
                        "status": "good",
                    }
                ],
                "overall_status": "healthy",
            }
        ],
        "summary": {"total_shipments": 12}
    }

    monkeypatch.setattr(main_module.dashboard_service, "set_current_user", fake_set_current_user)
    monkeypatch.setattr(main_module.dashboard_service, "get_operational_scorecard", lambda: fake_scorecard)

    response = client.get("/api/v1/dashboard/scorecard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["timestamp"] == "2026-01-15T12:00:00"
    assert payload["systems"] == fake_scorecard["systems"]
    assert payload["summary"] == fake_scorecard["summary"]
    assert captured_user["value"] is None


def test_auth_login_returns_token_payload(monkeypatch, client):
    fake_result = {
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "System Admin",
            "is_superuser": True,
            "client_id": None,
            "department": "operations",
            "roles": [],
            "permissions": []
        },
        "token": "token-123",
        "refresh_token": "refresh-123",
        "expires_at": "2026-01-15T20:00:00"
    }

    monkeypatch.setattr(main_module.auth_service, "authenticate", lambda *args, **kwargs: fake_result)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "password"},
        headers={"user-agent": "pytest"},
    )

    assert response.status_code == 200
    assert response.json() == fake_result


def test_auth_me_returns_current_user(monkeypatch, client):
    fake_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "System Admin",
        "is_superuser": True,
        "client_id": None,
        "department": "operations",
        "roles": ["system_admin"],
        "permissions": ["*"]
    }

    monkeypatch.setattr(main_module.auth_service, "validate_token", lambda token: fake_user)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == fake_user


def test_exception_stats_returns_service_payload(monkeypatch, client):
    class DummySession:
        def close(self):
            pass

    class DummyService:
        def __init__(self):
            self.session = DummySession()

        def get_exception_stats(self):
            return {"open": 3, "resolved": 7}

    monkeypatch.setattr(main_module, "get_exception_service", lambda: DummyService())

    response = client.get("/api/v1/exceptions/stats")

    assert response.status_code == 200
    assert response.json() == {"open": 3, "resolved": 7}


def test_auth_logout_returns_success_for_valid_token(monkeypatch, client):
    fake_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "System Admin",
        "is_superuser": True,
        "client_id": None,
        "department": "operations",
        "roles": ["system_admin"],
        "permissions": ["*"]
    }

    monkeypatch.setattr(main_module.auth_service, "validate_token", lambda token: fake_user)
    monkeypatch.setattr(main_module.auth_service, "logout", lambda token, ip_address=None: True)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Logged out successfully"}