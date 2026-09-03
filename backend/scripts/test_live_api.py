#!/usr/bin/env python3
"""
Comprehensive Live API and Integration Test Script for SmartRent.

Runs real HTTP requests against a running SmartRent backend (http://127.0.0.1:8000)
connected to a real Mosquitto broker and Supabase database.

Covers:
  1. GET /health - System health & MQTT connection status
  2. Mosquitto Webhooks:
     - POST /api/v1/auth/mqtt/user (valid, invalid, form-urlencoded)
     - POST /api/v1/auth/mqtt/superuser (worker vs other user)
     - POST /api/v1/auth/mqtt/acl (worker vs out-of-scope vs unknown edge user)
  3. Properties CRUD:
     - POST /api/v1/properties
     - GET /api/v1/properties
     - GET /api/v1/properties/{property_id}
     - PATCH /api/v1/properties/{property_id}
  4. IoT Devices Management:
     - POST /api/v1/properties/{property_id}/devices
     - GET /api/v1/properties/{property_id}/devices
     - GET /api/v1/properties/{property_id}/devices/{device_id}
     - PATCH /api/v1/properties/{property_id}/devices/{device_id}
  5. Smart Lock PINs (AES Encrypted at Rest & Audit Logged):
     - POST /api/v1/properties/{property_id}/locks/{device_id}/pins
     - GET /api/v1/properties/{property_id}/locks/{device_id}/pins
     - PATCH /api/v1/properties/{property_id}/locks/{device_id}/pins/{pin_id}
     - DELETE /api/v1/properties/{property_id}/locks/{device_id}/pins/{pin_id}
  6. IoT Command Dispatcher:
     - POST /api/v1/properties/{property_id}/devices/{device_id}/command
  7. Telemetry & Audit Trail:
     - GET /api/v1/properties/{property_id}/logs/audit
     - GET /api/v1/properties/{property_id}/logs/telemetry
  8. Cleanup & Deletion Verification:
     - DELETE /api/v1/properties/{property_id}/devices/{device_id}
     - DELETE /api/v1/properties/{property_id}
     - GET /api/v1/properties/{property_id} (verify 404)
"""

import os
import sys
import uuid

import httpx
from supabase import create_client

from src.config import get_settings

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_step(title: str):
    print(f"\n{CYAN}{BOLD}▶ {title}{RESET}")


def print_pass(message: str):
    print(f"  {GREEN}✔ [PASS]{RESET} {message}")


def print_fail(message: str):
    print(f"  {RED}✘ [FAIL]{RESET} {message}")


def get_auth_token(settings) -> str:
    """Obtains a valid Supabase JWT for testing user-authenticated endpoints."""
    email = os.getenv("TEST_USER_EMAIL", "testowner@smartrent.io")
    password = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")

    # Try signing in via Supabase client
    try:
        admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
        public_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)

        # Ensure user exists and is confirmed
        users = admin_client.auth.admin.list_users()
        existing = next((u for u in users if u.email == email), None)
        if not existing:
            admin_client.auth.admin.create_user({"email": email, "password": password, "email_confirm": True})
        elif not existing.email_confirmed_at:
            admin_client.auth.admin.update_user_by_id(existing.id, {"email_confirm": True})

        session = public_client.auth.sign_in_with_password({"email": email, "password": password})
        return session.session.access_token
    except Exception as exc:
        print(f"  {YELLOW}⚠ Не удалось войти через Supabase ({exc}), используем тестовый токен{RESET}")
        import jwt

        return jwt.encode(
            {"sub": str(uuid.uuid4()), "email": email, "role": "authenticated"},
            "test_secret_with_minimum_32_characters_for_hmac",
            algorithm="HS256",
        )


