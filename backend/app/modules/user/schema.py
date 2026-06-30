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


class UserOut(BaseModel):
    id: int
    email: str
    employee_id: int
    is_active: bool
    role_ids: list[int] = []
    model_config = {"from_attributes": True}
