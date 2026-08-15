from pydantic import BaseModel, Field

from app.modules.company.schema import ISSUE_CODE_PATTERN


class DepartmentBase(BaseModel):
    code: str = ""
    name: str
    #  Mã đi vào số hiệu văn bản (`NS` trong `08/2026/TB-NS-DEGO`), khác `code`.
    issue_code: str = Field(default="", max_length=20, pattern=ISSUE_CODE_PATTERN)
    kind: int = 1
    company_id: int = 0
    parent: int = 0
    manager_id: int = 0
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    issue_code: str | None = Field(default=None, max_length=20, pattern=ISSUE_CODE_PATTERN)
    kind: int | None = None
    company_id: int | None = None
    parent: int | None = None
    manager_id: int | None = None
    is_active: bool | None = None


class DepartmentOut(DepartmentBase):
    id: int
    manager_name: str | None = None
    model_config = {"from_attributes": True}
