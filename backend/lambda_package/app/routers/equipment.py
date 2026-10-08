from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import Equipment, User, UserRole
from app.schemas.equipment import EquipmentCreate, EquipmentRead


router = APIRouter(
    prefix="/equipment",
    tags=["equipment"],
)


@router.get("/", response_model=list[EquipmentRead])
async def get_equipment(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Equipment))
    return result.scalars().all()


@router.get("/{equipment_id}", response_model=EquipmentRead)
async def get_equipment_by_id(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    equipment = await db.get(Equipment, equipment_id)

    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment


@router.post(
    "/",
    response_model=EquipmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_equipment(
    equipment_data: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.CLINICAL_ADMIN)
    ),
):
    equipment = Equipment(**equipment_data.model_dump())

    db.add(equipment)
    await db.commit()
    await db.refresh(equipment)

    return equipment