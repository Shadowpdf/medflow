import pytest


@pytest.mark.asyncio
async def test_admin_login(client, test_users):
    response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_invalid_login(client, test_users):
    response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_me(client, test_users):
    login_response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    token = login_response.json()["access_token"]

    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "admin"
    assert data["role"] == "Clinical Admin"

@pytest.mark.asyncio
async def test_auth_me_without_token(client):
    response = await client.get("/auth/me")

    assert response.status_code == 401