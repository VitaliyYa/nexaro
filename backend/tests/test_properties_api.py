import uuid


def test_create_and_list_properties(client, test_user):
    # 1. Create property
    create_payload = {
        "name": "Luxury Apartment 101",
        "address": "123 Ocean View Blvd",
        "timezone": "America/New_York",
    }
    response = client.post("/api/v1/properties", json=create_payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Luxury Apartment 101"
    assert created["owner_id"] == str(test_user.id)
    prop_id = created["id"]

    # 2. Get property by ID
    get_resp = client.get(f"/api/v1/properties/{prop_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == prop_id

    # 3. List properties
    list_resp = client.get("/api/v1/properties")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == prop_id

    # 4. Update property
    update_resp = client.patch(f"/api/v1/properties/{prop_id}", json={"name": "Updated Apartment 101"})
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Apartment 101"

    # 5. Delete property
    del_resp = client.delete(f"/api/v1/properties/{prop_id}")
    assert del_resp.status_code == 204

    # 6. Verify deleted
    get_deleted = client.get(f"/api/v1/properties/{prop_id}")
    assert get_deleted.status_code == 404


def test_get_nonexistent_property(client):
    random_id = str(uuid.uuid4())
    resp = client.get(f"/api/v1/properties/{random_id}")
    assert resp.status_code == 404