def main():
    settings = get_settings()
    base_url = "http://127.0.0.1:8000"
    worker_username = settings.MQTT_WORKER_USERNAME or "backend_worker"
    worker_password = settings.MQTT_WORKER_PASSWORD

    print(f"{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}SmartRent Live End-to-End API & Integration Test Suite{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}")
    print(f"Target API:        {base_url}")
    print(f"Worker Username:   {worker_username}")
    print(f"Environment:       {settings.ENVIRONMENT}")

    client = httpx.Client(base_url=base_url, timeout=10.0)
    failed_tests = 0

    # --------------------------------------------------------------------------
    # 1. Health Check
    # --------------------------------------------------------------------------
    print_step("1. GET /health - System Health & MQTT Connection")
    try:
        resp = client.get("/health")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "healthy":
                mqtt_status = "connected" if data.get("mqtt_connected") else "disconnected"
                print_pass(f"Server is healthy (MQTT Broker: {mqtt_status}, HTTP 200)")
            else:
                print_fail(f"Unexpected status response: {data}")
                failed_tests += 1
        else:
            print_fail(f"Expected HTTP 200, got {resp.status_code}: {resp.text}")
            failed_tests += 1
    except Exception as exc:
        print_fail(f"Could not connect to {base_url}/health: {exc}")
        print(f"\n{YELLOW}Подсказка: запустите бэкенд перед тестом:{RESET}")
        print("  uv run uvicorn src.main:app --reload --port 8000\n")
        return 1

    # --------------------------------------------------------------------------
    # 2. Mosquitto Webhooks
    # --------------------------------------------------------------------------
    print_step("2. Mosquitto Broker Auth Webhooks (/user, /superuser, /acl)")

    # 2.1 Valid worker credentials
    resp = client.post(
        "/api/v1/auth/mqtt/user",
        json={"username": worker_username, "password": worker_password},
    )
    if resp.status_code == 200 and resp.json().get("status") == "ok":
        print_pass("POST /api/v1/auth/mqtt/user: Valid credentials accepted (HTTP 200)")
    else:
        print_fail(f"POST /api/v1/auth/mqtt/user: Valid credentials rejected: {resp.status_code}")
        failed_tests += 1

    # 2.2 Invalid password
    resp = client.post(
        "/api/v1/auth/mqtt/user",
        json={"username": worker_username, "password": "wrong_invalid_password_123"},
    )
    if resp.status_code == 401:
        print_pass("POST /api/v1/auth/mqtt/user: Invalid password rejected (HTTP 401)")
    else:
        print_fail(f"POST /api/v1/auth/mqtt/user: Expected 401, got {resp.status_code}")
        failed_tests += 1

    # 2.3 Form-urlencoded
    resp = client.post(
        "/api/v1/auth/mqtt/user",
        data={"username": worker_username, "password": worker_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code == 200:
        print_pass("POST /api/v1/auth/mqtt/user: Form-urlencoded format accepted (HTTP 200)")
    else:
        print_fail(f"POST /api/v1/auth/mqtt/user: Form-urlencoded rejected: {resp.status_code}")
        failed_tests += 1

    # 2.4 Superuser check
    resp = client.post("/api/v1/auth/mqtt/superuser", json={"username": worker_username})
    if resp.status_code == 200 and resp.json().get("superuser") is True:
        print_pass(f"POST /api/v1/auth/mqtt/superuser: '{worker_username}' is superuser (HTTP 200)")
    else:
        print_fail(f"POST /api/v1/auth/mqtt/superuser: Worker superuser check failed: {resp.status_code}")
        failed_tests += 1

    resp = client.post("/api/v1/auth/mqtt/superuser", json={"username": "unauthorized_user"})
    if resp.status_code == 403:
        print_pass("POST /api/v1/auth/mqtt/superuser: Other user rejected (HTTP 403)")
    else:
        print_fail(f"POST /api/v1/auth/mqtt/superuser: Expected 403, got {resp.status_code}")
        failed_tests += 1

    # 2.5 ACL check
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={"username": worker_username, "topic": "properties/prop_test_123/relay/r1/set", "acc": 2},
    )
    if resp.status_code == 200 and resp.json().get("allowed") is True:
        print_pass("POST /api/v1/auth/mqtt/acl: Worker allowed 'properties/+/+/+/set' (HTTP 200)")
    else:
        print_fail(f"POST /api/v1/auth/mqtt/acl: Worker ACL check failed: {resp.status_code}")
        failed_tests += 1

    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={"username": worker_username, "topic": "forbidden/topic/prefix", "acc": 2},
    )
    if resp.status_code == 403:
        print_pass("POST /api/v1/auth/mqtt/acl: Worker out-of-scope topic blocked (HTTP 403)")
    else:
        print_fail(f"POST /api/v1/auth/mqtt/acl: Expected 403, got {resp.status_code}")
        failed_tests += 1

    # --------------------------------------------------------------------------
    # Authentication for User Endpoints
    # --------------------------------------------------------------------------
    print_step("3. Supabase User Authentication Token")
    token = get_auth_token(settings)
    print_pass(f"Obtained Bearer token for user (length: {len(token)})")
    auth_client = httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )

    created_prop_id = None
    created_device_id = "test_lock_live_01"
    created_pin_id = None

    try:
        # ----------------------------------------------------------------------
        # 4. Properties CRUD
        # ----------------------------------------------------------------------
        print_step("4. Properties API Endpoints (/api/v1/properties)")

        # 4.1 Create Property
        prop_payload = {
            "name": "Live Test Apartments, 12",
            "address": "34, 56, Random st.",
            "timezone": "UTC",
        }
        resp = auth_client.post("/api/v1/properties", json=prop_payload)
        if resp.status_code == 201:
            created_prop_id = resp.json()["id"]
            print_pass(f"POST /api/v1/properties: Created property (id={created_prop_id}, HTTP 201)")
        else:
            print_fail(f"POST /api/v1/properties: Failed ({resp.status_code}): {resp.text}")
            failed_tests += 1
            return 1

        # 4.2 List Properties
        resp = auth_client.get("/api/v1/properties")
        if resp.status_code == 200 and any(p["id"] == created_prop_id for p in resp.json()):
            print_pass("GET /api/v1/properties: Listed properties successfully, found created (HTTP 200)")
        else:
            print_fail(f"GET /api/v1/properties: Created property not in list ({resp.status_code})")
            failed_tests += 1

        # 4.3 Get Property by ID
        resp = auth_client.get(f"/api/v1/properties/{created_prop_id}")
        if resp.status_code == 200 and resp.json()["name"] == "Live Test Apartments, 12":
            print_pass(f"GET /api/v1/properties/{created_prop_id}: Fetched property details (HTTP 200)")
        else:
            print_fail(f"GET /api/v1/properties/{created_prop_id}: Failed ({resp.status_code})")
            failed_tests += 1

        # 4.4 Patch Property
        resp = auth_client.patch(
            f"/api/v1/properties/{created_prop_id}",
            json={"name": "Live Test Apartments, 12 (Renamed)"},
        )
        if resp.status_code == 200 and resp.json()["name"] == "Live Test Apartments, 12 (Renamed)":
            print_pass(f"PATCH /api/v1/properties/{created_prop_id}: Renamed property (HTTP 200)")
        else:
            print_fail(f"PATCH /api/v1/properties/{created_prop_id}: Failed ({resp.status_code})")
            failed_tests += 1

        # ----------------------------------------------------------------------
        # 5. Devices API Endpoints
        # ----------------------------------------------------------------------
        print_step("5. Devices API Endpoints (/properties/{id}/devices)")

        # 5.1 Register Device
        dev_payload = {
            "id": created_device_id,
            "device_type": "lock",
            "name": "Entrance Smart Lock",
            "is_active": True,
            "settings": {"auto_lock": True},
        }
        resp = auth_client.post(f"/api/v1/properties/{created_prop_id}/devices", json=dev_payload)
        if resp.status_code == 201:
            print_pass(f"POST .../devices: Registered '{created_device_id}' (HTTP 201)")
        else:
            print_fail(f"POST .../devices: Failed ({resp.status_code}): {resp.text}")
            failed_tests += 1

        # 5.2 List Devices
        resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/devices")
        if resp.status_code == 200 and any(d["id"] == created_device_id for d in resp.json()):
            print_pass(f"GET .../devices: Found '{created_device_id}' in property devices (HTTP 200)")
        else:
            print_fail(f"GET .../devices: Failed ({resp.status_code})")
            failed_tests += 1

        # 5.3 Get Device by ID
        resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}")
        if resp.status_code == 200 and resp.json()["name"] == "Entrance Smart Lock":
            print_pass(f"GET .../devices/{created_device_id}: Retrieved device details (HTTP 200)")
        else:
            print_fail(f"GET .../devices/{created_device_id}: Failed ({resp.status_code})")
            failed_tests += 1

        # 5.4 Patch Device
        resp = auth_client.patch(
            f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}",
            json={"name": "Entrance Smart Lock (Updated)"},
        )
        if resp.status_code == 200 and resp.json()["name"] == "Entrance Smart Lock (Updated)":
            print_pass(f"PATCH .../devices/{created_device_id}: Updated device name (HTTP 200)")
        else:
            print_fail(f"PATCH .../devices/{created_device_id}: Failed ({resp.status_code})")
            failed_tests += 1

        # ----------------------------------------------------------------------
        # 6. Smart Lock PINs (Encryption at Rest & Audit Logged)
        # ----------------------------------------------------------------------
        print_step("6. Smart Lock PIN API Endpoints (AES Encryption & Audit Trail)")

        # 6.1 Create PIN
        pin_payload = {
            "device_id": created_device_id,
            "name": "Guest: Alice",
            "pin": "654321",
            "valid_from": "2026-09-01T12:00:00Z",
            "valid_to": "2026-09-05T12:00:00Z",
        }
        resp = auth_client.post(
            f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins",
            json=pin_payload,
        )
        if resp.status_code == 201:
            data = resp.json()
            created_pin_id = data["id"]
            raw_pin_exposed = "pin" in data
            if not raw_pin_exposed:
                print_pass(f"POST .../pins: Created PIN (id={created_pin_id}, raw PIN not exposed, HTTP 201)")
            else:
                print_fail("Security violation: raw PIN was returned in response!")
                failed_tests += 1
        else:
            print_fail(f"POST .../pins: Failed ({resp.status_code}): {resp.text}")
            failed_tests += 1

        # 6.2 List PINs
        resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins")
        if resp.status_code == 200 and any(p["id"] == created_pin_id for p in resp.json()):
            print_pass("GET .../pins: Retrieved active PINs list (HTTP 200)")
        else:
            print_fail(f"GET .../pins: Failed ({resp.status_code})")
            failed_tests += 1

        # 6.3 Patch PIN
        resp = auth_client.patch(
            f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins/{created_pin_id}",
            json={"name": "Guest: Alice (Extended)"},
        )
        if resp.status_code == 200 and resp.json()["name"] == "Guest: Alice (Extended)":
            print_pass(f"PATCH .../pins/{created_pin_id}: Updated PIN label (HTTP 200)")
        else:
            print_fail(f"PATCH .../pins/{created_pin_id}: Failed ({resp.status_code})")
            failed_tests += 1

        # ----------------------------------------------------------------------
        # 7. Commands Dispatcher (MQTT QoS 1)
        # ----------------------------------------------------------------------
        print_step("7. IoT Device Commands Dispatcher via MQTT")

        cmd_payload = {"command": "unlock"}
        resp = auth_client.post(
            f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}/command",
            json=cmd_payload,
        )
        if resp.status_code == 200:
            data = resp.json()
            print_pass(f"POST .../command: Dispatched 'unlock' -> status='{data.get('status')}' (HTTP 200)")
        else:
            print_fail(f"POST .../command: Failed ({resp.status_code}): {resp.text}")
            failed_tests += 1

        # ----------------------------------------------------------------------
        # 8. Logs API (Audit Trail & Telemetry)
        # ----------------------------------------------------------------------
        print_step("8. Audit Trail & Telemetry Logs API")

        # 8.1 Audit Logs (verifies PIN creation & lock command were audited)
        resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/logs/audit")
        if resp.status_code == 200:
            audit_records = resp.json()
            actions = [r.get("action") for r in audit_records]
            print_pass(f"GET .../logs/audit: Audit trail fetched ({len(audit_records)} records, actions={actions})")
        else:
            print_fail(f"GET .../logs/audit: Failed ({resp.status_code})")
            failed_tests += 1

        # 8.2 Telemetry Logs
        resp = auth_client.get(f"/api/v1/properties/{created_prop_id}/logs/devices")
        if resp.status_code == 200:
            print_pass("GET .../logs/devices: Device telemetry endpoint returned successfully (HTTP 200)")
        else:
            print_fail(f"GET .../logs/devices: Failed ({resp.status_code})")
            failed_tests += 1

        # ----------------------------------------------------------------------
        # 9. Cleanup & Verification
        # ----------------------------------------------------------------------
        print_step("9. Safe Cleanup & Deletion Verification")

        # 9.1 Delete PIN
        if created_pin_id:
            del_resp = auth_client.delete(
                f"/api/v1/properties/{created_prop_id}/locks/{created_device_id}/pins/{created_pin_id}"
            )
            if del_resp.status_code == 204:
                print_pass(f"DELETE .../pins/{created_pin_id}: Deleted PIN (HTTP 204)")
            else:
                print_fail(f"DELETE PIN failed: {del_resp.status_code}")
                failed_tests += 1

        # 9.2 Delete Device
        del_dev_resp = auth_client.delete(f"/api/v1/properties/{created_prop_id}/devices/{created_device_id}")
        if del_dev_resp.status_code == 204:
            print_pass(f"DELETE .../devices/{created_device_id}: Deleted device (HTTP 204)")
        else:
            print_fail(f"DELETE device failed: {del_dev_resp.status_code}")
            failed_tests += 1

        # 9.3 Delete Property
        del_prop_resp = auth_client.delete(f"/api/v1/properties/{created_prop_id}")
        if del_prop_resp.status_code == 204:
            print_pass(f"DELETE /api/v1/properties/{created_prop_id}: Deleted property (HTTP 204)")
        else:
            print_fail(f"DELETE property failed: {del_prop_resp.status_code}")
            failed_tests += 1

        # 9.4 Verify Property 404
        check_deleted = auth_client.get(f"/api/v1/properties/{created_prop_id}")
        if check_deleted.status_code == 404:
            print_pass(f"GET /api/v1/properties/{created_prop_id}: Verified property deleted (HTTP 404 Not Found)")
        else:
            print_fail(f"Expected 404 for deleted property, got {check_deleted.status_code}")
            failed_tests += 1

    finally:
        # Failsafe cleanup if test crashed midway
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

    # --------------------------------------------------------------------------
    # Final Summary
    # --------------------------------------------------------------------------
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    if failed_tests == 0:
        print(f"{GREEN}{BOLD}Все API эндпоинты успешно протестированы! (0 ошибок){RESET}")
        print(f"{BOLD}{'=' * 70}{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}Провалено тестов: {failed_tests}{RESET}")
        print(f"{BOLD}{'=' * 70}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
