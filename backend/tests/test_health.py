import pytest
from app.main import app
from app.dependencies import get_db
from unittest.mock import AsyncMock
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

mock_db = AsyncMock()
mock_db.execute.side_effect = ConnectionError("Database unavailable")


async def failing_get_db():
    raise ConnectionError("Simulated database failure")
    yield


async def override_get_db_failure():
    yield mock_db


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "MedFlow API is running"}


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready(client):
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_health_fail(client):
    # creates a restore point of the orginal db
    original_override = app.dependency_overrides.get(get_db)

    try:
        # forces the db the should fail
        app.dependency_overrides[get_db] = override_get_db_failure

        response = await client.get("/health/ready")

        assert response.status_code == 503
        assert response.json() == {"detail": "Database is unreachable"}

    finally:
        # actually restores the db back to the restore created above
        if original_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_override


@pytest.mark.asyncio
async def test_health_detail_no_auth(client):
    response = await client.get("/health/detail")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_detail_forbidden(client, test_users):

    response = await client.post(
        "/auth/token",
        data={
            "username": "technician",
            "password": "tech123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(
        "/health/detail",
        headers=headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_health_detail_admin(client, test_users):
    response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    with patch(
        "app.routers.health.s3.head_bucket",
        return_value={},
    ):
        response = await client.get(
            "/health/detail",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_s3_failure(client, test_users):
    response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    with patch(
        "app.routers.health.s3.head_bucket",
        side_effect=ConnectionError("Simulated S3 failure"),
    ):
        response = await client.get(
            "/health/detail",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["database"] == "healthy"
    assert response.json()["s3"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_detail_db_failure(client, test_users):
    response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    original_execute = AsyncSession.execute

    async def execute_with_failure(self, statement, *args, **kwargs):
        if str(statement).strip() == "SELECT 1":
            raise ConnectionError("Simulated database failure")

        return await original_execute(self, statement, *args, **kwargs)

    with patch.object(
        AsyncSession,
        "execute",
        side_effect=execute_with_failure,
        autospec=True,
    ):
        response = await client.get(
            "/health/detail",
            headers={"Authorization": f"Bearer {token}"},
        )

    with (
        patch.object(
            AsyncSession,
            "execute",
            side_effect=execute_with_failure,
            autospec=True,
        ),
        patch("app.routers.health.s3.head_bucket", return_value={}),
    ):
        response = await client.get(
            "/health/detail",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["database"] == "unhealthy"
    assert response.json()["s3"] == "healthy"
