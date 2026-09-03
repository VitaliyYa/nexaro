import uuid

from src.services.mqtt_auth_service import hash_password_pbkdf2


def test_mqtt_user_auth_superuser(client):
    from src.config import get_settings

    settings = get_settings()
    response = client.post(
        "/api/v1/auth/mqtt/user",
        json={
            "username": settings.MQTT_WORKER_USERNAME or "backend_worker",
            "password": settings.MQTT_WORKER_PASSWORD or "test_worker_pass",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mqtt_user_auth_edge_user(client, mock_db):
    prop_id = str(uuid.uuid4())
    pw_hash = hash_password_pbkdf2("edge_secret_pass")
    mock_db.table("mqtt_credentials").insert(
        {
            "username": "edge_prop_123",
            "password_hash": pw_hash,
            "property_id": prop_id,
            "is_active": True,
        }
    ).execute()

    # Valid password
    resp = client.post(
        "/api/v1/auth/mqtt/user",
        json={
            "username": "edge_prop_123",
            "password": "edge_secret_pass",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["property_id"] == prop_id

    # Wrong password
    resp_wrong = client.post(
        "/api/v1/auth/mqtt/user",
        json={
            "username": "edge_prop_123",
            "password": "wrong_password",
        },
    )
    assert resp_wrong.status_code == 401


def test_mqtt_superuser_webhook(client):
    # Backend worker is superuser
    resp_ok = client.post("/api/v1/auth/mqtt/superuser", json={"username": "backend_worker"})
    assert resp_ok.status_code == 200

    # Normal edge node is not superuser
    resp_bad = client.post("/api/v1/auth/mqtt/superuser", json={"username": "edge_user_456"})
    assert resp_bad.status_code == 403


def test_mqtt_acl_check_enforces_property_isolation(client, mock_db):
    prop_id_1 = str(uuid.uuid4())
    prop_id_2 = str(uuid.uuid4())

    mock_db.table("mqtt_credentials").insert(
        {
            "username": "edge_node_p1",
            "password_hash": "dummy",
            "property_id": prop_id_1,
            "is_active": True,
        }
    ).execute()

    # Allowed: Publish state in own property namespace (acc=2)
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": "edge_node_p1",
            "topic": f"properties/{prop_id_1}/relay/switch1/state",
            "acc": 2,
        },
    )
    assert resp.status_code == 200

    # Allowed: Subscribe to set in own property namespace (acc=1)
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": "edge_node_p1",
            "topic": f"properties/{prop_id_1}/relay/switch1/set",
            "acc": 1,
        },
    )
    assert resp.status_code == 200

    # DENIED: Cross-tenant publish to another property (acc=2)
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": "edge_node_p1",
            "topic": f"properties/{prop_id_2}/relay/switch1/state",
            "acc": 2,
        },
    )
    assert resp.status_code == 403

    # DENIED: Edge node trying to publish to /set command topic
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": "edge_node_p1",
            "topic": f"properties/{prop_id_1}/relay/switch1/set",
            "acc": 2,
        },
    )
    assert resp.status_code == 403


def test_mqtt_acl_superuser_allowed_all_properties(client):
    resp = client.post(
        "/api/v1/auth/mqtt/acl",
        json={
            "username": "backend_worker",
            "topic": "properties/any_prop/relay/r1/set",
            "acc": 2,
        },
    )
    assert resp.status_code == 200


def test_openapi_schema_has_no_broken_defs_references():
    import json

    from src.main import app

    schema = app.openapi()
    schema_str = json.dumps(schema)
    assert "#/$defs" not in schema_str

    acl_body = schema["paths"]["/api/v1/auth/mqtt/acl"]["post"]["requestBody"]["content"]
    assert "application/json" in acl_body
    assert "application/x-www-form-urlencoded" in acl_body
    assert "$ref" not in json.dumps(acl_body)
