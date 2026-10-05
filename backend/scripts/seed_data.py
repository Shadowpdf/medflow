import asyncio
from decimal import Decimal

from app.database import AsyncSessionLocal
from app.models import (
    Hospital,
    Equipment,
    WorkOrder,
    ServiceReport,
    EquipmentStatus,
    OrderPriority,
    OrderStatus,
)


async def seed_data():
    async with AsyncSessionLocal() as session:

        # Hospitals
        hospital_1 = Hospital(
            name="Central Medical Center",
            location_region="North",
            capacity=500,
            supervisor_id=101,
        )

        hospital_2 = Hospital(
            name="Regional Medical Center",
            location_region="South",
            capacity=350,
            supervisor_id=102,
        )

        session.add_all([hospital_1, hospital_2])

        # Sends INSERTs so generated IDs become available
        await session.flush()

        # Equipment
        equipment_1 = Equipment(
            serial_number="EQ-1001",
            model="Ventilator X1",
            status=EquipmentStatus.AVAILABLE,
            charge_level=Decimal("100.00"),
            facility_id=hospital_1.id,
        )

        equipment_2 = Equipment(
            serial_number="EQ-1002",
            model="Infusion Pump A2",
            status=EquipmentStatus.MAINTENANCE,
            charge_level=Decimal("45.00"),
            facility_id=hospital_1.id,
        )

        equipment_3 = Equipment(
            serial_number="EQ-2001",
            model="Patient Monitor M5",
            status=EquipmentStatus.IN_USE,
            charge_level=Decimal("78.00"),
            facility_id=hospital_2.id,
        )

        session.add_all([
            equipment_1,
            equipment_2,
            equipment_3,
        ])

        await session.flush()

        # Work Orders
        work_order_1 = WorkOrder(
            title="Inspect ventilator",
            priority=OrderPriority.MEDIUM,
            status=OrderStatus.PENDING,
            equipment_id=equipment_1.id,
            technician_id=201,
        )

        work_order_2 = WorkOrder(
            title="Repair infusion pump",
            priority=OrderPriority.CRITICAL,
            status=OrderStatus.IN_PROGRESS,
            equipment_id=equipment_2.id,
            technician_id=202,
        )

        work_order_3 = WorkOrder(
            title="Routine monitor inspection",
            priority=OrderPriority.LOW,
            status=OrderStatus.COMPLETED,
            equipment_id=equipment_3.id,
            technician_id=201,
        )

        session.add_all([
            work_order_1,
            work_order_2,
            work_order_3,
        ])

        # Get the generated work-order IDs from PostgreSQL
        await session.flush()

        report_1 = ServiceReport(
            work_order_id=work_order_1.id,
            file_url="reports/inspection-001.pdf",
            notes="Initial equipment inspection completed.",
        )

        report_2 = ServiceReport(
            work_order_id=work_order_2.id,
            file_url="reports/repair-002.pdf",
            notes="Pump requires additional maintenance.",
        )

        session.add_all([report_1, report_2])


        await session.commit()

        print("Seed data inserted successfully.")


if __name__ == "__main__":
    asyncio.run(seed_data())