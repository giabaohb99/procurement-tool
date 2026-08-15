from pydantic import BaseModel, Field


#  Mã đi vào số hiệu văn bản: chỉ chữ HOA và số. Có dấu tiếng Việt hay khoảng
#  trắng là hỏng cả chuỗi số hiệu, mà số đã ban hành thì không sửa lại được.
ISSUE_CODE_PATTERN = r"^[A-Z0-9]*$"


class CompanyBase(BaseModel):
    code: str = ""
    name: str
    #  Xem `Company.issue_code` — khác `code`, và khóa lại sau khi đã cấp số.
    issue_code: str = Field(default="", max_length=20, pattern=ISSUE_CODE_PATTERN)
    short_name: str = ""
    level: int = 2
    tax_code: str = ""
    address: str = ""
    invoice_email: str = ""
    parent: int = 0
    legal_representative_id: int | None = None
    legal_rep_title: str = ""
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    issue_code: str | None = Field(default=None, max_length=20, pattern=ISSUE_CODE_PATTERN)
    short_name: str | None = None
    level: int | None = None
    tax_code: str | None = None
    address: str | None = None
    invoice_email: str | None = None
    parent: int | None = None
    legal_representative_id: int | None = None
    legal_rep_title: str | None = None
    is_active: bool | None = None


class CompanyOut(CompanyBase):
    id: int
    legal_rep_name: str | None = None
    model_config = {"from_attributes": True}
