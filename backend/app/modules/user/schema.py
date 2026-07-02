from pydantic import BaseModel


class UserProvision(BaseModel):
    """Cấp tài khoản cho 1 nhân viên đã có."""

    employee_id: int
    email: str = ""
    password: str
    role_ids: list[int] = []


class PasswordReset(BaseModel):
    new_password: str


class RoleAssign(BaseModel):
    role_ids: list[int]


class ScopeUpdate(BaseModel):
    """Phạm vi tổng theo user (Lớp B). Trống = không giới hạn chiều đó."""

    companies: list[int] = []
    departments: list[str] = []
    employees: list[int] = []
    exclude_companies: list[int] = []
    exclude_departments: list[str] = []
    exclude_employees: list[int] = []


class UserOut(BaseModel):
    id: int
    email: str
    employee_id: int
    is_active: bool
    role_ids: list[int] = []
    model_config = {"from_attributes": True}
