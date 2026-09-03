import uuid


def test_device_crud_lifecycle(client):
    prop_id = str(uuid.uuid4())

    # 1. Create Device
    device_payload = {
        "id": "switch_main",
        "device_type": "relay",
        "name": "Main Water Heater",
        "is_active": True,
        "settings": {"auto_off_minutes": 30},
    }
    resp = client.post(f"/api/v1/properties/{prop_id}/devices", json=device_payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"] == "switch_main"
    assert created["property_id"] == prop_id
    assert created["device_type"] == "relay"

    # 2. List Devices for Property
    list_resp = client.get(f"/api/v1/properties/{prop_id}/devices")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Get Device
    get_resp = client.get(f"/api/v1/properties/{prop_id}/devices/switch_main")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Main Water Heater"

    # 4. Update Device
    patch_resp = client.patch(
        f"/api/v1/properties/{prop_id}/devices/switch_main",
        json={"name": "Renamed Switch", "is_active": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Renamed Switch"
    assert patch_resp.json()["is_active"] is False

    # 5. Delete Device
    del_resp = client.delete(f"/api/v1/properties/{prop_id}/devices/switch_main")
    assert del_resp.status_code == 204

    # 6. Verify Not Found
    get_del = client.get(f"/api/v1/properties/{prop_id}/devices/switch_main")
    assert get_del.status_code == 404
