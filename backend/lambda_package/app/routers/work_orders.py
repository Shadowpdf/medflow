from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import WorkOrder, User, UserRole
from app.schemas.work_order import (WorkOrderCreate,WorkOrderRead, WorkOrderStatusUpdate)


router = APIRouter(
    prefix="/work-orders",
    tags=["work orders"],
)


@router.get("/", response_model=list[WorkOrderRead])
async def get_work_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WorkOrder))
    return result.scalars().all()


@router.get("/{work_order_id}", response_model=WorkOrderRead)
async def get_work_order(
    work_order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    work_order = await db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )

    return work_order


@router.post(
    "/",
    response_model=WorkOrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_work_order(
    work_order_data: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.CLINICAL_ADMIN)
    ),
):
    work_order = WorkOrder(**work_order_data.model_dump())

    db.add(work_order)
    await db.commit()
    await db.refresh(work_order)

    return work_order

@router.patch(
    "/{work_order_id}/status",
    response_model=WorkOrderRead,
)
async def update_work_order_status(
    work_order_id: int,
    status_data: WorkOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.CLINICAL_ADMIN,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    work_order = await db.get(WorkOrder, work_order_id)

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )

    work_order.status = status_data.status

    await db.commit()
    await db.refresh(work_order)

    return work_order