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
async def test_admin_can_create_work_order(
    client,
    test_users,
    test_equipment,
):
    headers = await login(client, "admin", "admin123")

    response = await client.post(
        "/work-orders/",
        headers=headers,
        json={
            "title": "Test Work Order",
            "priority": "Medium",
            "status": "Pending",
            "equipment_id": test_equipment,
            "technician_id": 201,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Test Work Order"
    assert data["priority"] == "Medium"
    assert data["status"] == "Pending"
    assert data["equipment_id"] == test_equipment


@pytest.mark.asyncio
async def test_technician_cannot_create_work_order(client, test_users):
    headers = await login(
        client,
        "technician",
        "tech123",
    )

    response = await client.post(
        "/work-orders/",
        headers=headers,
        json={
            "title": "Unauthorized Work Order",
            "priority": "Medium",
            "status": "Pending",
            "equipment_id": 1,
            "technician_id": 201,
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_auditor_cannot_create_work_order(client, test_users):
    headers = await login(
        client,
        "auditor",
        "audit123",
    )

    response = await client.post(
        "/work-orders/",
        headers=headers,
        json={
            "title": "Unauthorized Work Order",
            "priority": "Low",
            "status": "Pending",
            "equipment_id": 1,
            "technician_id": 201,
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_update_work_order_status(
    client,
    test_users,
    test_work_order,
):
    headers = await login(client, "admin", "admin123")

    response = await client.patch(
        f"/work-orders/{test_work_order}/status",
        headers=headers,
        json={"status": "Completed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Completed"


@pytest.mark.asyncio
async def test_technician_can_update_work_order_status(
    client,
    test_users,
    test_work_order,
):
    headers = await login(client, "technician", "tech123")

    response = await client.patch(
        f"/work-orders/{test_work_order}/status",
        headers=headers,
        json={"status": "In-Progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In-Progress"


@pytest.mark.asyncio
async def test_auditor_cannot_update_work_order_status(
    client,
    test_users,
    test_work_order,
):
    headers = await login(client, "auditor", "audit123")

    response = await client.patch(
        f"/work-orders/{test_work_order}/status",
        headers=headers,
        json={"status": "Completed"},
    )

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_authenticated_user_can_get_work_orders(
    client,
    test_users,
):
    headers = await login(
        client,
        "auditor",
        "audit123",
    )

    response = await client.get(
        "/work-orders/",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_work_order_by_id(
    client,
    test_users,
    test_work_order,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.get(
        f"/work-orders/{test_work_order}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == test_work_order
    assert data["title"] == "Test Repair"
    assert data["status"] == "Pending"


@pytest.mark.asyncio
async def test_missing_work_order_returns_404(
    client,
    test_users,
):
    headers = await login(
        client,
        "admin",
        "admin123",
    )

    response = await client.get(
        "/work-orders/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Work order not found"