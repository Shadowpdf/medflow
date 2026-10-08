"""

run from backend with venv active
    python -m scripts.medflow_queries
"""

import asyncio

from sqlalchemy import select, func, case

from app.database import AsyncSessionLocal, engine
from app.models import Hospital, Equipment, ServiceReport, Technician
from app.models.work_order import WorkOrder
from app.models.enums import EquipmentStatus, OrderPriority, OrderStatus, UserRole


async def find_low_charge_alert(session):
    async with AsyncSessionLocal() as session:
        statement = (
            select(Equipment)
            .where(Equipment.charge_level < 20.0)
            .where(
                Equipment.status.in_(
                    [EquipmentStatus.AVAILABLE, EquipmentStatus.IN_USE]
                )
            )
            .order_by(Equipment.id)
        )

        result = await session.execute(statement)
        equipments = result.scalars().all()

        print("\n== Low Charge Equipment (Via ORM) ==")

        if not equipments:
            print("\n=== All Equipment charge levels sufficient ===")

        for equipment in equipments:
            print(
                f"Equipment ID: {equipment.id} | Equipment S/N: {equipment.serial_number} | "
                f"Equipment Status: {equipment.status.value} | Charge-Level: {equipment.charge_level}% | "
                f"Hospital ID: {equipment.facility_id}"
            )


async def find_colocation_discrepancies(session):
    async with AsyncSessionLocal() as session:
        statement = (
            select(Equipment, Technician, WorkOrder)
            .join(Equipment, WorkOrder.equipment_id == Equipment.id)
            .join(Technician, WorkOrder.technician_id == Technician.id)
            .where(Technician.facility_id != Equipment.facility_id)
            .order_by(WorkOrder.id)
        )

        result = await session.execute(statement)

        rows = result.all()

        print("\n== Co-location Discrepancies (Via ORM) ==")

        for equipment, technician, work_order in rows:
            print(
                f"Work Order ID: {work_order.id} | "
                f"Equipment ID: {equipment.id} | "
                f"Equipment Hospital ID: {equipment.facility_id} | "
                f"Technician ID: {technician.id} | "
                f"Technician Hospital ID: {technician.facility_id}"
            )


async def find_reliability_work_order(session, WorkOrder):
    completed_work_orders = func.sum(
        case((WorkOrder.status == OrderStatus.COMPLETED, 1), else_=0)
    )
    failed_work_orders = func.sum(
        case((WorkOrder.status == OrderStatus.FAILED, 1), else_=0)
    )
    total_work_orders = completed_work_orders + failed_work_orders

    completetion_ratio = completed_work_orders * 100.0 / total_work_orders

    statement = (
        select(
            Equipment.model,
            total_work_orders,
            completed_work_orders,
            failed_work_orders,
            completetion_ratio,
        )
        .join(WorkOrder, Equipment.id == WorkOrder.equipment_id)
        .group_by(Equipment.model)
        .having(total_work_orders > 0)
    )
    result = await session.execute(statement)

    rows = result.all()

    print("\n== Equipment with Highest Work Order Success ==")

    for (
        model,
        total_work_orders,
        completed_work_orders,
        failed_work_orders,
        completetion_ratio,
    ) in rows:
        print(
            f"Model: {model} | "
            f"Total Work Orders: {total_work_orders} | "
            f"Completed: {completed_work_orders} | "
            f"Failed: {failed_work_orders} | "
            f"Completion Ratio: {completetion_ratio:.2f}%"
        )


async def find_high_maintenance_hospital(session):
    async with AsyncSessionLocal() as session:

        total_equipment = func.count(Equipment.id)
        maintenance_equipments = func.sum(
            case((Equipment.status == EquipmentStatus.MAINTENANCE, 1), else_=0)
        )
        maintenance_percentage = maintenance_equipments * 100.0 / total_equipment

        statement = (
            select(
                Hospital.id,
                Hospital.name,
                total_equipment,
                maintenance_equipments,
                maintenance_percentage,
            )
            .join(Equipment, Hospital.id == Equipment.facility_id)
            .group_by(Hospital.id, Hospital.name)
            .having(maintenance_percentage > 30.0)
        )
        result = await session.execute(statement)

        rows = result.all()

        print("\n== Hospital with Highest Maintenance Equipment (30% +) ==")

        for (
            hospital_id,
            hospital_name,
            total_equipment,
            maintenance_equipments,
            maintenance_percentage,
        ) in rows:
            print(
                f"Hospital ID: {hospital_id} | "
                f"Hospital: {hospital_name} | "
                f"Total Equipment: {total_equipment} | "
                f"Maintenance Equipment: {maintenance_equipments} | "
                f"Maintenance %: {maintenance_percentage:.2f}%"
            )


async def find_technicians_with_active_calls(session, supervisor_id):
    async with AsyncSessionLocal() as session:
        statement = (
            select(Technician, WorkOrder)
            .join(WorkOrder, Technician.id == WorkOrder.technician_id)
            .where((WorkOrder.status.in_(["In-Progress", "Pending"])))
            .where(Technician.supervisor_id == supervisor_id)
        )

        result = await session.execute(statement)
        rows = result.all()

        print(f"\n== # of Technicians with Active Calls (Via ORM) ==")

        if not rows:
            print(f"\n== No Technicians with Active Calls  ==")
        for technician, work_order in rows:
            print(
                f"Technician ID: {technician.id} | "
                f"Technician Name: {technician.name} | "
                f"Supervisor ID: {technician.supervisor_id} | "
                f"Work Order ID: {work_order.id} | "
                f"Work Order Status: {work_order.status}"
            )


async def main() -> None:
    async with AsyncSessionLocal() as session:

        low_charge_equipments = await find_low_charge_alert(session)

        high_maintenanace_hospital = await find_high_maintenance_hospital(session)

        work_order_status = await find_reliability_work_order(session, WorkOrder)

        colocation_discrepancies = await find_colocation_discrepancies(session)

        technicians_with_active_calls = await find_technicians_with_active_calls(
            session, 101
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
