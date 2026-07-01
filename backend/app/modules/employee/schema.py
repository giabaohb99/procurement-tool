from datetime import datetime
from pydantic import BaseModel


class EmployeeBase(BaseModel):
    code: str = ""
    full_name: str
    email: str = ""
    phone: str = ""
    company_id: int = 0
    department_id: int = 0
    position: str = ""
    role_name: str = ""
    status: str = "Chính thức"
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
    role_name: str | None = None
    status: str | None = None
    is_active: bool | None = None


class EmployeeOut(EmployeeBase):
    id: int
    code: str
    department_name: str | None = None
    manager_name: str | None = None
    created_at: datetime | None = None
    model_config = {"from_attributes": True}
