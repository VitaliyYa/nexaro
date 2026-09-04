import uuid

from src.services.pin_crypto import decrypt_pin


def test_lock_pins_encryption_and_audit_trail(client, mock_db, test_user):
    prop_id = str(uuid.uuid4())
    lock_id = "lock_front_door"

    pin_payload = {
        "device_id": lock_id,
        "name": "Guest: Alice",
        "pin": "123456",
        "valid_from": "2026-09-01T14:00:00Z",
        "valid_to": "2026-09-05T12:00:00Z",
    }

    # 1. Create PIN
    resp = client.post(f"/api/v1/properties/{prop_id}/locks/{lock_id}/pins", json=pin_payload)
    assert resp.status_code == 201
    created_pin = resp.json()
    assert created_pin["name"] == "Guest: Alice"
    assert "pin" not in created_pin  # Raw PIN is never exposed in response
    pin_id = created_pin["id"]

    # Verify that in database, pin_encrypted is encrypted and not raw '123456'
    db_record = mock_db.table("property_pins").store["property_pins"][0]
    assert db_record["pin_encrypted"] != "123456"
    assert decrypt_pin(db_record["pin_encrypted"]) == "123456"

    # Verify audit log recorded PIN creation
    audit_logs = mock_db.table("audit_logs").store["audit_logs"]
    assert len(audit_logs) == 1
    assert audit_logs[0]["action"] == "PIN_CREATED"
    assert audit_logs[0]["user_id"] == str(test_user.id)
    assert audit_logs[0]["details"]["pin_name"] == "Guest: Alice"
    assert "123456" not in str(audit_logs[0])  # PIN never logged!

    # 2. List PINs
    list_resp = client.get(f"/api/v1/properties/{prop_id}/locks/{lock_id}/pins")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Update PIN
    patch_resp = client.patch(
        f"/api/v1/properties/{prop_id}/locks/{lock_id}/pins/{pin_id}",
        json={"name": "Guest: Alice (Extended Stay)"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Guest: Alice (Extended Stay)"
    assert len(mock_db.table("audit_logs").store["audit_logs"]) == 2

    # 4. Delete PIN
    del_resp = client.delete(f"/api/v1/properties/{prop_id}/locks/{lock_id}/pins/{pin_id}")
    assert del_resp.status_code == 204
    assert len(mock_db.table("audit_logs").store["audit_logs"]) == 3


def test_permanent_pin_creation_and_defaults(client, mock_db, test_user):
    prop_id = str(uuid.uuid4())
    lock_id = "lock_main_entrance"

    # Create permanent PIN (no valid_to, using alias pin_name and pin_code)
    payload = {
        "pin_name": "Property Owner (Master)",
        "pin_code": "888999",
    }
    resp = client.post(f"/api/v1/properties/{prop_id}/locks/{lock_id}/pins", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "Property Owner (Master)"
    assert "2099" in created["valid_to"]
