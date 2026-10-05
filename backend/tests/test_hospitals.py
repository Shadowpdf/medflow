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
async def test_authenticated_user_can_get_hospitals(
    client,
    test_users,
):
    headers = await login(
        client,
        "auditor",
        "audit123",
    )

    response = await client.get(
        "/hospitals/",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_get_hospitals(client):
    response = await client.get("/hospitals/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_create_hospital(
    client,
    test_users,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.post(
        "/hospitals/",
        headers=headers,
        json={
            "name": "Unit Test Medical Center",
            "location_region": "East",
            "capacity": 250,
            "supervisor_id": 500,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Unit Test Medical Center"
    assert data["location_region"] == "East"
    assert data["capacity"] == 250
    assert data["supervisor_id"] == 500
    assert "id" in data


@pytest.mark.asyncio
async def test_technician_cannot_create_hospital(
    client,
    test_users,
):
    headers = await login(
        client,
        "technician",
        "tech123",
    )

    response = await client.post(
        "/hospitals/",
        headers=headers,
        json={
            "name": "Unauthorized Hospital",
            "location_region": "West",
            "capacity": 100,
            "supervisor_id": 501,
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_missing_hospital_returns_404(
    client,
    test_users,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.get(
        "/hospitals/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Hospital not found"