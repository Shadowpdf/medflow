import pytest

from decimal import Decimal

from app.models import Equipment, Hospital, EquipmentStatus
from app.models.enums import OrderPriority, OrderStatus
from tests.conftest import TestSessionLocal

from sqlalchemy import delete
from app.models import Technician, WorkOrder


@pytest.mark.asyncio
async def test_low_charge_requires_authentication(client):
    response = await client.get("/analytics/low-charge")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_low_charge_authenticated(client, test_users):
    login_response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = await client.get(
        "/analytics/low-charge",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "devices" in data
    assert isinstance(data["devices"], list)


@pytest.mark.asyncio
async def test_low_charge_filters_equipment(client, test_users):
    async with TestSessionLocal() as session:
        hospital = Hospital(
            name="Analytics Test Hospital",
            location_region="Test Region",
            capacity=100,
            supervisor_id=999,
        )

        session.add(hospital)
        await session.flush()

        test_devices = [
            ("TEST-LOW-01", EquipmentStatus.AVAILABLE, "15.00"),
            ("TEST-LOW-02", EquipmentStatus.IN_USE, "19.99"),
            ("TEST-HIGH-01", EquipmentStatus.AVAILABLE, "20.00"),
            ("TEST-MAINT-01", EquipmentStatus.MAINTENANCE, "10.00"),
            ("TEST-OFFLINE-01", EquipmentStatus.OFFLINE, "5.00"),
        ]

        for serial, status, charge in test_devices:
            session.add(
                Equipment(
                    serial_number=serial,
                    model="Analytics Test Device",
                    status=status,
                    charge_level=Decimal(charge),
                    facility_id=hospital.id,
                )
            )

        await session.commit()

        device_serials = [device[0] for device in test_devices]

    try:
        login_response = await client.post(
            "/auth/token",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await client.get(
            "/analytics/low-charge",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        returned_serials = {
            device["serial_number"] for device in response.json()["devices"]
        }

        assert returned_serials.intersection(device_serials) == {
            "TEST-LOW-01",
            "TEST-LOW-02",
        }

    finally:
        async with TestSessionLocal() as session:
            from sqlalchemy import delete

            await session.execute(
                delete(Equipment).where(Equipment.serial_number.in_(device_serials))
            )
            await session.delete(await session.get(Hospital, hospital.id))
            await session.commit()


@pytest.mark.asyncio
async def test_colocation_requires_authentication(client):
    response = await client.get("/analytics/co-location")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_colocation_authenticated(client, test_users):
    login_response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = await client.get(
        "/analytics/co-location",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "discrepancies" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["discrepancies"], list)


@pytest.mark.asyncio
async def test_colocation_counts_unique_devices(client, test_users):
    async with TestSessionLocal() as session:
        hospital_a = Hospital(
            name="CoLocation Hospital A",
            location_region="North",
            capacity=100,
            supervisor_id=900,
        )

        hospital_b = Hospital(
            name="CoLocation Hospital B",
            location_region="South",
            capacity=100,
            supervisor_id=901,
        )

        session.add_all([hospital_a, hospital_b])
        await session.flush()

        technician_a = Technician(
            name="Local Technician",
            facility_id=hospital_a.id,
            supervisor_id=900,
        )

        technician_b = Technician(
            name="Remote Technician",
            facility_id=hospital_b.id,
            supervisor_id=901,
        )

        session.add_all([technician_a, technician_b])
        await session.flush()

        equipment = Equipment(
            serial_number="TEST-COLOC-001",
            model="CoLocation Test Device",
            status=EquipmentStatus.AVAILABLE,
            charge_level=Decimal("80.00"),
            facility_id=hospital_a.id,
        )

        session.add(equipment)
        await session.flush()

        orders = [
            WorkOrder(
                title="Local Assignment",
                priority=OrderPriority.MEDIUM,
                status=OrderStatus.PENDING,
                equipment_id=equipment.id,
                technician_id=technician_a.id,
            ),
            WorkOrder(
                title="Remote Assignment 1",
                priority=OrderPriority.MEDIUM,
                status=OrderStatus.PENDING,
                equipment_id=equipment.id,
                technician_id=technician_b.id,
            ),
            WorkOrder(
                title="Remote Assignment 2",
                priority=OrderPriority.MEDIUM,
                status=OrderStatus.PENDING,
                equipment_id=equipment.id,
                technician_id=technician_b.id,
            ),
        ]

        session.add_all(orders)
        await session.commit()

        equipment_id = equipment.id
        remote_technician_id = technician_b.id
        hospital_a_id = hospital_a.id
        hospital_b_id = hospital_b.id

    try:
        login_response = await client.post(
            "/auth/token",
            data={"username": "admin", "password": "admin123"},
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await client.get(
            "/analytics/co-location",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        matching = [
            item
            for item in data["discrepancies"]
            if item["equipment_id"] == equipment_id
        ]

        assert len(matching) == 1
        assert matching[0]["technician_id"] == remote_technician_id
        assert matching[0]["equipment_facility_id"] == hospital_a_id
        assert matching[0]["technician_facility_id"] == hospital_b_id

        assert equipment_id in {item["equipment_id"] for item in data["discrepancies"]}

    finally:
        async with TestSessionLocal() as session:
            await session.execute(
                delete(WorkOrder).where(WorkOrder.equipment_id == equipment_id)
            )
            await session.execute(delete(Equipment).where(Equipment.id == equipment_id))
            await session.execute(
                delete(Technician).where(
                    Technician.id.in_(
                        [
                            technician_a.id,
                            technician_b.id,
                        ]
                    )
                )
            )
            await session.execute(
                delete(Hospital).where(Hospital.id.in_([hospital_a_id, hospital_b_id]))
            )
            await session.commit()


@pytest.mark.asyncio
async def test_reliability_requires_authentication(client):
    response = await client.get("/analytics/reliability")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_reliability_authenticated(client, test_users):
    login_response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = await client.get(
        "/analytics/reliability",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "metrics" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["metrics"], list)

    assert data["count"] == len(data["metrics"])


@pytest.mark.asyncio
async def test_reliability_calculates_correct_percentages(client, test_users):
    async with TestSessionLocal() as session:
        hospital = Hospital(
            name="Reliability Test Hospital",
            location_region="Test Region",
            capacity=100,
            supervisor_id=999,
        )

        session.add(hospital)
        await session.flush()

        device = Equipment(
            serial_number="TEST-RELIABILITY-001",
            model="Reliability Test Model",
            status=EquipmentStatus.AVAILABLE,
            charge_level=Decimal("100.00"),
            facility_id=hospital.id,
        )

        session.add(device)
        await session.flush()

        statuses = (
            [OrderStatus.COMPLETED] * 3
            + [OrderStatus.FAILED]
            + [OrderStatus.PENDING]
            + [OrderStatus.IN_PROGRESS]
        )

        for index, status in enumerate(statuses):
            session.add(
                WorkOrder(
                    title=f"Reliability Test Order {index}",
                    priority=OrderPriority.MEDIUM,
                    status=status,
                    equipment_id=device.id,
                    technician_id=201,
                )
            )

        await session.commit()

        device_id = device.id
        hospital_id = hospital.id

    try:
        login_response = await client.post(
            "/auth/token",
            data={"username": "admin", "password": "admin123"},
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await client.get(
            "/analytics/reliability",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        metrics = response.json()["metrics"]

        model_metrics = next(
            item for item in metrics if item["model"] == "Reliability Test Model"
        )

        assert model_metrics["completed"] == 3
        assert model_metrics["failed"] == 1
        assert model_metrics["total"] == 4
        assert model_metrics["completion_rate"] == 75.0
        assert model_metrics["failure_rate"] == 25.0

    finally:
        async with TestSessionLocal() as session:
            await session.execute(
                delete(WorkOrder).where(WorkOrder.equipment_id == device_id)
            )
            await session.execute(delete(Equipment).where(Equipment.id == device_id))
            await session.execute(delete(Hospital).where(Hospital.id == hospital_id))
            await session.commit()


@pytest.mark.asyncio
async def test_maintenance_flags_requires_authentication(client):
    response = await client.get("/analytics/maintenance-flags")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_maintenance_flags_authenticated(client, test_users):
    login_response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = await client.get(
        "/analytics/maintenance-flags",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "hospitals" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["hospitals"], list)

    assert data["count"] == len(data["hospitals"])


@pytest.mark.asyncio
async def test_maintenance_flags_threshold(client, test_users):
    async with TestSessionLocal() as session:
        hospital_a = Hospital(
            name="Maintenance Test A",
            location_region="North",
            capacity=100,
            supervisor_id=900,
        )

        hospital_b = Hospital(
            name="Maintenance Test B",
            location_region="South",
            capacity=100,
            supervisor_id=901,
        )

        session.add_all([hospital_a, hospital_b])
        await session.flush()

        hospital_a_id = hospital_a.id
        hospital_b_id = hospital_b.id

        for hospital, maintenance_count in [
            (hospital_a, 4),
            (hospital_b, 3),
        ]:
            for index in range(10):
                status = (
                    EquipmentStatus.MAINTENANCE
                    if index < maintenance_count
                    else EquipmentStatus.AVAILABLE
                )

                session.add(
                    Equipment(
                        serial_number=f"MAINT-{hospital.id}-{index}",
                        model="Maintenance Test Device",
                        status=status,
                        charge_level=Decimal("100.00"),
                        facility_id=hospital.id,
                    )
                )

        await session.commit()

    try:
        login_response = await client.post(
            "/auth/token",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await client.get(
            "/analytics/maintenance-flags",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        flagged_hospitals = {
            hospital["hospital_id"]: hospital
            for hospital in response.json()["hospitals"]
        }

        # Hospital A: 40% maintenance, should be flagged
        assert hospital_a_id in flagged_hospitals

        hospital_a_result = flagged_hospitals[hospital_a_id]

        assert hospital_a_result["total_equipment"] == 10
        assert hospital_a_result["maintenance_equipment"] == 4
        assert hospital_a_result["maintenance_percentage"] == 40.0

        # Hospital B: exactly 30%, should NOT be flagged
        assert hospital_b_id not in flagged_hospitals

    finally:
        async with TestSessionLocal() as session:
            await session.execute(
                delete(Equipment).where(
                    Equipment.facility_id.in_(
                        [
                            hospital_a_id,
                            hospital_b_id,
                        ]
                    )
                )
            )

            await session.execute(
                delete(Hospital).where(
                    Hospital.id.in_(
                        [
                            hospital_a_id,
                            hospital_b_id,
                        ]
                    )
                )
            )

            await session.commit()


@pytest.mark.asyncio
async def test_reporting_lines_requires_authentication(client):
    response = await client.get("/analytics/reporting-lines/101")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_reporting_lines_authenticated(client, test_users):
    login_response = await client.post(
        "/auth/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = await client.get(
        "/analytics/reporting-lines/101",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supervisor_id"] == 101
    assert "count" in data
    assert "technicians" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["technicians"], list)

    assert data["count"] == len(data["technicians"])


@pytest.mark.asyncio
async def test_reporting_lines_counts_distinct_active_technicians(client, test_users):
    supervisor_id = 9001

    async with TestSessionLocal() as session:
        hospital = Hospital(
            name="Reporting Lines Test Hospital",
            location_region="Test Region",
            capacity=100,
            supervisor_id=supervisor_id,
        )
        session.add(hospital)
        await session.flush()

        device = Equipment(
            serial_number="TEST-REPORTING-001",
            model="Reporting Lines Test Model",
            status=EquipmentStatus.AVAILABLE,
            charge_level=Decimal("100.00"),
            facility_id=hospital.id,
        )
        session.add(device)
        await session.flush()

        technicians = [
            Technician(
                name="Reporting Test A",
                facility_id=hospital.id,
                supervisor_id=supervisor_id,
            ),
            Technician(
                name="Reporting Test B",
                facility_id=hospital.id,
                supervisor_id=supervisor_id,
            ),
            Technician(
                name="Reporting Test C",
                facility_id=hospital.id,
                supervisor_id=supervisor_id,
            ),
            Technician(
                name="Reporting Test D",
                facility_id=hospital.id,
                supervisor_id=9002,
            ),
        ]

        session.add_all(technicians)
        await session.flush()

        technician_ids = [tech.id for tech in technicians]
        hospital_id = hospital.id
        device_id = device.id

        assignments = [
            (technicians[0].id, OrderStatus.PENDING),
            (technicians[0].id, OrderStatus.IN_PROGRESS),
            (technicians[1].id, OrderStatus.PENDING),
            (technicians[2].id, OrderStatus.COMPLETED),
            (technicians[3].id, OrderStatus.PENDING),
        ]

        for index, (technician_id, status) in enumerate(assignments):
            session.add(
                WorkOrder(
                    title=f"Reporting Test Order {index}",
                    priority=OrderPriority.MEDIUM,
                    status=status,
                    equipment_id=device_id,
                    technician_id=technician_id,
                )
            )

        await session.commit()

    try:
        login_response = await client.post(
            "/auth/token",
            data={"username": "admin", "password": "admin123"},
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await client.get(
            f"/analytics/reporting-lines/{supervisor_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        data = response.json()

        # Check only the technicians created by this test.
        returned_ids = {tech["technician_id"] for tech in data["technicians"]}

        test_returned_ids = returned_ids.intersection(technician_ids)

        assert test_returned_ids == {
            technician_ids[0],
            technician_ids[1],
        }

        # Verify each technician appears only once.
        assert len(data["technicians"]) == len(returned_ids)

    finally:
        async with TestSessionLocal() as session:
            await session.execute(
                delete(WorkOrder).where(WorkOrder.equipment_id == device_id)
            )
            await session.execute(
                delete(Technician).where(Technician.id.in_(technician_ids))
            )
            await session.execute(delete(Equipment).where(Equipment.id == device_id))
            await session.execute(delete(Hospital).where(Hospital.id == hospital_id))
            await session.commit()
