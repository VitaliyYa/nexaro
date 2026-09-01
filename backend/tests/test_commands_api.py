import uuid


def test_send_relay_command(client, mock_db, mock_mqtt):
    prop_id = str(uuid.uuid4())
    device_id = "switch_boiler"

    # Register device in DB
    mock_db.table("devices").insert(
        {
            "id": device_id,
            "property_id": prop_id,
            "device_type": "relay",
            "name": "Water Boiler",
            "is_active": True,
        }
    ).execute()

    # Send command
    cmd_resp = client.post(
        f"/api/v1/properties/{prop_id}/devices/{device_id}/command",
        json={"command": "ON"},
    )
    assert cmd_resp.status_code == 200
    res = cmd_resp.json()
    assert res["status"] == "published"
    assert res["topic"] == f"properties/{prop_id}/relay/{device_id}/set"

    # Verify MQTT publish params
    assert len(mock_mqtt.published_messages) == 1
    published = mock_mqtt.published_messages[0]
    assert published["topic"] == f"properties/{prop_id}/relay/{device_id}/set"
    assert published["qos"] == 1
    assert published["retain"] is False
    assert published["payload"]["command"] == "ON"


def test_send_lock_command_and_audit(client, mock_db, mock_mqtt, test_user):
    prop_id = str(uuid.uuid4())
    lock_id = "door_lock_front"

    mock_db.table("devices").insert(
        {
            "id": lock_id,
            "property_id": prop_id,
            "device_type": "lock",
            "name": "Front Door Lock",
            "is_active": True,
        }
    ).execute()

    cmd_resp = client.post(
        f"/api/v1/properties/{prop_id}/devices/{lock_id}/command",
        json={"command": "UNLOCK", "duration_seconds": 10},
    )
    assert cmd_resp.status_code == 200
    res = cmd_resp.json()
    assert res["topic"] == f"properties/{prop_id}/lock/{lock_id}/set"

    # Verify audit log for lock operation
    audit_logs = mock_db.table("audit_logs").store.get("audit_logs", [])
    assert len(audit_logs) == 1
    assert audit_logs[0]["action"] == "LOCK_COMMAND_UNLOCK"
    assert audit_logs[0]["user_id"] == str(test_user.id)


def test_send_invalid_command_rejected(client, mock_db):
    prop_id = str(uuid.uuid4())
    device_id = "switch_kitchen"

    mock_db.table("devices").insert(
        {
            "id": device_id,
            "property_id": prop_id,
            "device_type": "relay",
            "name": "Kitchen Light",
            "is_active": True,
        }
    ).execute()

    # Invalid command for relay (must be ON, OFF, TOGGLE)
    cmd_resp = client.post(
        f"/api/v1/properties/{prop_id}/devices/{device_id}/command",
        json={"command": "INVALID_STATE"},
    )
    assert cmd_resp.status_code == 422


def test_send_command_nonexistent_device(client):
    prop_id = str(uuid.uuid4())
    cmd_resp = client.post(
        f"/api/v1/properties/{prop_id}/devices/nonexistent/command",
        json={"command": "ON"},
    )
    assert cmd_resp.status_code == 404
