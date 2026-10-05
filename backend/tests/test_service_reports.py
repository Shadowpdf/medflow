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
async def test_authenticated_user_can_get_service_reports(
    client,
    test_users,
):
    headers = await login(
        client,
        "auditor",
        "audit123",
    )

    response = await client.get(
        "/service-reports/",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_get_service_reports(
    client,
):
    response = await client.get("/service-reports/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_create_service_report(
    client,
    test_users,
    test_work_order,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.post(
        "/service-reports/",
        headers=headers,
        json={
            "work_order_id": test_work_order,
            "file_url": "reports/admin-test.pdf",
            "notes": "Created by admin test.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["work_order_id"] == test_work_order
    assert data["file_url"] == "reports/admin-test.pdf"
    assert data["notes"] == "Created by admin test."
    assert "id" in data


@pytest.mark.asyncio
async def test_technician_can_create_service_report(
    client,
    test_users,
    test_work_order,
):
    headers = await login(
        client,
        "technician",
        "tech123",
    )

    response = await client.post(
        "/service-reports/",
        headers=headers,
        json={
            "work_order_id": test_work_order,
            "file_url": "reports/technician-test.pdf",
            "notes": "Created by technician test.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["work_order_id"] == test_work_order
    assert data["file_url"] == "reports/technician-test.pdf"


@pytest.mark.asyncio
async def test_auditor_cannot_create_service_report(
    client,
    test_users,
    test_work_order,
):
    headers = await login(
        client,
        "auditor",
        "audit123",
    )

    response = await client.post(
        "/service-reports/",
        headers=headers,
        json={
            "work_order_id": test_work_order,
            "file_url": "reports/unauthorized.pdf",
            "notes": "This should not be created.",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_missing_service_report_returns_404(
    client,
    test_users,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.get(
        "/service-reports/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Service report not found"