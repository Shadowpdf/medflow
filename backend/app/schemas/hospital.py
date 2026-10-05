from pydantic import BaseModel, ConfigDict


class HospitalBase(BaseModel):
    name: str
    location_region: str
    capacity: int
    supervisor_id: int


class HospitalCreate(HospitalBase):
    pass


class HospitalRead(HospitalBase):
    id: int

    model_config = ConfigDict(from_attributes=True)