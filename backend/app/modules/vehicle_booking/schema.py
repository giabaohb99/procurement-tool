from pydantic import BaseModel, Field
from typing import Optional
from app.core.base_schema import BaseResponse

class VehicleBase(BaseModel):
    license_plate: str = Field(..., max_length=50)
    model: str = Field("", max_length=100)
    type: str = Field("", max_length=50)
    capacity: int = 4
    status: str = "available"
    is_external: bool = False
    external_company: str = ""

class VehicleResponse(VehicleBase):
    id: int
    class Config:
        from_attributes = True

class DriverBase(BaseModel):
    name: str = Field(..., max_length=255)
    phone: str = Field("", max_length=20)
    license_number: str = Field("", max_length=50)
    status: str = "available"
    is_external: bool = False
    external_company: str = ""

class DriverResponse(DriverBase):
    id: int
    class Config:
        from_attributes = True

class VehicleBookingBase(BaseModel):
    purpose: str
    start_location: str = Field(..., max_length=255)
    end_location: str = Field(..., max_length=255)
    start_time: str = Field(..., max_length=20)
    end_time: str = Field(..., max_length=20)
    passenger_count: int = 1
    attendees: str = ""
    contact_phone: str = Field("", max_length=20)
    is_round_trip: bool = False
    department_id: int
    company_id: int
    first_approver_id: int
    note: str = ""

class VehicleBookingCreate(VehicleBookingBase):
    pass

class VehicleBookingUpdate(BaseModel):
    purpose: str | None = None
    start_location: str | None = None
    end_location: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    passenger_count: int | None = None
    attendees: str | None = None
    contact_phone: str | None = None
    is_round_trip: bool | None = None
    department_id: int | None = None
    company_id: int | None = None
    first_approver_id: int | None = None
    note: str | None = None
    assigned_vehicle_id: int | None = None
    assigned_driver_id: int | None = None
    driver_status: str | None = None

class VehicleBookingResponse(VehicleBookingBase):
    id: int
    code: str
    requester: str
    requester_id: int
    status: str
    assigned_vehicle_id: int | None = None
    assigned_driver_id: int | None = None
    dispatched_by: int | None = None
    dispatched_at: str | None = None
    driver_status: str
    created_at: str | None = None
    class Config:
        from_attributes = True
