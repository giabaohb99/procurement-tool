"""Pydantic schema đầu vào của Điểm cà phê. Đầu ra serialize tay ở `service.py`
(khuôn chung của các module: dict + nhãn enum, không dùng response_model)."""
from pydantic import BaseModel, Field


class PolicyIn(BaseModel):
    company_id: int = 0
    level_code: int
    monthly_points: int = Field(ge=0)
    effective_from: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: str = ""


class MemberCreate(BaseModel):
    employee_id: int
    level_code: int
    company_id: int = 0
    note: str = ""


class MemberUpdate(BaseModel):
    level_code: int | None = None
    status: int | None = None
    note: str | None = None


class MatchIn(BaseModel):
    """Xác nhận ghép một khách POS365 — người bấm chịu trách nhiệm cặp này (A3)."""
    pos_partner_id: int = Field(gt=0)
    pos_partner_code: str = ""


class CreatePartnerIn(BaseModel):
    """B-03 — tạo khách mới bên POS365 rồi tự ghép. Xem trước ở UI, đây là hành
    động GHI sang hệ ngoài."""
    name: str
    phone: str = ""


class AdjustIn(BaseModel):
    employee_id: int
    points: int
    reason: str = Field(min_length=3, description="Lý do bắt buộc — luật A-07")


class ResolveIn(BaseModel):
    """Xử lý đơn chưa khớp: `employee_id` > 0 = gán người; = 0 = bỏ qua (cần lý do)."""
    employee_id: int = 0
    reason: str = ""


class SyncRunIn(BaseModel):
    kind: int
    period: str | None = Field(default=None, pattern=r"^\d{6}$")


class ResetExecuteIn(BaseModel):
    """Chốt cấp phát một kỳ (A-06: từng kỳ PHẢI có người duyệt)."""
    period: str = Field(pattern=r"^\d{6}$")


class SelfOrderItemIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=20)


class SelfOrderIn(BaseModel):
    """Tự đặt nước từ DEGO — đơn đẩy sang POS365, quầy pha, điểm trừ qua vòng kéo."""
    items: list[SelfOrderItemIn] = Field(min_length=1, max_length=20)
    note: str = Field(default="", max_length=200)
