from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import EquipmentStatus


class EquipmentBase(BaseModel):
    serial_number: str
    model: str
    status: EquipmentStatus
    charge_level: Decimal
    facility_id: int


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentRead(EquipmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)