import pytest_asyncio
import os
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.main import app
from app.dependencies import get_db
from app.models import Base

from app.models import User, UserRole
from app.security import hash_password

from decimal import Decimal

from app.models import Hospital, Equipment, EquipmentStatus
from app.models import WorkOrder, OrderPriority, OrderStatus


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set")


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client




@pytest_asyncio.fixture
async def test_users():
    async with TestSessionLocal() as session:
        users = [
            User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.CLINICAL_ADMIN,
            ),
            User(
                username="technician",
                hashed_password=hash_password("tech123"),
                role=UserRole.FIELD_TECHNICIAN,
            ),
            User(
                username="auditor",
                hashed_password=hash_password("audit123"),
                role=UserRole.AUDITOR,
            ),
        ]

        session.add_all(users)
        await session.commit()

        yield users

        for user in users:
            await session.delete(user)

        await session.commit()


@pytest_asyncio.fixture
async def test_equipment():
    async with TestSessionLocal() as session:
        hospital = Hospital(
            name="Test Hospital",
            location_region="Test Region",
            capacity=100,
            supervisor_id=999,
        )

        session.add(hospital)
        await session.flush()

        equipment = Equipment(
            serial_number="TEST-EQ-001",
            model="Test Equipment",
            status=EquipmentStatus.AVAILABLE,
            charge_level=Decimal("100.00"),
            facility_id=hospital.id,
        )

        session.add(equipment)
        await session.commit()
        await session.refresh(equipment)

        equipment_id = equipment.id

        yield equipment_id


@pytest_asyncio.fixture
async def test_work_order(test_equipment):
    async with TestSessionLocal() as session:
        work_order = WorkOrder(
            title="Test Repair",
            priority=OrderPriority.MEDIUM,
            status=OrderStatus.PENDING,
            equipment_id=test_equipment,
            technician_id=201,
        )

        session.add(work_order)
        await session.commit()
        await session.refresh(work_order)

        yield work_order.id

@pytest_asyncio.fixture
async def test_hospital():
    async with TestSessionLocal() as session:
        hospital = Hospital(
            name="Equipment Test Hospital",
            location_region="North",
            capacity=200,
            supervisor_id=777,
        )

        session.add(hospital)
        await session.commit()
        await session.refresh(hospital)

        yield hospital.id