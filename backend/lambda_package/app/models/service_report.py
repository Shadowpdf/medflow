from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ServiceReport(Base):
    __tablename__ = "service_reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("work_orders.id")
    )

    file_url: Mapped[str] = mapped_column(Text)

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )