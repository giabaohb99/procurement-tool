from pydantic import BaseModel


class EmployeeBase(BaseModel):
    code: str
    full_name: str
    email: str = ""
    phone: str = ""
    company_id: int = 0
    department_id: int = 0
    position: str = ""
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company_id: int | None = None
    department_id: int | None = None
    position: str | None = None
    is_active: bool | None = None


class EmployeeOut(EmployeeBase):
    id: int
    model_config = {"from_attributes": True}
