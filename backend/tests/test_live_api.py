"""Integration tests against live running FastAPI and Mosquitto services.

These tests send real HTTP requests over the network to http://127.0.0.1:8000.
Automatically skipped if the live backend server is not running.
"""

import httpx
import pytest

from src.config import get_settings

BASE_URL = "http://127.0.0.1:8000"


def is_live_server_reachable() -> bool:
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=1.0)
        return resp.status_code == 200
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not is_live_server_reachable(),
        reason="Live backend server is not running on http://127.0.0.1:8000",
    ),
]


@pytest.fixture(scope="module")
def live_client():
    with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
        yield client


@pytest.fixture(scope="module")
def worker_creds():
    settings = get_settings()
    return {
        "username": settings.MQTT_WORKER_USERNAME or "backend_worker",
        "password": settings.MQTT_WORKER_PASSWORD,
    }


def test_live_health_endpoint(live_client):
    resp = live_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "mqtt_connected" in data


def test_live_mqtt_user_auth_valid(live_client, worker_creds):
    resp = live_client.post("/api/v1/auth/mqtt/user", json=worker_creds)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["user"] == worker_creds["username"]


def test_live_mqtt_user_auth_invalid(live_client, worker_creds):
    resp = live_client.post(
        "/api/v1/auth/mqtt/user",
        json={"username": worker_creds["username"], "password": "wrong_password_123"},
    )
    assert resp.status_code == 401


def test_live_mqtt_user_auth_form_urlencoded(live_client, worker_creds):
    resp = live_client.post(
        "/api/v1/auth/mqtt/user",
        data=worker_creds,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_live_mqtt_superuser_worker(live_client, worker_creds):
    resp = live_client.post(
        "/api/v1/auth/mqtt/superuser",
        json={"username": worker_creds["username"]},
    )
    assert resp.status_code == 200
    assert resp.json()["superuser"] is True


def test_live_mqtt_superuser_other_user(live_client):
    resp = live_client.post(
        "/api/v1/auth/mqtt/superuser",
        json={"username": "random_edge_node"},
    )
    assert resp.status_code == 403


def test_live_mqtt_acl_worker_superuser_access(live_client, worker_creds):
    resp = live_client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": worker_creds["username"],
            "topic": "properties/prop_test_1/relay/switch1/set",
            "acc": 2,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["allowed"] is True


def test_live_mqtt_acl_worker_out_of_scope_denied(live_client, worker_creds):
    resp = live_client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": worker_creds["username"],
            "topic": "outside/scope/topic",
            "acc": 2,
        },
    )
    assert resp.status_code == 403


def test_live_mqtt_acl_unauthorized_user_denied(live_client):
    resp = live_client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": "unknown_edge_node",
            "topic": "properties/prop_test_1/relay/switch1/state",
            "acc": 2,
        },
    )
    assert resp.status_code == 403
