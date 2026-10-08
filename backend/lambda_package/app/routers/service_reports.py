from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import ServiceReport, User, UserRole
from app.schemas.service_report import ServiceReportCreate, ServiceReportRead


router = APIRouter(
    prefix="/service-reports",
    tags=["service reports"],
)


@router.get("/", response_model=list[ServiceReportRead])
async def get_service_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ServiceReport))
    return result.scalars().all()


@router.get("/{report_id}", response_model=ServiceReportRead)
async def get_service_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await db.get(ServiceReport, report_id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service report not found",
        )

    return report


@router.post(
    "/",
    response_model=ServiceReportRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_report(
    report_data: ServiceReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.CLINICAL_ADMIN,
            UserRole.FIELD_TECHNICIAN,
        )
    ),
):
    report = ServiceReport(**report_data.model_dump())

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report