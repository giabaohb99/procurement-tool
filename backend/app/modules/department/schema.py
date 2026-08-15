from pydantic import BaseModel, Field, field_validator

from app.modules.company.schema import ISSUE_CODE_PATTERN


class DepartmentBase(BaseModel):
    code: str = ""
    name: str
    #  Mã đi vào số hiệu văn bản (`NS` trong `08/2026/TB-NS-DEGO`), khác `code`.
    issue_code: str = Field(default="", max_length=20, pattern=ISSUE_CODE_PATTERN)
    kind: int = Field(default=1, ge=1, le=3)
    company_id: int = 0
    parent: int = 0
    manager_id: int = 0
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    issue_code: str | None = Field(default=None, max_length=20, pattern=ISSUE_CODE_PATTERN)
    kind: int | None = Field(default=None, ge=1, le=3)
    company_id: int | None = None
    parent: int | None = None
    manager_id: int | None = None
    is_active: bool | None = None


class DepartmentOut(DepartmentBase):
    id: int
    manager_name: str | None = None
    model_config = {"from_attributes": True}


class DepartmentCompanyInput(BaseModel):
    company_id: int = Field(gt=0)
    manager_employee_id: int | None = Field(default=None, gt=0)
    issue_code_override: str = Field(default="", max_length=20, pattern=ISSUE_CODE_PATTERN)
    is_active: bool = True

    @field_validator("issue_code_override", mode="before")
    @classmethod
    def upper_issue_code(cls, value):
        return (value or "").strip().upper() if isinstance(value, str) else value


class DepartmentCompanyReplace(BaseModel):
    items: list[DepartmentCompanyInput]


class DepartmentCompanyOut(DepartmentCompanyInput):
    id: int
    department_id: int
    company_name: str = ""
    manager_name: str = ""
    model_config = {"from_attributes": True}
