#!/usr/bin/env python3
"""
Live API and Mosquitto Webhooks Integration Test Script for SmartRent.

Runs real HTTP requests against a running SmartRent backend (http://127.0.0.1:8000)
and validates live API responses for health checks and Mosquitto authentication.
"""

import sys

import httpx

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


def main():
    settings = get_settings()
    base_url = "http://127.0.0.1:8000"
    worker_username = settings.MQTT_WORKER_USERNAME or "backend_worker"
    worker_password = settings.MQTT_WORKER_PASSWORD

    print(f"{BOLD}{'=' * 65}{RESET}")
    print(f"{BOLD}SmartRent Live API & Mosquitto Webhook Integration Tests{RESET}")
    print(f"{BOLD}{'=' * 65}{RESET}")
    print(f"Target API:        {base_url}")
    print(f"Worker Username:   {worker_username}")
    print(f"Worker Password:   {'*' * len(worker_password) if worker_password else '<empty>'}")
    print(f"Environment:       {settings.ENVIRONMENT}")

    client = httpx.Client(base_url=base_url, timeout=5.0)
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
        print(f"\n{YELLOW}Подсказка: убедитесь, что бэкенд запущен:{RESET}")
        print("  uv run uvicorn src.main:app --reload --port 8000\n")
        return 1

    # --------------------------------------------------------------------------
    # 2. Mosquitto /user Webhook
    # --------------------------------------------------------------------------
    print_step("2. POST /api/v1/auth/mqtt/user - Broker User Authentication")

    # 2.1 Valid worker credentials
    resp = client.post(
        "/api/v1/auth/mqtt/user",
        json={"username": worker_username, "password": worker_password},
    )
    if resp.status_code == 200 and resp.json().get("status") == "ok":
        print_pass("Valid worker credentials accepted (HTTP 200, status=ok)")
    else:
        print_fail(f"Valid credentials rejected: {resp.status_code} {resp.text}")
        failed_tests += 1

    # 2.2 Invalid password
    resp = client.post(
        "/api/v1/auth/mqtt/user",
        json={"username": worker_username, "password": "wrong_invalid_password_123"},
    )
    if resp.status_code == 401:
        print_pass("Invalid password rejected as expected (HTTP 401 Unauthorized)")
    else:
        print_fail(f"Expected HTTP 401 for bad password, got {resp.status_code}: {resp.text}")
        failed_tests += 1

    # 2.3 Form-urlencoded format test (as Mosquitto may send)
    resp = client.post(
        "/api/v1/auth/mqtt/user",
        data={"username": worker_username, "password": worker_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code == 200 and resp.json().get("status") == "ok":
        print_pass("Form-urlencoded format accepted (HTTP 200, status=ok)")
    else:
        print_fail(f"Form-urlencoded rejected: {resp.status_code} {resp.text}")
        failed_tests += 1

    # --------------------------------------------------------------------------
    # 3. Mosquitto /superuser Webhook
    # --------------------------------------------------------------------------
    print_step("3. POST /api/v1/auth/mqtt/superuser - Superuser Check")

    # 3.1 Worker is superuser
    resp = client.post(
        "/api/v1/auth/mqtt/superuser",
        json={"username": worker_username},
    )
    if resp.status_code == 200 and resp.json().get("superuser") is True:
        print_pass(f"'{worker_username}' is recognized as superuser (HTTP 200)")
    else:
        print_fail(f"Worker superuser check failed: {resp.status_code} {resp.text}")
        failed_tests += 1

    # 3.2 Unknown user is not superuser
    resp = client.post(
        "/api/v1/auth/mqtt/superuser",
        json={"username": "random_edge_node"},
    )
    if resp.status_code == 403:
        print_pass("Non-worker user rejected as superuser (HTTP 403 Forbidden)")
    else:
        print_fail(f"Expected HTTP 403 for non-worker, got {resp.status_code}: {resp.text}")
        failed_tests += 1

    # --------------------------------------------------------------------------
    # 4. Mosquitto /acl Webhook
    # --------------------------------------------------------------------------
    print_step("4. POST /api/v1/auth/mqtt/acl - Multi-tenant Topic ACL Isolation")

    # 4.1 Backend worker superuser write access across properties
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": worker_username,
            "topic": "properties/prop_test_123/relay/switch1/set",
            "acc": 2,
        },
    )
    if resp.status_code == 200 and resp.json().get("allowed") is True:
        print_pass("Superuser granted access to 'properties/+/+/+/set' (HTTP 200)")
    else:
        print_fail(f"Superuser ACL check failed: {resp.status_code} {resp.text}")
        failed_tests += 1

    # 4.2 Backend worker out-of-scope topic blocked
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": worker_username,
            "topic": "other_service/unauthorized/topic",
            "acc": 2,
        },
    )
    if resp.status_code == 403:
        print_pass("Out-of-scope topic denied even for superuser (HTTP 403 Forbidden)")
    else:
        print_fail(f"Expected HTTP 403 for out-of-scope topic, got {resp.status_code}: {resp.text}")
        failed_tests += 1

    # 4.3 Unknown edge node blocked
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": "unknown_edge_node",
            "topic": "properties/prop_test_123/relay/switch1/state",
            "acc": 2,
        },
    )
    if resp.status_code == 403:
        print_pass("Unknown edge user denied topic access (HTTP 403 Forbidden)")
    else:
        print_fail(f"Expected HTTP 403 for unknown edge node, got {resp.status_code}: {resp.text}")
        failed_tests += 1

    # --------------------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------------------
    print(f"\n{BOLD}{'=' * 65}{RESET}")
    if failed_tests == 0:
        print(f"{GREEN}{BOLD}Все API тесты успешно пройдены! (0 ошибок){RESET}")
        print(f"{BOLD}{'=' * 65}{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}Провалено тестов: {failed_tests}{RESET}")
        print(f"{BOLD}{'=' * 65}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
