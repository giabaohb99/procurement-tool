"""Schema Mẫu hợp đồng lao động. `max_length` khớp ĐÚNG `String(n)` ở `template_model.py`
(SQLite không ép VARCHAR nên chỉ schema giữ được trần — luật backend-input-limits)."""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.core.labor_contract_codes import LaborContractType

Name200 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Note500 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]

#  Trần số biến lưu vào cột JSON `placeholders` (danh mục hiện < 60 biến).
MAX_PLACEHOLDERS = 200


def check_contract_type(v: int) -> int:
    """`0` và số không ai cấp đều là lỗi 422."""
    try:
        return int(LaborContractType(int(v)))
    except ValueError:
        allowed = ", ".join(str(int(x)) for x in LaborContractType)
        raise ValueError(f"Loại hợp đồng không hợp lệ — chỉ nhận: {allowed}")


class TemplateCreateIn(BaseModel):
    """Các trường dạng form của POST multipart (tệp đi riêng)."""

    model_config = {"extra": "forbid"}

    name: Name200
    company_id: int = Field(ge=1)
    contract_type: int
    note: Note500 = ""

    @field_validator("contract_type")
    @classmethod
    def _check_type(cls, v: int) -> int:
        return check_contract_type(v)


class TemplateUpdate(BaseModel):
    """PATCH — KHÔNG có `company_id` (mẫu gắn một pháp nhân suốt đời)."""

    model_config = {"extra": "forbid"}

    name: Name200 | None = None
    note: Note500 | None = None
    contract_type: int | None = None
    is_active: bool | None = None

    @field_validator("contract_type")
    @classmethod
    def _check_type(cls, v):
        return None if v is None else check_contract_type(v)


#  Soạn mẫu trên web (duoc-CR-606, 07/10/2026). Trần HTML 2 MB: một hợp đồng 10 trang có bảng chỉ cỡ
#  vài chục KB; trần chặn gửi rác làm treo bộ chuyển HTML → Word. Lề nằm trong khoảng thước cho kéo.
MAX_TEMPLATE_HTML = 2_000_000
MARGIN_MIN_MM, MARGIN_MAX_MM = 5, 60


class TemplateContentIn(BaseModel):
    """PUT `/{id}/content` — nội dung mẫu soạn trên web, lưu lại thành tệp .docx."""

    model_config = {"extra": "forbid"}

    html: str = Field(min_length=1, max_length=MAX_TEMPLATE_HTML)
    margin_left_mm: int = Field(30, ge=MARGIN_MIN_MM, le=MARGIN_MAX_MM)
    margin_right_mm: int = Field(20, ge=MARGIN_MIN_MM, le=MARGIN_MAX_MM)


class TemplateOut(BaseModel):
    """Hình dạng TRẢ RA. Cố ý KHÔNG có `url` / `file_key` / `file_id`."""

    id: int
    company_id: int
    company_name: str = ""
    company_code: str = ""
    contract_type: int
    name: str
    note: str = ""
    original_filename: str = ""
    file_size: int = 0
    placeholders: list[str] = []
    is_active: bool
    created_at: datetime | None = None
    created_by_name: str = ""
    contract_count: int = 0
