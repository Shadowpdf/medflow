import pytest


async def login(client, username, password):
    response = await client.post(
        "/auth/token",
        data={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.mark.asyncio
async def test_authenticated_user_can_get_equipment(
    client,
    test_users,
):
    headers = await login(
        client,
        "auditor",
        "audit123",
    )

    response = await client.get(
        "/equipment/",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_get_equipment(client):
    response = await client.get("/equipment/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_get_equipment_by_id(
    client,
    test_users,
    test_equipment,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    # test_equipment already created a hospital,
    # so we'll use its facility through a new test fixture
    response = await client.get(
        f"/equipment/{test_equipment}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == test_equipment
    assert data["serial_number"] == "TEST-EQ-001"
    assert data["model"] == "Test Equipment"
    assert data["status"] == "Available"


@pytest.mark.asyncio
async def test_technician_cannot_create_equipment(
    client,
    test_users,
):
    headers = await login(
        client,
        "technician",
        "tech123",
    )

    response = await client.post(
        "/equipment/",
        headers=headers,
        json={
            "serial_number": "NO-PERMISSION-001",
            "model": "Unauthorized Equipment",
            "status": "Available",
            "charge_level": 100.00,
            "facility_id": 999999,
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_missing_equipment_returns_404(
    client,
    test_users,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.get(
        "/equipment/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Equipment not found"


@pytest.mark.asyncio
async def test_admin_can_create_equipment(
    client,
    test_users,
    test_hospital,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.post(
        "/equipment/",
        headers=headers,
        json={
            "serial_number": "POST-TEST-001",
            "model": "Test Ventilator",
            "status": "Available",
            "charge_level": 95.50,
            "facility_id": test_hospital,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["serial_number"] == "POST-TEST-001"
    assert data["model"] == "Test Ventilator"
    assert data["status"] == "Available"
    assert float(data["charge_level"]) == 95.50
    assert data["facility_id"] == test_hospital
    assert "id" in data