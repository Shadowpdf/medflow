from pydantic import BaseModel, ConfigDict

from app.models.enums import OrderPriority, OrderStatus


class WorkOrderBase(BaseModel):
    title: str
    priority: OrderPriority
    status: OrderStatus
    equipment_id: int
    technician_id: int


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderRead(WorkOrderBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class WorkOrderStatusUpdate(BaseModel):
    status: OrderStatus