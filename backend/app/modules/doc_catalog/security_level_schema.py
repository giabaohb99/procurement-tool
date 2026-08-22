"""Schema danh mục MỨC MẬT / ĐỘ KHẨN.

`value` để dải rộng (1–99) chứ không khóa 1–4: khóa lại thì danh mục sửa được
thành sửa được trên giấy. Ràng buộc thật là **duy nhất trong một thang** và
**không xóa khi đang có nơi dùng**, cả hai ép ở `security_level_guard.py`.
"""
from pydantic import BaseModel, Field, field_validator

from .security_level_model import KIND_CONFIDENTIAL, KIND_URGENCY

CODE_PATTERN = r"^[A-Z0-9_]+$"

#: Chặn trên của `value`. Không phải giới hạn nghiệp vụ mà là chặn gõ nhầm —
#: cột dưới DB là SMALLINT và thứ bậc chỉ cần vài bậc là đủ.
VALUE_MAX = 99


class SecurityLevelCreate(BaseModel):
    kind: int = Field(default=KIND_CONFIDENTIAL, ge=KIND_CONFIDENTIAL, le=KIND_URGENCY)
    value: int = Field(ge=1, le=VALUE_MAX)
    code: str = Field(min_length=1, max_length=30, pattern=CODE_PATTERN)
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    is_active: bool = True

    @field_validator("code", mode="before")
    @classmethod
    def upper_code(cls, v):
        return (v or "").strip().upper().replace(" ", "_")


class SecurityLevelUpdate(BaseModel):
    #  KHÔNG cho sửa `kind` và `value`. Đổi thang thì con số đang nằm trên hàng
    #  nghìn văn bản đột nhiên đọc sang thang khác; đổi số thì mọi điều kiện
    #  luồng duyệt đã lưu (`{"field":"secrecy_level","op":"gte","value":3}`) trỏ
    #  vào một mức khác mà không báo gì — xem đầu `security_level_model.py`.
    #  Cần một bậc khác thì thêm dòng mới rồi ngừng dòng cũ.
    code: str | None = Field(default=None, min_length=1, max_length=30, pattern=CODE_PATTERN)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None

    @field_validator("code", mode="before")
    @classmethod
    def upper_code(cls, v):
        return None if v is None else (v or "").strip().upper().replace(" ", "_")


class SecurityLevelOut(BaseModel):
    id: int
    kind: int
    value: int
    code: str
    name: str
    description: str
    is_active: bool

    model_config = {"from_attributes": True}
