"""Schema của SỔ VĂN BẢN."""
from pydantic import BaseModel, Field, field_validator

CODE_PATTERN = r"^[A-Z0-9-]+$"


class DocumentBookBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: int = 1
    description: str = ""
    company_id: int
    number_prefix: str = ""
    reset_yearly: bool = True
    start_no: int = Field(default=1, ge=1)
    is_active: bool = True

    #  Danh sách NHÂN SỰ đích danh, không phải tài khoản và không phải phòng ban.
    #  Gửi cả hai mảng mỗi lần lưu: bỏ trống nghĩa là xóa hết khỏi vai đó.
    #  `manager_ids` phải có ít nhất một người — sổ không ai quản lý là sổ không
    #  ai chịu trách nhiệm; kiểm ở `book_service.create_book` / `update_book`.
    manager_ids: list[int] = []
    viewer_ids: list[int] = []


class DocumentBookCreate(DocumentBookBase):
    #  Bỏ trống thì service tự sinh theo loại sổ (`SD`, `SDI`, `SNB` + số thứ tự).
    code: str = Field(default="", max_length=30)

    @field_validator("code", mode="before")
    @classmethod
    def upper_code(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class DocumentBookUpdate(BaseModel):
    """Sửa từng phần. **Không cho sửa `code`** — mã sổ là khóa của bộ đếm."""

    name: str | None = Field(default=None, max_length=200)
    kind: int | None = None
    description: str | None = None
    company_id: int | None = None
    number_prefix: str | None = None
    reset_yearly: bool | None = None
    start_no: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    manager_ids: list[int] | None = None
    viewer_ids: list[int] | None = None


class DocumentBookOut(DocumentBookBase):
    id: int
    code: str
    #  Số kế tiếp của năm hiện tại — chỉ để hiển thị, không phải số đã chiếm.
    next_no: int = 0
    next_number_display: str = ""
    #  Đã cấp bao nhiêu số trong năm nay.
    issued_count: int = 0
    company_name: str = ""
    manager_names: list[str] = []
    viewer_names: list[str] = []

    model_config = {"from_attributes": True}
