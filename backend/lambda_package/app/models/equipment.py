from .base import Base

from decimal import Decimal
from .enums import EquipmentStatus
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class Equipment(Base):
    __tablename__ = "equipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    serial_number: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    status: Mapped[EquipmentStatus] = mapped_column(
        SqlEnum(
            EquipmentStatus,
            name="equipment_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        )
    )
    charge_level: Mapped[Decimal] = mapped_column(Numeric(5,2))
    facility_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hospitals.id")
        )
    #possible forgien key^