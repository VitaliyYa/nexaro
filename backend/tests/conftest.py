import uuid
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient

from src.auth.jwt import get_current_user
from src.auth.models import CurrentUser
from src.auth.supabase import get_supabase_admin_client, get_supabase_client
from src.config import Settings, get_settings
from src.main import app
from src.mqtt.client import get_mqtt_service


class MockPostgrestResponse:
    def __init__(self, data: list[dict[str, Any]] | None = None):
        self.data = data if data is not None else []


class MockQueryBuilder:
    def __init__(self, table_name: str, db_store: dict[str, list[dict[str, Any]]]):
        self.table_name = table_name
        self.db_store = db_store
        self.store = db_store
        self._filters: list[tuple[str, Any]] = []
        self._order_by: str | None = None
        self._limit_val: int | None = None
        self._action = "select"
        self._payload: dict[str, Any] | None = None

    def select(self, *args, **kwargs):
        self._action = "select"
        return self

    def insert(self, payload: dict[str, Any] | list[dict[str, Any]]):
        self._action = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict[str, Any]):
        self._action = "update"
        self._payload = payload
        return self

    def delete(self):
        self._action = "delete"
        return self

    def eq(self, column: str, value: Any):
        self._filters.append((column, value))
        return self

    def order(self, column: str, desc: bool = False):
        self._order_by = column
        return self

    def limit(self, count: int):
        self._limit_val = count
        return self

    def execute(self) -> MockPostgrestResponse:
        records = self.db_store.setdefault(self.table_name, [])

        if self._action == "insert":
            new_records = self._payload if isinstance(self._payload, list) else [self._payload]
            inserted = []
            for r in new_records:
                record = dict(r)
                if "id" not in record:
                    if self.table_name in ("device_logs", "audit_logs"):
                        record["id"] = len(records) + 1
                    else:
                        record["id"] = str(uuid.uuid4())
                if "created_at" not in record:
                    record["created_at"] = "2026-09-01T12:00:00Z"
                if "updated_at" not in record:
                    record["updated_at"] = "2026-09-01T12:00:00Z"
                records.append(record)
                inserted.append(record)
            return MockPostgrestResponse(inserted)

        # Filter matching records
        matching_indices = []
        for i, row in enumerate(records):
            match = True
            for col, val in self._filters:
                if str(row.get(col)) != str(val):
                    match = False
                    break
            if match:
                matching_indices.append(i)

        if self._action == "select":
            result = [records[i] for i in matching_indices]
            if self._limit_val:
                result = result[: self._limit_val]
            return MockPostgrestResponse(result)

        elif self._action == "update":
            updated = []
            for i in matching_indices:
                records[i].update(self._payload or {})
                records[i]["updated_at"] = "2026-09-01T12:00:00Z"
                updated.append(records[i])
            return MockPostgrestResponse(updated)

        elif self._action == "delete":
            deleted = []
            for i in reversed(matching_indices):
                deleted.append(records.pop(i))
            return MockPostgrestResponse(deleted)

        return MockPostgrestResponse([])


class MockSupabaseClient:
    def __init__(self):
        self.store: dict[str, list[dict[str, Any]]] = {}

    def table(self, table_name: str) -> MockQueryBuilder:
        return MockQueryBuilder(table_name, self.store)


class MockMqttService:
    def __init__(self):
        self.published_messages: list[dict[str, Any]] = []
        self._connected = True

    def publish_command(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> bool:
        self.published_messages.append(
            {
                "topic": topic,
                "payload": payload,
                "qos": qos,
                "retain": retain,
            }
        )
        return True

    @property
    def is_connected(self) -> bool:
        return self._connected


@pytest.fixture
def mock_db() -> MockSupabaseClient:
    return MockSupabaseClient()


@pytest.fixture
def mock_mqtt() -> MockMqttService:
    return MockMqttService()


@pytest.fixture
def test_user() -> CurrentUser:
    user_id = uuid.uuid4()
    secret = "secret_key_with_at_least_32_characters_for_hmac_sha256"
    raw_token = jwt.encode({"sub": str(user_id), "email": "owner@example.com"}, secret, algorithm="HS256")
    return CurrentUser(
        id=user_id,
        email="owner@example.com",
        role="authenticated",
        token=raw_token,
    )


@pytest.fixture
def client(mock_db: MockSupabaseClient, mock_mqtt: MockMqttService, test_user: CurrentUser) -> TestClient:
    app.dependency_overrides[get_supabase_client] = lambda: mock_db
    app.dependency_overrides[get_supabase_admin_client] = lambda: mock_db
    app.dependency_overrides[get_mqtt_service] = lambda: mock_mqtt
    app.dependency_overrides[get_current_user] = lambda: test_user
    base_settings = get_settings()
    app.dependency_overrides[get_settings] = lambda: Settings(
        ENVIRONMENT="test",
        MQTT_WORKER_USERNAME=base_settings.MQTT_WORKER_USERNAME or "backend_worker",
        MQTT_WORKER_PASSWORD=base_settings.MQTT_WORKER_PASSWORD or "test_worker_pass",
        PIN_ENCRYPTION_KEY=base_settings.PIN_ENCRYPTION_KEY or "k5M7j0v9y9mE2q_u2bW2Zg3d1K4t6F8s0A2b4C6d8E0=",
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
