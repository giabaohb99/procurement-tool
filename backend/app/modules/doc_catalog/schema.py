"""Schema của hai danh mục nền phân hệ Văn thư.

`code` viết HOA không dấu vì nó đi thẳng vào số hiệu văn bản (`TB-2026-001`) —
có dấu tiếng Việt hay khoảng trắng là hỏng cả chuỗi mã và không sửa được sau khi
đã ban hành.
"""
from pydantic import BaseModel, Field, field_validator

CODE_PATTERN = r"^[A-Z0-9-]+$"


def _upper(value: str) -> str:
    return (value or "").strip().upper()


# ---- Loại văn bản ----
class DocTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=10, pattern=CODE_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    group_code: str = ""
    description: str = ""

    id_scheme: int = 2
    number_when: int = 2
    default_secrecy: int = 2
    is_confidential_type: bool = False

    needs_approval: bool = False
    needs_signature: bool = False
    needs_decision: bool = False
    needs_request: bool = False

    review_cycle_months: int = 0
    retention_months: int = 0
    default_flow_id: int = 0
    sort_order: int = 0
    is_active: bool = True

    @field_validator("code", "group_code", mode="before")
    @classmethod
    def upper_code(cls, value):
        return _upper(value) if isinstance(value, str) else value


class DocTypeUpdate(BaseModel):
    """Sửa từng phần. `code` KHÔNG sửa được sau khi đã cấp số — chặn ở service."""

    code: str | None = Field(default=None, max_length=10, pattern=CODE_PATTERN)
    name: str | None = Field(default=None, max_length=200)
    group_code: str | None = None
    description: str | None = None

    id_scheme: int | None = None
    number_when: int | None = None
    default_secrecy: int | None = None
    is_confidential_type: bool | None = None

    needs_approval: bool | None = None
    needs_signature: bool | None = None
    needs_decision: bool | None = None
    needs_request: bool | None = None

    review_cycle_months: int | None = None
    retention_months: int | None = None
    default_flow_id: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None

    @field_validator("code", "group_code", mode="before")
    @classmethod
    def upper_code(cls, value):
        return _upper(value) if isinstance(value, str) else value


class DocTypeOut(DocTypeCreate):
    id: int
    model_config = {"from_attributes": True}


# ---- Đơn vị gửi nhận bên ngoài ----
class ExternalPartyCreate(BaseModel):
    code: str = Field(default="", max_length=30)
    name: str = Field(min_length=1, max_length=300)
    kind: int = 1
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    is_active: bool = True

    @field_validator("code", mode="before")
    @classmethod
    def upper_code(cls, value):
        return _upper(value) if isinstance(value, str) else value


class ExternalPartyUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=30)
    name: str | None = Field(default=None, max_length=300)
    kind: int | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    is_active: bool | None = None

    @field_validator("code", mode="before")
    @classmethod
    def upper_code(cls, value):
        return _upper(value) if isinstance(value, str) else value


class ExternalPartyOut(ExternalPartyCreate):
    id: int
    model_config = {"from_attributes": True}
