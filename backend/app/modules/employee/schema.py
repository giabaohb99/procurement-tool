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
    updated_at: datetime | None = None   # bao-CR-294 — cột "Ngày cập nhật" ở màn danh sách
    # Ảnh đại diện lấy từ tài khoản đăng nhập (tab_user.avatar). Danh sách phải
    # selectinload(Employee.user) — xem service.list_employees — để không thành N+1.
    avatar: str = ""
    model_config = {"from_attributes": True}


class EmployeeDetailOut(EmployeeOut):
    """Bản dùng cho MÀN CHI TIẾT — kèm id tài khoản đăng nhập để biết đã cấp tài khoản chưa."""

    user_id: int = 0
