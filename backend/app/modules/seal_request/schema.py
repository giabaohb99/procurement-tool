from pydantic import BaseModel, Field, field_validator


# --- Loại con dấu (danh mục nền) -------------------------------------------

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
    title: str = Field("", max_length=255, description="Tên chứng từ (tùy chọn)")
    seal_type_id: int = 0
    # company_id = CÔNG TY CỦA CON DẤU (người tạo chọn); auto-fill từ hồ sơ nếu bỏ trống.
    company_id: int = 0
    department_id: int = 0
    copies: int = 1
    first_approver_id: int = 0
    note: str = ""


class SealRequestCreate(SealRequestBase):
    pass


class SealRequestUpdate(BaseModel):
    purpose: str | None = None
    title: str | None = None
    seal_type_id: int | None = None
    company_id: int | None = None
    department_id: int | None = None
    copies: int | None = None
    first_approver_id: int | None = None
    note: str | None = None


class ReasonIn(BaseModel):
    """Lý do đi kèm khi Yêu cầu chỉnh sửa / Từ chối (TBP hoặc Văn thư)."""
    reason: str = Field("", max_length=1000)


class CompleteSealIn(BaseModel):
    """Văn thư HOÀN THÀNH (đã đóng dấu ngoài thực tế): số bản đã đóng + ghi chú."""
    copies_done: int | None = None
    note: str = Field("", max_length=1000)


class SealRequestResponse(SealRequestBase):
    id: int
    code: str
    status: int
    status_label: str = ""
    requester: str = ""
    requester_id: int = 0
    # Nhãn nối thêm (backend join) — hiển thị trên chi tiết như bản cũ.
    seal_type_name: str = ""
    company_name: str = ""
    company_tax_code: str = ""      # MST của công ty con dấu
    requester_email: str = ""
    requester_phone: str = ""
    requester_role: str = ""
    approver_name: str = ""         # tên Trưởng bộ phận phê duyệt
    signed_doc_count: int = 0       # số tệp chứng từ chữ ký sống đã đính kèm
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
