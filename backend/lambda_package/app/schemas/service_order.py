from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceReportBase(BaseModel):
    file_url: str
    notes: str | None = None


class ServiceReportCreate(ServiceReportBase):
    pass


class ServiceReportRead(ServiceReportBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)