import json
import uuid

from src.mqtt.worker import MqttWorker, parse_and_validate_payload


def test_parse_and_validate_relay_state():
    raw = json.dumps({"state": "ON", "power_w": 120.5, "voltage_v": 230.0, "timestamp": "2026-09-01T12:00:00Z"})
    parsed = parse_and_validate_payload("relay", "state", raw)
    assert parsed["state"] == "ON"
    assert parsed["power_w"] == 120.5


def test_parse_and_validate_lock_state():
    raw = json.dumps(
        {
            "state": "locked",
            "battery": 85,
            "last_trigger": "passcode",
            "timestamp": "2026-09-01T12:00:00Z",
        }
    )
    parsed = parse_and_validate_payload("lock", "state", raw)
    assert parsed["state"] == "locked"
    assert parsed["battery"] == 85


def test_parse_and_validate_climate_state():
    raw = json.dumps(
        {
            "current_temperature": 22.5,
            "target_temperature": 21.0,
            "hvac_mode": "cool",
            "is_powered": True,
            "timestamp": "2026-09-01T12:00:00Z",
        }
    )
    parsed = parse_and_validate_payload("climate", "state", raw)
    assert parsed["current_temperature"] == 22.5
    assert parsed["hvac_mode"] == "cool"


def test_parse_and_validate_valve_event():
    raw = json.dumps(
        {
            "leak_detected": True,
            "valve_state": "CLOSED",
            "auto_closed": True,
            "timestamp": "2026-09-01T12:00:00Z",
        }
    )
    parsed = parse_and_validate_payload("valve", "event", raw)
    assert parsed["leak_detected"] is True
    assert parsed["valve_state"] == "CLOSED"


def test_parse_and_validate_node_availability():
    raw = json.dumps(
        {
            "status": "online",
            "node_id": "haos_gateway_01",
            "timestamp": "2026-09-01T12:00:00Z",
        }
    )
    parsed = parse_and_validate_payload("node", "availability", raw)
    assert parsed["status"] == "online"
    assert parsed["node_id"] == "haos_gateway_01"


def test_worker_process_message(mock_db):
    prop_id = str(uuid.uuid4())
    device_id = "switch_kitchen"

    # Pre-populate device
    mock_db.table("devices").insert(
        {
            "id": device_id,
            "property_id": prop_id,
            "device_type": "relay",
            "name": "Kitchen Switch",
            "is_active": True,
        }
    ).execute()

    worker = MqttWorker(admin_client=mock_db)

    # Process state message
    state_payload = json.dumps({"state": "ON", "timestamp": "2026-09-01T12:00:00Z"})
    topic = f"properties/{prop_id}/relay/{device_id}/state"
    worker.process_message(topic, state_payload)

    # Verify device_logs has entry
    logs = mock_db.table("device_logs").store["device_logs"]
    assert len(logs) == 1
    assert logs[0]["property_id"] == prop_id
    assert logs[0]["device_id"] == device_id
    assert logs[0]["event_type"] == "state"
    assert logs[0]["payload"]["state"] == "ON"

    # Verify devices last_seen was updated
    device_rec = mock_db.table("devices").store["devices"][0]
    assert "last_seen" in device_rec
