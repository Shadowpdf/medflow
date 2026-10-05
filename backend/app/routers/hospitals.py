from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import Hospital, User, UserRole
from app.schemas.hospital import HospitalCreate, HospitalRead


router = APIRouter(
    prefix="/hospitals",
    tags=["hospitals"],
)


@router.get("/", response_model=list[HospitalRead])
async def get_hospitals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Hospital))
    return result.scalars().all()


@router.get("/{hospital_id}", response_model=HospitalRead)
async def get_hospital(
    hospital_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hospital = await db.get(Hospital, hospital_id)

    if hospital is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found",
        )

    return hospital


@router.post(
    "/",
    response_model=HospitalRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_hospital(
    hospital_data: HospitalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.CLINICAL_ADMIN)
    ),
):
    hospital = Hospital(**hospital_data.model_dump())

    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)

    return hospital