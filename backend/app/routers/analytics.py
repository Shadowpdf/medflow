from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models import Equipment
from app.models.enums import EquipmentStatus, OrderStatus
from app.dependencies import get_db, get_current_user
from app.models import Technician, Hospital
from app.models.work_order import WorkOrder

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/low-charge")
async def get_low_charge_alert(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    statement = (
        select(Equipment)
        .where(
            Equipment.charge_level < 20,
            Equipment.status.in_(
                [
                    EquipmentStatus.AVAILABLE,
                    EquipmentStatus.IN_USE,
                ]
            ),
        )
        .order_by(Equipment.id)
    )

    result = await db.execute(statement)
    equipments = result.scalars().all()

    return {
        "count": len(equipments),
        "devices": [
            {
                "id": equipment.id,
                "serial_number": equipment.serial_number,
                "model": equipment.model,
                "status": equipment.status.value,
                "charge_level": float(equipment.charge_level),
                "facility_id": equipment.facility_id,
            }
            for equipment in equipments
        ],
    }


@router.get("/co-location")
async def get_colocation_discrepancies(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    statement = (
        select(
            Equipment.id,
            Equipment.serial_number,
            Equipment.model,
            Equipment.facility_id,
            Technician.id.label("technician_id"),
            Technician.facility_id.label("technician_facility_id"),
        )
        .join(WorkOrder, WorkOrder.equipment_id == Equipment.id)
        .join(Technician, WorkOrder.technician_id == Technician.id)
        .where(Equipment.facility_id != Technician.facility_id)
        .distinct()
        .order_by(Equipment.id)
    )

    result = await db.execute(statement)
    rows = result.all()

    devices = [
        {
            "equipment_id": row.id,
            "serial_number": row.serial_number,
            "model": row.model,
            "equipment_facility_id": row.facility_id,
            "technician_id": row.technician_id,
            "technician_facility_id": row.technician_facility_id,
        }
        for row in rows
    ]

    return {
        "count": len({device["equipment_id"] for device in devices}),
        "discrepancies": devices,
    }


@router.get("/reliability")
async def get_reliability_metrics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    completed = func.sum(
        case(
            (WorkOrder.status == OrderStatus.COMPLETED, 1),
            else_=0,
        )
    )

    failed = func.sum(
        case(
            (WorkOrder.status == OrderStatus.FAILED, 1),
            else_=0,
        )
    )

    statement = (
        select(
            Equipment.model,
            completed.label("completed"),
            failed.label("failed"),
        )
        .join(WorkOrder, Equipment.id == WorkOrder.equipment_id)
        .group_by(Equipment.model)
        .order_by(Equipment.model)
    )

    result = await db.execute(statement)
    rows = result.all()

    metrics = []

    for row in rows:
        completed_count = row.completed
        failed_count = row.failed
        total = completed_count + failed_count

        if total == 0:
            continue

        metrics.append(
            {
                "model": row.model,
                "completed": completed_count,
                "failed": failed_count,
                "total": total,
                "completion_rate": round(completed_count / total * 100, 2),
                "failure_rate": round(failed_count / total * 100, 2),
            }
        )

    return {
        "count": len(metrics),
        "metrics": metrics,
    }


@router.get("/maintenance-flags")
async def get_maintenance_flags(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    total_equipment = func.count(Equipment.id)

    maintenance_equipment = func.sum(
        case(
            (Equipment.status == EquipmentStatus.MAINTENANCE, 1),
            else_=0,
        )
    )

    maintenance_percentage = maintenance_equipment * 100.0 / total_equipment

    statement = (
        select(
            Hospital.id,
            Hospital.name,
            total_equipment.label("total_equipment"),
            maintenance_equipment.label("maintenance_equipment"),
            maintenance_percentage.label("maintenance_percentage"),
        )
        .join(Equipment, Hospital.id == Equipment.facility_id)
        .group_by(Hospital.id, Hospital.name)
        .having(maintenance_percentage > 30.0)
        .order_by(Hospital.id)
    )

    result = await db.execute(statement)
    rows = result.all()

    hospitals = [
        {
            "hospital_id": row.id,
            "hospital_name": row.name,
            "total_equipment": row.total_equipment,
            "maintenance_equipment": row.maintenance_equipment,
            "maintenance_percentage": round(float(row.maintenance_percentage), 2),
        }
        for row in rows
    ]

    return {
        "count": len(hospitals),
        "hospitals": hospitals,
    }


@router.get("/reporting-lines/{supervisor_id}")
async def get_reporting_lines(
    supervisor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    statement = (
        select(
            Technician.id,
            Technician.name,
            Technician.facility_id,
        )
        .join(
            WorkOrder,
            WorkOrder.technician_id == Technician.id,
        )
        .where(
            Technician.supervisor_id == supervisor_id,
            WorkOrder.status.in_(
                [
                    OrderStatus.PENDING,
                    OrderStatus.IN_PROGRESS,
                ]
            ),
        )
        .distinct()
        .order_by(Technician.id)
    )

    result = await db.execute(statement)
    rows = result.all()

    technicians = [
        {
            "technician_id": row.id,
            "technician_name": row.name,
            "facility_id": row.facility_id,
        }
        for row in rows
    ]

    return {
        "supervisor_id": supervisor_id,
        "count": len(technicians),
        "technicians": technicians,
    }
