from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import UserRole, User
import boto3
import os
from starlette.concurrency import run_in_threadpool
import asyncio
from botocore.config import Config

router = APIRouter(
    prefix="/health",
    tags=["health"],
)

s3_config = Config(
    connect_timeout=2,
    read_timeout=3,
    retries={"total_max_attempts": 1},
)
s3 = boto3.client("s3", config= s3_config)


@router.get("")
async def get_health():
    return {"status": "ok"}


@router.get("/ready")
async def get_health_ready(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unreachable",
        )

    return {"status": "ready"}


@router.get("/detail")
async def get_detail(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLINICAL_ADMIN)),
):
    bucket_name = os.getenv("S3_BUCKET_NAME")
    try:
        await asyncio.wait_for(
            db.execute(text("SELECT 1")),
            timeout=3.0,
        )
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    try:
        await run_in_threadpool(s3.head_bucket, Bucket=bucket_name)
        s3_status = "healthy"
    except Exception as e:
        print(f"S3 health check failed: {type(e).__name__}: {e}")
        s3_status = "unhealthy"

    return {
        "database": db_status,
        "s3": s3_status,
    }
