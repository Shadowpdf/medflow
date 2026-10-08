from .base import Base

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    facility_id: Mapped[int] = mapped_column(
        ForeignKey("hospitals.id")
    )
    supervisor_id: Mapped[int] = mapped_column(Integer)