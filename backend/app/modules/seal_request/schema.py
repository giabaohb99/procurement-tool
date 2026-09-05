from pydantic import BaseModel, Field, field_validator


# --- Loại con dấu (danh mục nền — giữ API cho tương thích, không còn trên form) ---

class SealTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field("", max_length=255)
    is_active: bool = True


class SealTypeCreate(SealTypeBase):
    pass


class SealTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SealTypeResponse(SealTypeBase):
    id: int

    class Config:
        from_attributes = True


# --- Yêu cầu đóng dấu -------------------------------------------------------

class SealRequestBase(BaseModel):
    purpose: str = Field("", description="Mục đích sử dụng — tiêu đề hiển thị của phiếu")
    #  NHIỀU công ty cần đóng dấu (bảng nối tab_seal_request_company).
    company_ids: list[int] = Field(default_factory=list)
    department_id: int = 0
    first_approver_id: int = 0
    note: str = ""


class SealRequestCreate(SealRequestBase):
    pass


class SealRequestUpdate(BaseModel):
    purpose: str | None = None
    company_ids: list[int] | None = None
    department_id: int | None = None
    first_approver_id: int | None = None
    note: str | None = None


class ReasonIn(BaseModel):
    """Lý do đi kèm khi Yêu cầu chỉnh sửa / Từ chối (TBP hoặc Văn thư)."""
    reason: str = Field("", max_length=1000)


class CompleteSealIn(BaseModel):
    """Văn thư HOÀN THÀNH (đã đóng dấu ngoài thực tế): ghi chú."""
    note: str = Field("", max_length=1000)


class CompanyRef(BaseModel):
    """Công ty gắn trên phiếu — có tên + MST + logo cho hiển thị."""
    id: int
    name: str = ""
    tax_code: str = ""
    logo: str = ""


class SealRequestResponse(SealRequestBase):
    id: int
    code: str
    status: int
    status_label: str = ""
    requester: str = ""
    requester_id: int = 0
    # Nhãn nối thêm (backend join) — hiển thị trên chi tiết.
    companies: list[CompanyRef] = Field(default_factory=list)
    requester_email: str = ""
    requester_phone: str = ""
    requester_role: str = ""
    approver_name: str = ""         # tên Trưởng bộ phận phê duyệt
    signed_doc_count: int = 0       # số tệp chứng từ đã đính kèm
    #  Đang chạy LUỒNG DUYỆT NHIỀU BƯỚC (engine) → FE ẩn nút duyệt một bước (cổng 1).
    approval_running: bool = False
    created_at: str | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def _fmt_created_at(cls, v):
        """AuditMixin trả datetime; API dùng chuỗi ISO. Không có validator này thì
        `model_validate(req)` vỡ ngay (đúng lỗi 500 khi tạo phiếu)."""
        if v is None:
            return None
        return v.isoformat() if hasattr(v, "isoformat") else str(v)

    class Config:
        from_attributes = True
