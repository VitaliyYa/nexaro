"""Integration tests against live running FastAPI and Mosquitto services.

These tests send real HTTP requests over the network to http://127.0.0.1:8000.
Automatically skipped if the live backend server is not running.
"""

import os
import uuid

import httpx
import pytest
from supabase import create_client

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
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        yield client


@pytest.fixture(scope="module")
def worker_creds():
    settings = get_settings()
    return {
        "username": settings.MQTT_WORKER_USERNAME or "backend_worker",
        "password": settings.MQTT_WORKER_PASSWORD,
    }


@pytest.fixture(scope="module")
def auth_token():
    settings = get_settings()
    email = os.getenv("TEST_USER_EMAIL", "testowner@smartrent.io")
    password = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")
    try:
        admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
        public_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)

        users = admin_client.auth.admin.list_users()
        existing = next((u for u in users if u.email == email), None)
        if not existing:
            admin_client.auth.admin.create_user({"email": email, "password": password, "email_confirm": True})
        elif not existing.email_confirmed_at:
            admin_client.auth.admin.update_user_by_id(existing.id, {"email_confirm": True})

        session = public_client.auth.sign_in_with_password({"email": email, "password": password})
        return session.session.access_token
    except Exception:
        import jwt

        return jwt.encode(
            {"sub": str(uuid.uuid4()), "email": email, "role": "authenticated"},
            "test_secret_with_minimum_32_characters_for_hmac",
            algorithm="HS256",
        )


@pytest.fixture(scope="module")
def auth_client(auth_token):
    with httpx.Client(base_url=BASE_URL, headers={"Authorization": f"Bearer {auth_token}"}, timeout=10.0) as client:
        yield client


# ==============================================================================
# 1. Health & Broker Webhooks
# ==============================================================================


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


# ==============================================================================
# 2. Properties, Devices, PINs, Commands & Logs Full Lifecycle
# ==============================================================================


def test_live_full_crud_and_iot_lifecycle(auth_client):
    created_prop_id = None
    created_device_id = f"test_lock_{uuid.uuid4().hex[:8]}"
    created_pin_id = None

    try:
        # 1. POST /properties
        prop_payload = {
            "name": "Live Pytest Apartment, 42",
            "address": "Baker street 221B",
            "timezone": "UTC",
        }
        create_prop_resp = auth_client.post("/api/v1/properties", json=prop_payload)
        assert create_prop_resp.status_code == 201
        created_prop_id = create_prop_resp.json()["id"]

        # 2. GET /properties
        list_props_resp = auth_client.get("/api/v1/properties")
        assert list_props_resp.status_code == 200
        assert any(p["id"] == created_prop_id for p in list_props_resp.json())

        # 3. GET /properties/{id}
        get_prop_resp = auth_client.get(f"/api/v1/properties/{created_prop_id}")
        assert get_prop_resp.status_code == 200
        assert get_prop_resp.json()["name"] == "Live Pytest Apartment, 42"

        # 4. PATCH /properties/{id}
        patch_prop_resp = auth_client.patch(
            f"/api/v1/properties/{created_prop_id}",
            json={"name": "Live Pytest Apartment, 42 (Updated)"},
        )
        assert patch_prop_resp.status_code == 200
        assert patch_prop_resp.json()["name"] == "Live Pytest Apartment, 42 (Updated)"

        # 5. POST /properties/{id}/devices
        device_payload = {
            "id": created_device_id,
            "device_type": "lock",
            "name": "Front Door Lock",
            "is_active": True,
            "settings": {"auto_lock": True},
        }
        create_dev_resp = auth_client.post(f"/api/v1/properties/{created_prop_id}/devices", json=device_payload)
        assert create_dev_resp.status_code == 201
        assert create_dev_resp.json()["id"] == created_device_id

        # 6. GET /properties/{id}/devices
        list_devs_resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/devices")
        assert list_devs_resp.status_code == 200
        assert any(d["id"] == created_device_id for d in list_devs_resp.json())

        # 7. GET /properties/{id}/devices/{device_id}
        get_dev_resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}")
        assert get_dev_resp.status_code == 200
        assert get_dev_resp.json()["name"] == "Front Door Lock"

        # 8. PATCH /properties/{id}/devices/{device_id}
        patch_dev_resp = auth_client.patch(
            f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}",
            json={"name": "Front Door Lock (Renamed)"},
        )
        assert patch_dev_resp.status_code == 200
        assert patch_dev_resp.json()["name"] == "Front Door Lock (Renamed)"

        # 9. POST /properties/{id}/locks/{device_id}/pins (AES Encryption)
        pin_payload = {
            "device_id": created_device_id,
            "name": "Guest PIN",
            "pin": "123456",
            "valid_from": "2026-09-01T12:00:00Z",
            "valid_to": "2026-09-05T12:00:00Z",
        }
        create_pin_resp = auth_client.post(
            f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins",
            json=pin_payload,
        )
        assert create_pin_resp.status_code == 201
        pin_data = create_pin_resp.json()
        created_pin_id = pin_data["id"]
        assert "pin" not in pin_data  # Raw PIN must never be exposed

        # 10. GET /properties/{id}/locks/{device_id}/pins
        list_pins_resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins")
        assert list_pins_resp.status_code == 200
        assert any(p["id"] == created_pin_id for p in list_pins_resp.json())

        # 11. PATCH /properties/{id}/locks/{device_id}/pins/{pin_id}
        patch_pin_resp = auth_client.patch(
            f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins/{created_pin_id}",
            json={"name": "Guest PIN (Extended)"},
        )
        assert patch_pin_resp.status_code == 200
        assert patch_pin_resp.json()["name"] == "Guest PIN (Extended)"

        # 12. POST /properties/{id}/devices/{device_id}/command (MQTT publish)
        cmd_resp = auth_client.post(
            f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}/command",
            json={"command": "unlock"},
        )
        assert cmd_resp.status_code == 200
        assert cmd_resp.json()["status"] in ("published", "queued_offline")

        # 13. GET /properties/{id}/logs/audit
        audit_resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/logs/audit")
        assert audit_resp.status_code == 200
        audit_actions = [a["action"] for a in audit_resp.json()]
        assert "PIN_CREATED" in audit_actions

        # 14. GET /properties/{id}/logs/devices
        logs_resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/logs/devices")
        assert logs_resp.status_code == 200

        # 15. DELETE PIN
        del_pin_resp = auth_client.delete(
            f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins/{created_pin_id}"
        )
        assert del_pin_resp.status_code == 204

        # 16. DELETE Device
        del_dev_resp = auth_client.delete(f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}")
        assert del_dev_resp.status_code == 204

        # 17. DELETE Property
        del_prop_resp = auth_client.delete(f"/api/v1/properties/{created_prop_id}")
        assert del_prop_resp.status_code == 204

        # 18. Verify 404
        check_deleted_resp = auth_client.get(f"/api/v1/properties/{created_prop_id}")
        assert check_deleted_resp.status_code == 404

    finally:
        try:
            if created_pin_id:
                auth_client.delete(
                    f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins/{created_pin_id}"
                )
            if created_device_id and created_prop_id:
                auth_client.delete(f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}")
            if created_prop_id:
                auth_client.delete(f"/api/v1/properties/{created_prop_id}")
        except Exception:
            pass
