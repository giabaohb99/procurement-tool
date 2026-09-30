from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .constants import COMPANY_TYPE_VALUES, CompanyType


#  Mã đi vào số hiệu văn bản: chỉ chữ HOA và số. Có dấu tiếng Việt hay khoảng
#  trắng là hỏng cả chuỗi số hiệu, mà số đã ban hành thì không sửa lại được.
ISSUE_CODE_PATTERN = r"^[A-Z0-9]*$"


def _check_company_type(value):
    """Loại hình phải là một mã của `CompanyType` — bao-CR-531.

    Nhận cả chuỗi số (`"2"`) vì ô chọn của giao diện cũ gửi chuỗi. Mã lạ trả 422 chứ
    không để lọt xuống DB: một mã không ai biết nghĩa thì bản in đoán bừa bộ ô ký.
    """
    if value is None:
        return value
    if isinstance(value, bool):
        raise ValueError("Loại hình không hợp lệ")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError("Loại hình không hợp lệ") from None
    if isinstance(value, float) and value != number:
        raise ValueError("Loại hình không hợp lệ")
    if number not in COMPANY_TYPE_VALUES:
        raise ValueError("Loại hình chỉ nhận 1 (Công ty) hoặc 2 (Hộ kinh doanh)")
    return number


class CompanyBase(BaseModel):
    code: str = ""
    name: str
    #  Xem `Company.issue_code` — khác `code`, và khóa lại sau khi đã cấp số.
    issue_code: str = Field(default="", max_length=20, pattern=ISSUE_CODE_PATTERN)
    short_name: str = ""
    level: int = Field(default=2, ge=1, le=3)
    #  bao-CR-531: 1 Công ty · 2 Hộ kinh doanh (`CompanyType`).
    company_type: int = int(CompanyType.COMPANY)
    tax_code: str = ""
    address: str = ""
    invoice_email: str = ""
    parent: int = 0
    legal_representative_id: int | None = None
    legal_rep_title: str = ""
    is_active: bool = True

    @field_validator("company_type", mode="before")
    @classmethod
    def _valid_company_type(cls, value):
        #  Bản ghi chưa flush (hoặc dòng cũ trước migration) mang `None` — coi là Công ty,
        #  đừng để cả màn danh sách trả 500 vì một ô (bài học `_gender_none_is_unknown`).
        if value is None:
            return int(CompanyType.COMPANY)
        return _check_company_type(value)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    issue_code: str | None = Field(default=None, max_length=20, pattern=ISSUE_CODE_PATTERN)
    short_name: str | None = None
    level: int | None = Field(default=None, ge=1, le=3)
    company_type: int | None = None
    tax_code: str | None = None
    address: str | None = None
    invoice_email: str | None = None
    parent: int | None = None
    legal_representative_id: int | None = None
    legal_rep_title: str | None = None
    is_active: bool | None = None

    @field_validator("company_type", mode="before")
    @classmethod
    def _valid_company_type(cls, value):
        return _check_company_type(value)


class CompanyOut(CompanyBase):
    id: int
    legal_rep_name: str | None = None
    logo: str = ""
    updated_at: datetime | None = None   # bao-CR-294 — cột "Ngày cập nhật" ở màn danh sách
    model_config = {"from_attributes": True}
