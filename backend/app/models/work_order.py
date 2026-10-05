from .base import Base

from .enums import OrderPriority, OrderStatus
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    priority: Mapped[OrderPriority] = mapped_column(
        SqlEnum(
            OrderPriority,
            name="order_priority",
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        )
    )

    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(
            OrderStatus,
            name="order_status",
            values_callable=lambda enum_clas: [member.value for member in enum_clas]
        )
    )
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("equipments.id"))
    technician_id: Mapped[int] = mapped_column(Integer)