import uuid


def test_logs_retrieval(client, mock_db, test_user):
    prop_id = str(uuid.uuid4())

    # Seed mock device_logs
    mock_db.table("device_logs").insert(
        [
            {
                "property_id": prop_id,
                "device_id": "sensor_leak",
                "topic": f"properties/{prop_id}/valve/sensor_leak/event",
                "event_type": "event",
                "payload": {"leak_detected": True, "valve_state": "CLOSED"},
            },
            {
                "property_id": prop_id,
                "device_id": "relay_1",
                "topic": f"properties/{prop_id}/relay/relay_1/state",
                "event_type": "state",
                "payload": {"state": "ON"},
            },
        ]
    ).execute()

    # Query device logs
    resp = client.get(f"/api/v1/properties/{prop_id}/logs/devices")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # Query filtered device logs
    resp_filtered = client.get(f"/api/v1/properties/{prop_id}/logs/devices?device_id=sensor_leak")
    assert resp_filtered.status_code == 200
    assert len(resp_filtered.json()) == 1

    # Query audit logs
    mock_db.table("audit_logs").insert(
        {
            "user_id": str(test_user.id),
            "property_id": prop_id,
            "action": "CONFIG_UPDATE",
            "details": {"key": "value"},
        }
    ).execute()

    audit_resp = client.get(f"/api/v1/properties/{prop_id}/logs/audit")
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) == 1
