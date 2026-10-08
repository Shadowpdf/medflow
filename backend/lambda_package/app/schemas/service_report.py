from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ServiceReportBase(BaseModel):
    work_order_id: int
    file_url: str
    notes: str | None = None


class ServiceReportCreate(ServiceReportBase):
    pass


class ServiceReportRead(ServiceReportBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)