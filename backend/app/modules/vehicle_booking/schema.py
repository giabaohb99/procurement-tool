import json
from pydantic import BaseModel, Field, field_validator

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
    # 1 = đặt xe công tác · 2 = giao hàng (xem hằng số TYPE_* ở model)
    request_type: int = 1
    purpose: str
    start_location: str = Field("", max_length=255)
    end_location: str = Field("", max_length=255)
    stops: list[str] = Field(default_factory=list)  # điểm dừng trung gian, giữ thứ tự
    start_time: str = Field("", max_length=20)
    end_time: str = Field("", max_length=20)
    # Riêng đặt xe công tác
    passenger_count: int = 1
    attendees: str = ""
    contact_phone: str = Field("", max_length=20)
    is_round_trip: bool = False
    # Riêng đặt xe giao hàng
    goods_name: str = Field("", max_length=255)
    goods_size: str = Field("", max_length=255)
    sender_name: str = Field("", max_length=255)
    sender_phone: str = Field("", max_length=30)
    receiver_name: str = Field("", max_length=255)
    receiver_phone: str = Field("", max_length=30)
    special_instructions: str = ""
    # Phạm vi + người duyệt (auto-fill từ hồ sơ nếu bỏ trống)
    department_id: int = 0
    company_id: int = 0
    first_approver_id: int = 0
    note: str = ""

class VehicleBookingCreate(VehicleBookingBase):
    pass

class VehicleBookingUpdate(BaseModel):
    request_type: int | None = None
    purpose: str | None = None
    start_location: str | None = None
    end_location: str | None = None
    stops: list[str] | None = None
    start_time: str | None = None
    end_time: str | None = None
    passenger_count: int | None = None
    attendees: str | None = None
    contact_phone: str | None = None
    is_round_trip: bool | None = None
    goods_name: str | None = None
    goods_size: str | None = None
    sender_name: str | None = None
    sender_phone: str | None = None
    receiver_name: str | None = None
    receiver_phone: str | None = None
    special_instructions: str | None = None
    department_id: int | None = None
    company_id: int | None = None
    first_approver_id: int | None = None
    note: str | None = None
    assigned_vehicle_id: int | None = None
    assigned_driver_id: int | None = None
    driver_status: int | None = None

class VehicleBookingResponse(VehicleBookingBase):
    id: int
    code: str
    request_type_label: str = ""
    requester: str
    requester_id: int
    status: int
    status_label: str = ""
    assigned_vehicle_id: int | None = None
    assigned_driver_id: int | None = None
    dispatched_by: int | None = None
    dispatched_at: str | None = None
    driver_status: int = 0
    driver_status_label: str = ""
    actual_start_time: str = ""
    actual_end_time: str = ""
    distance_km: float = 0
    cost: int = 0
    created_at: str | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def _fmt_created_at(cls, v):
        """AuditMixin trả datetime; API dùng chuỗi ISO cho đồng nhất với các module khác."""
        if v is None:
            return None
        return v.isoformat() if hasattr(v, "isoformat") else str(v)

    @field_validator("stops", mode="before")
    @classmethod
    def _parse_stops(cls, v):
        """Model lưu stops dạng chuỗi JSON; tách về list khi trả API."""
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                data = json.loads(v)
                return data if isinstance(data, list) else []
            except (ValueError, TypeError):
                return []
        return v or []

    class Config:
        from_attributes = True
